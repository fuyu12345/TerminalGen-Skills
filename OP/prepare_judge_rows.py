#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd


OP_ROOT = Path(__file__).resolve().parent


@dataclass
class PrepareConfig:
    responses_csv: str = str(OP_ROOT / "outputs" / "overton60_Llama-3.2-3B-Instruct_20260330_062654.csv")
    official_data_path: str = ""  # Optional local CSV/parquet for the official full split.
    hf_dataset_name: str = "elinorpd/overtonbench"
    hf_split: str = "full"
    output_dir: str = str(OP_ROOT / "judge_inputs")
    output_name: str = "llama_overton60_full_rows.csv"
    model_name: str = "Llama-3.2-3B-Instruct"


CONFIG = PrepareConfig()


BASE_COLUMNS = [
    "user",
    "question_id",
    "question",
    "freeresponse",
    "selection_text",
    "selection_position",
    "Age",
    "Sex",
    "Ethnicity simplified",
    "U.s. political affiliation",
    "cluster_kmeans",
]


def load_dataframe(path_str: str) -> pd.DataFrame:
    path = Path(path_str).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Official data file not found: {path}")
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported official_data_path suffix: {path.suffix}")


def load_official_data(config: PrepareConfig) -> pd.DataFrame:
    if config.official_data_path.strip():
        return load_dataframe(config.official_data_path)

    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError(
            "datasets is not installed. Install it or set official_data_path to a local CSV/parquet."
        ) from exc

    dataset = load_dataset(config.hf_dataset_name, split=config.hf_split)
    return dataset.to_pandas()


def validate_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def load_responses(path_str: str) -> pd.DataFrame:
    path = Path(path_str).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Responses CSV not found: {path}")
    df = pd.read_csv(path)
    validate_columns(df, ["question_id", "question", "response"], "responses_csv")
    df = df.rename(columns={"response": "llm_response"})
    df["question_id"] = df["question_id"].astype(int)
    return df.drop_duplicates(subset=["question_id"], keep="first").copy()


def build_rows(config: PrepareConfig) -> pd.DataFrame:
    responses = load_responses(config.responses_csv)
    official = load_official_data(config)
    validate_columns(official, BASE_COLUMNS, "official benchmark data")

    official["question_id"] = official["question_id"].astype(int)
    base = official.drop_duplicates(subset=["user", "question_id"]).copy()
    base = base[BASE_COLUMNS]

    merged = base.merge(
        responses[["question_id", "question", "llm_response"]],
        on="question_id",
        how="inner",
        suffixes=("_official", ""),
    )
    if merged.empty:
        raise ValueError("No rows matched between official benchmark data and responses CSV.")

    official_question = merged["question_official"].astype(str)
    response_question = merged["question"].astype(str)
    mismatch = official_question != response_question
    if mismatch.any():
        mismatched_ids = sorted(merged.loc[mismatch, "question_id"].unique().tolist())
        raise ValueError(f"Question text mismatch for question_id values: {mismatched_ids[:10]}")

    merged = merged.drop(columns=["question_official"])
    merged["model"] = config.model_name

    ordered_cols = [
        "user",
        "question_id",
        "question",
        "llm_response",
        "model",
        "freeresponse",
        "selection_text",
        "selection_position",
        "Age",
        "Sex",
        "Ethnicity simplified",
        "U.s. political affiliation",
        "cluster_kmeans",
    ]
    return merged[ordered_cols].sort_values(["question_id", "user"]).reset_index(drop=True)


def save_outputs(df: pd.DataFrame, config: PrepareConfig) -> tuple[Path, Path]:
    out_dir = Path(config.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / config.output_name
    meta_path = out_dir / f"{Path(config.output_name).stem}.meta.json"

    df.to_csv(csv_path, index=False)

    payload = {
        "config": asdict(config),
        "rows": int(len(df)),
        "unique_question_id": int(df["question_id"].nunique()),
        "unique_user_question": int(df[["user", "question_id"]].drop_duplicates().shape[0]),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return csv_path, meta_path


def main() -> None:
    df = build_rows(CONFIG)
    csv_path, meta_path = save_outputs(df, CONFIG)
    print(f"[save] judge_rows={csv_path}")
    print(f"[save] meta={meta_path}")
    print(f"[summary] rows={len(df)} questions={df['question_id'].nunique()} model={CONFIG.model_name}")


if __name__ == "__main__":
    main()
