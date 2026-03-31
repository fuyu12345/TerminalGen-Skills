# OP Local Inference Pipeline

This folder contains a minimal pipeline to:

- load a local Hugging Face model directory
- run the OvertonBench 60-question list
- read the local 60-question input set from `OP/data/`
- save the model responses to `OP/outputs/`

## Model Directory

The script expects a local Hugging Face model directory like:

- `config.json`
- `generation_config.json`
- `tokenizer_config.json`
- `tokenizer.json` or `vocab.json` + `merges.txt`
- `special_tokens_map.json`
- `chat_template.jinja` if the model uses chat templating
- model shard files such as `model-00001-of-00002.safetensors`

## Files

- [run_local_overton60.py](/home/fuyu/projects/skill_hub_terminalgen/TerminalGen-Skills/OP/run_local_overton60.py): main script
- [prepare_judge_rows.py](/home/fuyu/projects/skill_hub_terminalgen/TerminalGen-Skills/OP/prepare_judge_rows.py): expand one model's 60 answers into official `user×question` rows for Gemini judging
- [build_benchmark_csv.py](/home/fuyu/projects/skill_hub_terminalgen/TerminalGen-Skills/OP/build_benchmark_csv.py): convert Gemini prediction output into a benchmark-ready scored CSV
- [overtonbench_60_questions.csv](/home/fuyu/projects/skill_hub_terminalgen/TerminalGen-Skills/OP/data/overtonbench_60_questions.csv): local 60-question input set
- [overtonbench_60_questions.md](/home/fuyu/projects/skill_hub_terminalgen/TerminalGen-Skills/OP/data/overtonbench_60_questions.md): readable version of the same input set
- `outputs/`: generated answers

## Setup

Install the dependencies in a Python environment:

```bash
pip install -r OP/requirements.txt
```

Optional for faster GPU inference on supported setups:

```bash
pip install bitsandbytes flash-attn
```

## Run

Edit the config block at the top of [run_local_overton60.py](/home/fuyu/projects/skill_hub_terminalgen/TerminalGen-Skills/OP/run_local_overton60.py):

- set `model_dir`
- adjust generation settings if needed
- keep or change the default `questions_csv` in `OP/data/`

Then run:

```bash
python OP/run_local_overton60.py
```

## Output

The script writes:

- `*.csv`: question and response table
- `*.json`: same content in JSON
- `*.meta.json`: run config and runtime metadata

## Llama Evaluation Flow

1. Generate the 60 answers:

```bash
python OP/run_local_overton60.py
```

2. Expand the selected answers to official `user×question` rows:

```bash
python OP/prepare_judge_rows.py
```

3. Run Gemini judge on the expanded CSV with the OvertonBench repo:

```bash
python src/prompting_pipeline/prediction.py \
  --client gemini \
  --prompt fr \
  --data /home/fuyu/projects/skill_hub_terminalgen/TerminalGen-Skills/OP/judge_inputs/llama_overton60_full_rows.csv
```

4. Point [build_benchmark_csv.py](/home/fuyu/projects/skill_hub_terminalgen/TerminalGen-Skills/OP/build_benchmark_csv.py) at the Gemini prediction CSV and run:

```bash
python OP/build_benchmark_csv.py
```

5. Compute OP with the OvertonBench benchmark script:

```bash
python src/benchmark_overton_pipeline.py \
  --data /home/fuyu/projects/skill_hub_terminalgen/TerminalGen-Skills/OP/benchmark_inputs/llama_overton60_gemini_fr_scored.csv \
  --cluster_col cluster_kmeans \
  --weighted
```

## Acceleration

The script already uses:

- batched generation
- `torch.inference_mode()`
- `device_map="auto"`
- BF16/FP16 capable loading via config
- `sdpa` or `flash_attention_2` when available
- TF32 on CUDA

If your GPU memory is tight, enable `load_in_4bit` or `load_in_8bit` in the script config.
