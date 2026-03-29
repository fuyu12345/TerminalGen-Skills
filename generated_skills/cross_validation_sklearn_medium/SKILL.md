---
name: evaluating-sklearn-models-with-cross-validation
description: Build a reproducible sklearn cross-validation pipeline for mixed-type tabular data, then emit summary metrics JSON. Use when a task requires replacing unstable train/test evaluation with k-fold results.
---

# Evaluating sklearn Models with Cross-Validation

## When to Use
- Evaluate multiple classifiers on a tabular dataset with both numeric and categorical columns.
- Require robust metrics (mean/std across folds) instead of a single split.
- Need deterministic behavior (`random_state=42`) and strict JSON output for grading/automation.
- Need a terminal-safe, one-shot script that writes results to a required path.

## Minimal Reliable Workflow
1. **Load data and split target**
   - Read CSV with pandas.
   - Set `X = df.drop(columns=[target_col])`, `y = df[target_col]`.

2. **Detect feature types**
   - Build `categorical_cols` from `object/category/bool`.
   - Treat remaining columns as numeric.

3. **Build preprocessing inside a pipeline**
   - Use `ColumnTransformer` with:
     - categorical: `OneHotEncoder(handle_unknown='ignore')`
     - numeric: passthrough (or optional imputation if required).
   - Keep preprocessing inside sklearn `Pipeline` to avoid leakage during CV.

4. **Define CV strategy for reproducibility**
   - Use `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` for binary classification.

5. **Evaluate each model with identical CV**
   - Wrap each model in `Pipeline([('preprocess', ...), ('model', ...)])`.
   - Run `cross_val_score(..., scoring='accuracy')`.
   - Compute and round:
     - `mean_accuracy = round(scores.mean(), 4)`
     - `std_accuracy = round(scores.std(), 4)`

6. **Write strict JSON schema**
   - Save to required location (create parent dir first).
   - Use stable keys expected by tests, e.g.:
     - `logistic_regression`
     - `random_forest`
     - `gradient_boosting`

7. **Confirm file content before completion**
   - `cat` the JSON and sanity-check keys and value ranges.

## Common Pitfalls
- **Marking completion before command output flushes**
  - In two runs, heredoc execution looked incomplete until waiting briefly; verification commands appeared delayed.
  - Prevent by polling (`""` wait command) and confirming prompt/output before finalizing.

- **Command concatenation from missing newline**
  - One run emitted a warning: a command without terminal newline can concatenate with the next command.
  - Prevent by ending every command string with `\n`.

- **Preprocessing outside CV pipeline**
  - Causes leakage and inflated metrics.
  - Prevent by embedding `ColumnTransformer` in per-model `Pipeline`.

- **Non-reproducible splits/models**
  - Omitting `shuffle=True` + `random_state` in CV (and model random states where applicable) makes run-to-run numbers unstable.

- **Output schema drift**
  - Tests expect exact top-level model keys and metric field names; extra nesting or renamed fields can fail validation.

## Verification Strategy
Use a two-layer verification aligned to observed test expectations:

1. **Artifact checks**
   - Confirm file exists at required path.
   - Confirm valid JSON parse.

2. **Schema + metric checks**
   - Assert top-level keys for all required models.
   - Assert each model has `mean_accuracy` and `std_accuracy`.
   - Assert `0 <= mean_accuracy <= 1`.
   - Assert `std_accuracy >= 0`.
   - Assert rounding/precision to 4 decimals in serialized values.

3. **Methodology checks**
   - Confirm 5-fold stratified CV with fixed random state.
   - Confirm categorical handling via encoder in pipeline.

4. **Terminal reliability checks**
   - Wait for heredoc completion if output is pending.
   - Re-run `cat` and (optionally) a short Python assert block before final submission.

## References to Load On Demand
- `sklearn.pipeline.Pipeline`
- `sklearn.compose.ColumnTransformer`
- `sklearn.model_selection.StratifiedKFold`, `cross_val_score`
- `sklearn.preprocessing.OneHotEncoder`
