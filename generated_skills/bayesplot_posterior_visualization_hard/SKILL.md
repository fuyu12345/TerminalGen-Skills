---
name: generating-mcmc-diagnostic-reports-from-csv
description: Generate a robust MCMC diagnostic PDF and text summary from posterior draw tables, including trace/density/autocorrelation/interval diagnostics and convergence flags. Use when posterior samples are available but convergence review is incomplete.
---

# Generating MCMC Diagnostic Reports from CSV

## When to Use
- Use when a task requires:
  - `/workspace/mcmc_diagnostics.pdf` (multi-page, programmatic diagnostics)
  - `/workspace/diagnostic_summary.txt` (line-wise findings like `CONVERGENCE_ISSUE:` / `LOW_ESS:`)
- Use when posterior data is in flat files (especially CSV) with uncertain schema/versioned plotting libraries.
- Use when environment library versions are unknown and ArviZ APIs may differ.

## Minimal Reliable Workflow
1. **Discover and inspect input structure first.**
   - Locate candidate files.
   - Print shape/columns/head.
   - Identify:
     - chain column (`chain`, `.chain`, `chain_id`)
     - draw/iteration column (`draw`, `iteration`, `iter`, `.draw`)
     - sampler-diagnostic columns (`divergent`, `divergent__`, etc.)
     - true parameter columns (numeric, excluding metadata/sampler columns).

2. **Normalize draws into chain × draw arrays per parameter.**
   - Sort by chain and draw.
   - If no draw column exists, generate per-chain index.
   - If chain lengths differ, truncate to common minimum and record warning.
   - Exclude sampler columns (especially `divergent`) from parameter list.

3. **Compute diagnostics with version-safe logic.**
   - Prefer manual/statistically simple fallback for reliability:
     - R-hat (when chains ≥ 2), otherwise mark unavailable.
     - ESS per parameter.
   - If using ArviZ stats, wrap calls in compatibility guards (API differences were observed).

4. **Generate PDF with matplotlib-first fallback (avoid fragile plotting APIs).**
   - Include at minimum:
     - trace plots (all parameters),
     - density overlays,
     - autocorrelation plots,
     - interval/forest-style parameter comparison.
   - Add overview page with source path, chain count, draw count, parameter count.
   - Add divergence visualization/page if divergence indicator exists.

5. **Write summary lines in strict finding format.**
   - Emit one finding per line:
     - `CONVERGENCE_ISSUE: ... (R_hat=...)` for finite R-hat > 1.01
     - `LOW_ESS: ... (ESS=...)` for ESS < 400
     - `SAMPLING_WARNING: ...` for divergences/pathologies
     - `CONVERGENCE_WARNING: R_hat_not_available_single_chain` when only one chain
   - Avoid falsely claiming convergence when R-hat is `NaN`/unavailable.

6. **Verify artifacts and content before completion.**
   - Confirm both output files exist and are non-empty.
   - Confirm PDF is substantial (not tiny/truncated).
   - Confirm summary includes parameter-level lines and required warning types.

## Common Pitfalls
- **Assuming modern ArviZ constructor signatures.**  
  Evidence: `TypeError: from_dict() got an unexpected keyword argument 'posterior'` occurred repeatedly.  
  Guardrail: use compatibility wrappers or avoid dependency on fragile constructor paths.

- **Using ArviZ plotting functions that break on coordinate mismatches.**  
  Evidence: trace plotting failed with draw-coordinate conflict in one run.  
  Guardrail: keep matplotlib-native plotting fallback as primary/backup path.

- **Treating sampler diagnostics as model parameters.**  
  Evidence: `divergent` was accidentally reported as `LOW_ESS` parameter.  
  Guardrail: explicitly exclude known sampler columns from parameter set.

- **Reporting “CONVERGENCE_OK” when R-hat is undefined (single chain).**  
  Evidence: runs produced `R_hat=nan` while initially claiming convergence OK.  
  Guardrail: detect `n_chains < 2` and emit explicit convergence warning instead.

- **Command batching mistakes causing concatenated execution.**  
  Evidence: missing trailing newline and literal `C-c` misuse produced noisy/stuck sessions.  
  Guardrail: terminate every command with newline; send proper interrupt sequences in the runner’s expected format.

- **Assuming tail ESS API parity.**  
  Evidence: `az.ess(..., method='tail')` required `prob` in some environments.  
  Guardrail: guard tail-ESS calls or rely on robust bulk/manual ESS for pass criteria.

## Verification Strategy
- **File-level checks**
  - Assert `/workspace/mcmc_diagnostics.pdf` exists and is non-trivial size.
  - Assert `/workspace/diagnostic_summary.txt` exists and is non-empty.

- **Content-level checks**
  - Confirm summary contains parameter names and finding prefixes (`LOW_ESS`, `CONVERGENCE_ISSUE`, warnings).
  - Confirm no sampler-only columns are mislabeled as posterior parameters.
  - Confirm single-chain case produces convergence limitation warning, not false “OK”.

- **Execution-level checks**
  - Run project tests (`pytest /tests/test_outputs.py -rA`) when available.
  - If tests pass but diagnostics look suspiciously sparse, inspect PDF size/page generation logs and summary logic for silent plotting/API failures.

## References to Load On Demand
- R-hat and ESS formula notes (Gelman-Rubin + Geyer IPS variants).
- ArviZ version compatibility matrix (`from_dict`, `ess` signatures).
- Minimal matplotlib templates for trace/density/acf/interval multipage PDFs.
