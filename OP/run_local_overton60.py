#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


OP_ROOT = Path(__file__).resolve().parent


@dataclass
class RunConfig:
    # Point this to the local Hugging Face model directory shown in your screenshot.
    model_dir: str = "/mnt/public/hf_models/Qwen/Qwen3-8B"
    questions_csv: str = str(OP_ROOT / "data" / "overtonbench_60_questions.csv")
    output_dir: str = str(OP_ROOT / "outputs")
    run_name: str = "Qwen3-8B"

    # Prompting
    system_prompt: str = (
        "You are a helpful assistant. Answer the user's question directly, clearly, and concisely."
    )
    user_prompt_template: str = "{question}"
    use_chat_template: bool = True
    save_rendered_prompt: bool = True

    # Generation
    batch_size: int = 20
    max_input_length: int = 4096
    max_new_tokens: int = 5120
    do_sample: bool = False
    temperature: float = 0.7
    top_p: float = 0.9
    repetition_penalty: float = 1.0

    # Loading / acceleration
    trust_remote_code: bool = False
    local_files_only: bool = True
    device_map: str = "auto"
    torch_dtype: str = "bfloat16"  # one of: auto, bfloat16, float16, float32
    attn_implementation: str = "auto"  # one of: auto, flash_attention_2, sdpa, eager, none
    load_in_4bit: bool = False
    load_in_8bit: bool = False

    # Save progress after each batch so long runs are resumable.
    save_every_batches: int = 1


CONFIG = RunConfig()


def resolve_torch_dtype(name: str) -> torch.dtype | str:
    if name == "auto":
        return "auto"
    mapping = {
        "bfloat16": torch.bfloat16,
        "float16": torch.float16,
        "float32": torch.float32,
    }
    if name not in mapping:
        raise ValueError(f"Unsupported torch_dtype: {name}")
    return mapping[name]


def resolve_attn_implementation(name: str) -> str | None:
    if name == "none":
        return None
    if name != "auto":
        return name
    if torch.cuda.is_available():
        if importlib.util.find_spec("flash_attn") is not None:
            return "flash_attention_2"
        return "sdpa"
    return None


def configure_torch() -> None:
    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True


def load_questions(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    required = {"source", "question_id", "question"}
    if not rows:
        raise ValueError(f"No rows found in {csv_path}")
    missing = required - set(rows[0].keys())
    if missing:
        raise ValueError(f"Missing columns in {csv_path}: {sorted(missing)}")
    return rows


def render_prompt(tokenizer: Any, system_prompt: str, user_prompt: str, use_chat_template: bool) -> str:
    if use_chat_template and getattr(tokenizer, "chat_template", None):
        messages = []
        if system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    if system_prompt.strip():
        return f"System:\n{system_prompt}\n\nUser:\n{user_prompt}\n\nAssistant:\n"
    return f"{user_prompt}\n"


def ensure_pad_token(tokenizer: Any) -> None:
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"


def infer_input_device(model: Any) -> torch.device:
    hf_device_map = getattr(model, "hf_device_map", None)
    if isinstance(hf_device_map, dict):
        for device in hf_device_map.values():
            if device not in ("cpu", "disk"):
                return torch.device(device)

    try:
        return next(model.parameters()).device
    except StopIteration:
        return torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


def normalize_generation_config(model: Any, tokenizer: Any, config: RunConfig) -> None:
    generation_config = getattr(model, "generation_config", None)
    if generation_config is None:
        return

    generation_config.pad_token_id = tokenizer.pad_token_id
    generation_config.eos_token_id = tokenizer.eos_token_id
    generation_config.use_cache = True

    if config.do_sample:
        generation_config.do_sample = True
        generation_config.temperature = config.temperature
        generation_config.top_p = config.top_p
    else:
        generation_config.do_sample = False
        for field in ("temperature", "top_p", "top_k", "min_p", "typical_p", "epsilon_cutoff", "eta_cutoff"):
            if hasattr(generation_config, field):
                setattr(generation_config, field, None)


def load_tokenizer_and_model(config: RunConfig) -> tuple[Any, Any]:
    model_path = Path(config.model_dir).expanduser().resolve()
    if not model_path.exists():
        raise FileNotFoundError(f"Model directory not found: {model_path}")

    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=config.trust_remote_code,
        local_files_only=config.local_files_only,
        use_fast=True,
    )
    ensure_pad_token(tokenizer)

    model_kwargs: dict[str, Any] = {
        "trust_remote_code": config.trust_remote_code,
        "local_files_only": config.local_files_only,
        "low_cpu_mem_usage": True,
    }

    dtype = resolve_torch_dtype(config.torch_dtype)
    if dtype != "auto":
        model_kwargs["torch_dtype"] = dtype

    if config.device_map:
        model_kwargs["device_map"] = config.device_map

    attn_impl = resolve_attn_implementation(config.attn_implementation)
    if attn_impl is not None:
        model_kwargs["attn_implementation"] = attn_impl

    if config.load_in_4bit and config.load_in_8bit:
        raise ValueError("Only one of load_in_4bit / load_in_8bit can be True.")
    if config.load_in_4bit:
        model_kwargs["load_in_4bit"] = True
    if config.load_in_8bit:
        model_kwargs["load_in_8bit"] = True

    model = AutoModelForCausalLM.from_pretrained(model_path, **model_kwargs)
    model.eval()
    normalize_generation_config(model, tokenizer, config)
    return tokenizer, model


def build_generation_kwargs(config: RunConfig, tokenizer: Any) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "max_new_tokens": config.max_new_tokens,
        "pad_token_id": tokenizer.pad_token_id,
        "eos_token_id": tokenizer.eos_token_id,
        "use_cache": True,
        "repetition_penalty": config.repetition_penalty,
    }
    if config.do_sample:
        kwargs["do_sample"] = True
        kwargs["temperature"] = config.temperature
        kwargs["top_p"] = config.top_p
    else:
        kwargs["do_sample"] = False
    return kwargs


def write_results_csv(rows: list[dict[str, Any]], path: Path) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_results_json(rows: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, ensure_ascii=False, indent=2)


def save_metadata(path: Path, config: RunConfig, questions_count: int, started_at: str) -> None:
    payload = {
        "config": asdict(config),
        "questions_count": questions_count,
        "started_at": started_at,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "cuda_available": torch.cuda.is_available(),
        "gpu_count": torch.cuda.device_count(),
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def main() -> None:
    configure_torch()
    started_at = datetime.now().isoformat(timespec="seconds")

    config = CONFIG
    questions_path = Path(config.questions_csv).expanduser().resolve()
    output_dir = Path(config.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    questions = load_questions(questions_path)
    tokenizer, model = load_tokenizer_and_model(config)
    generation_kwargs = build_generation_kwargs(config, tokenizer)

    run_prefix = f"{config.run_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    csv_path = output_dir / f"{run_prefix}.csv"
    json_path = output_dir / f"{run_prefix}.json"
    meta_path = output_dir / f"{run_prefix}.meta.json"

    all_results: list[dict[str, Any]] = []
    total = len(questions)
    batch_size = max(1, config.batch_size)

    print(f"[load] model_dir={Path(config.model_dir).expanduser().resolve()}")
    print(f"[load] questions={total} batch_size={batch_size}")

    for batch_start in range(0, total, batch_size):
        batch = questions[batch_start:batch_start + batch_size]
        prompts = []
        for row in batch:
            user_prompt = config.user_prompt_template.format(
                source=row["source"],
                question_id=row["question_id"],
                question=row["question"],
            )
            prompts.append(
                render_prompt(
                    tokenizer=tokenizer,
                    system_prompt=config.system_prompt,
                    user_prompt=user_prompt,
                    use_chat_template=config.use_chat_template,
                )
            )

        tokenized = tokenizer(
            prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=config.max_input_length,
        )
        input_device = infer_input_device(model)
        tokenized = {k: v.to(input_device) for k, v in tokenized.items()}

        batch_t0 = time.time()
        with torch.inference_mode():
            outputs = model.generate(**tokenized, **generation_kwargs)
        new_tokens = outputs[:, tokenized["input_ids"].shape[1]:]
        decoded = tokenizer.batch_decode(new_tokens, skip_special_tokens=True)

        for row, prompt_text, response_text in zip(batch, prompts, decoded):
            item: dict[str, Any] = {
                "source": row["source"],
                "question_id": row["question_id"],
                "question": row["question"],
                "response": response_text.strip(),
            }
            if config.save_rendered_prompt:
                item["prompt"] = prompt_text
            all_results.append(item)

        batch_index = (batch_start // batch_size) + 1
        batch_count = (total + batch_size - 1) // batch_size
        print(
            f"[batch {batch_index}/{batch_count}] "
            f"done={min(batch_start + len(batch), total)}/{total} "
            f"elapsed={time.time() - batch_t0:.2f}s"
        )

        if batch_index % max(1, config.save_every_batches) == 0:
            write_results_csv(all_results, csv_path)
            write_results_json(all_results, json_path)

    write_results_csv(all_results, csv_path)
    write_results_json(all_results, json_path)
    save_metadata(meta_path, config, total, started_at)

    print(f"[save] csv={csv_path}")
    print(f"[save] json={json_path}")
    print(f"[save] meta={meta_path}")


if __name__ == "__main__":
    main()
