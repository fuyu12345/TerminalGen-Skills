---
name: fitting-stable-ordinal-proportional-odds
description: Fit a proportional-odds ordinal model with data cleaning and numerical-stability guardrails, then emit strict key=value outputs. Use when solving terminal tasks that require ordinal regression predictions and formatted result files.
---

# Fitting Stable Ordinal Proportional Odds

## When to Use

- Build an ordinal logistic (proportional-odds) model from tabular data.
- Handle missing predictors and outliers before fitting.
- Output fixed-format fields (for graders/tests) including a probability like `P(Y >= k)`.
- Prevent degenerate outputs (exact `0.0000`/`1.0000`) caused by unstable fits.

## Minimal Reliable Workflow

1. **Inspect data before modeling.**
   - Print shape, missing counts, outcome category counts, and predictor summaries.
   - Confirm ordinal outcome has only expected levels (e.g., `1,2,3,4`).

2. **Clean deterministically.**
   - Coerce required columns to numeric with invalid parsing -> `NaN`.
   - Drop rows with invalid/missing outcome.
   - Impute continuous predictors with median.
   - Impute binary indicator with mode, then force to `{0,1}`.
   - Cap extreme continuous outliers (IQR winsorization) and apply same cap to prediction inputs.

3. **Fit proportional-odds model with stability first.**
   - Use `statsmodels.miscmodels.ordinal_model.OrderedModel(..., distr="logit")`.
   - Standardize continuous predictors before fitting to reduce optimizer instability.
   - Fit with a robust optimizer (`lbfgs`/`bfgs`) and adequate iterations.

4. **Check fit quality, not only convergence.**
   - Treat `converged=True` as necessary but not sufficient.
   - Flag instability if any of: Hessian inversion warnings, huge coefficient magnitudes, non-finite standard errors/p-values, or near-deterministic predictions.

5. **Handle quasi-separation before final output.**
   - If instability is detected, refit with a simplified predictor set (drop separating feature) or other documented stabilization strategy.
   - Recompute the required probability after refit.
   - Keep the approach reproducible and documented in script comments.

6. **Compute probability robustly across return types.**
   - `pred = model.predict(...)`
   - Convert with `arr = np.asarray(pred)`; do not assume pandas DataFrame.
   - For “Good or better”: `p = arr[0,2] + arr[0,3]` (indexing by ordinal order).

7. **Write exact output format with real newlines.**
   -  
     `MODEL_CONVERGED=<yes|no>`  
     `SIGNIFICANT_PREDICTORS=<comma-list|none>`  
     `PROBABILITY_GOOD_OR_BETTER=<rounded 4dp>`
   - Ensure actual newline characters, not literal `\n`.

## Common Pitfalls

- **Assuming prediction is a DataFrame**  
  Observed failure: `AttributeError: 'numpy.ndarray' object has no attribute 'iloc'`.  
  Prevention: always convert predictions via `np.asarray(...)`.

- **Accepting a degenerate fit because convergence says “yes”**  
  Observed across runs: Hessian inversion warnings, huge parameters, and final `PROBABILITY_GOOD_OR_BETTER=0.0000`, which failed range checks.  
  Prevention: add post-fit stability diagnostics and refit strategy.

- **Terminal command framing errors**  
  Observed: missing trailing newline caused command concatenation; heredoc confusion; literal `C-c` mishandling.  
  Prevention: end every command with newline, keep heredocs isolated, and verify prompt return before next command.

- **Writing escaped newlines into result file**  
  Observed intermediate output containing `\\n` text.  
  Prevention: write file with normal `\n` in Python strings and re-open file to verify plain line breaks.

## Verification Strategy

1. **File-level checks**
   - `cat /workspace/results.txt`
   - Confirm exactly three keys and expected spelling.

2. **Model sanity checks**
   - Ensure probability is finite and strictly non-extreme for target case (e.g., `0.01 <= p <= 0.99` when required by tests).
   - Print coefficients and warning status to catch separation early.

3. **Prediction consistency check**
   - Recompute target probability in a one-off Python command using the same preprocessing pipeline.
   - Confirm written value matches recomputed value (4 decimal rounding).

4. **Run grader tests before finalizing**
   - Execute task tests (e.g., `pytest /tests/test_outputs.py -rA`) and specifically confirm probability-range test passes.

## References to Load On Demand

- `statsmodels.miscmodels.ordinal_model.OrderedModel` docs (return type and fit diagnostics).
- Notes on quasi-/complete separation in logistic-family models and mitigation patterns.
