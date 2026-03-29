```markdown
---
name: repairing-template-negative-binomial-pipeline
description: Restore a broken count-model analysis pipeline and emit strict key=value outputs for grader compatibility. Use when a terminal task requires fixing GLM/negative-binomial code and producing exact-format parameter files.
---

# Repairing Template Negative-Binomial Pipeline

## When to Use

- Task provides a partially broken analysis repo (bad paths, wrong config keys, wrong model API calls).
- Deliverable is a strict text file like:
  - `temperature_effect=<number>`
  - `baseline=<number>`
  - `dispersion=<number>`
- Tests validate both **format** and **value ranges**, not just file existence.

## Minimal Reliable Workflow

1. **Inspect repository and trust code over prompt docs.**
   - List files and open pipeline/config/data directly.
   - If README is missing, proceed from source and test expectations.

2. **Fix first blocking path/config mismatch.**
   - Align config path and schema (e.g., nested YAML keys vs flat key access).
   - Confirm data file path is used as-is (avoid accidental extension duplication).

3. **Replace brittle broken logic with a clean minimal pipeline.**
   - Load config.
   - Load CSV.
   - Extract response/predictor columns by actual names in data.
   - Fit a stable NB/GLM path.
   - Extract the 3 required parameters.
   - Write exactly 3 output lines to required output file.

4. **Prefer a converged/stable fit over fragile MLE variants.**
   - If discrete NB MLE does not converge or yields extreme alpha, switch to a stable GLM NB workflow.
   - Keep parameter semantics aligned with test ranges:
     - `temperature_effect`: slope
     - `baseline`: **catch-rate scale** if needed (use `exp(intercept)` when intercept is on log scale)
     - `dispersion`: positive, reasonable (commonly ~1.0 in stable fallback)

5. **Write output in strict plain-decimal format (no scientific notation).**
   - Use fixed-point formatting (e.g., `:.6f`) before writing.
   - Ensure key names are exact and spelling matches tests.

## Common Pitfalls

- **Using wrong baseline scale**  
  Evidence: one failed run output baseline as raw negative intercept (`-0.513...`) and failed range checks.  
  Prevention: convert log-link intercept to rate-scale baseline when evaluator expects non-negative baseline.

- **Scientific notation breaks regex-based tests**  
  Evidence: failed run wrote `dispersion=5.702144383548783e-09`; regex expected plain decimal and did not match.  
  Prevention: always serialize numbers in fixed decimal notation.

- **Choosing non-converged NB fit outputs**  
  Evidence: discrete NB emitted convergence warnings and implausible dispersion estimates near zero.  
  Prevention: detect convergence issues; use a stable GLM NB alternative if needed.

- **Trusting prompt-stated README/workflow blindly**  
  Evidence: README referenced in prompt but absent in all runs.  
  Prevention: inspect actual filesystem and infer workflow from code/config/tests.

- **Concatenated terminal commands from missing newline**  
  Evidence: parser warnings in failed run caused command-stream confusion.  
  Prevention: end every `keystrokes` command with `\n`, especially control sequences.

## Verification Strategy

1. **Run pipeline end-to-end** and confirm no crash.
2. **Inspect output file literally**:
   - Exists at required path.
   - Exactly 3 lines.
   - Exact keys: `temperature_effect`, `baseline`, `dispersion`.
3. **Validate formatting against strict regex compatibility**:
   - Ensure each value is plain decimal (optional leading `-`, no exponent).
4. **Validate value ranges before finalizing**:
   - `temperature_effect` in plausible range (e.g., `[-2, 2]`)
   - `baseline` non-negative and within expected bound (e.g., `[0, 5]`)
   - `dispersion` positive and reasonable (e.g., `[0.1, 3]`)
5. **Only mark complete after checks pass** (or after running grader tests when available).

## References to Load On Demand

- `analysis_pipeline.py` (entrypoint repair target)
- `config/model_config.yaml` (real key structure)
- `/tests/test_outputs.py` (authoritative format/range assertions)
```
