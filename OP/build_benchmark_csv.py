#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd


OP_ROOT = Path(__file__).resolve().parent


@dataclass
class BuildConfig:
    predictions_csv: str = str(OP_ROOT / "judge_predictions" / "gemini_all_rows_fr_llama_overton60.csv")
    prediction_column: str = "gemini_fr_avg"
    output_dir: str = str(OP_ROOT / "benchmark_inputs")
    output_name: str = "llama_overton60_gemini_fr_scored.csv"
    model_name: str = "Llama-3.2-3B-Instruct"


CONFIG = BuildConfig()


KEEP_COLUMNS = [
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


def main() -> None:
    cfg = CONFIG
    preds_path = Path(cfg.predictions_csv).expanduser().resolve()
    if not preds_path.exists():
        raise FileNotFoundError(f"Predictions CSV not found: {preds_path}")

    df = pd.read_csv(preds_path)
    missing = [col for col in KEEP_COLUMNS + [cfg.prediction_column] if col not in df.columns]
    if missing:
        raise ValueError(f"Predictions CSV is missing required columns: {missing}")

    out = df[KEEP_COLUMNS].copy()
    out["representation_rating"] = pd.to_numeric(df[cfg.prediction_column], errors="raise")
    out["model"] = cfg.model_name

    out_dir = Path(cfg.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / cfg.output_name
    meta_path = out_dir / f"{Path(cfg.output_name).stem}.meta.json"

    out.to_csv(csv_path, index=False)

    payload = {
        "config": asdict(cfg),
        "rows": int(len(out)),
        "unique_question_id": int(out["question_id"].nunique()),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[save] benchmark_csv={csv_path}")
    print(f"[save] meta={meta_path}")
    print(f"[summary] rows={len(out)} questions={out['question_id'].nunique()} pred_col={cfg.prediction_column}")


if __name__ == "__main__":
    main()
