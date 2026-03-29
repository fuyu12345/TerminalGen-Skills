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

## Acceleration

The script already uses:

- batched generation
- `torch.inference_mode()`
- `device_map="auto"`
- BF16/FP16 capable loading via config
- `sdpa` or `flash_attention_2` when available
- TF32 on CUDA

If your GPU memory is tight, enable `load_in_4bit` or `load_in_8bit` in the script config.
