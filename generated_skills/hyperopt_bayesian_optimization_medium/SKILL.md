```markdown
---
name: optimizing-mixed-blackbox-parameters
description: Optimize a 4-parameter mixed continuous/integer black-box objective under evaluation-count and reproducibility constraints, and emit a validated JSON result. Use when a terminal task requires score-threshold minimization with strict output schema.
---

# Optimizing Mixed Black-Box Parameters

## When to Use

Use this skill when a task asks to:
- minimize a black-box function with mixed variable types (float + int),
- respect hard bounds and minimum evaluation count (e.g., `>=100`),
- set a fixed random seed (e.g., `42`),
- write final params to a strict JSON file (`best_params.json`-style),
- pass tests that re-evaluate the saved parameters.

---

## Minimal Reliable Workflow

1. **Run a preflight integrity check before any optimization.**
   - Inspect the objective file (`sed -n ...`).
   - Perform a smoke import and single call.
   - Confirm callable name/signature and that import is not circular.

2. **Branch on objective availability immediately.**
   - If import/call works: proceed.
   - If import fails (e.g., circular self-import), treat as environment/harness defect and resolve objective availability first (recover correct module/path), *then* optimize.

3. **Set reproducibility first.**
   - Seed all RNGs used (`random.seed(42)`, `np.random.seed(42)`).

4. **Normalize parameter handling in one place.**
   - Clip float bounds for continuous vars.
   - Round + clip integer vars.
   - Enforce output types (`x1/x2` float, `x3/x4` int).

5. **Use a staged mixed-variable search.**
   - Start with broad random/global exploration.
   - Follow with local refinement around incumbent best.
   - Ensure total unique evaluations exceed requirement (e.g., 120+ buffer above 100).

6. **Track and persist best result only.**
   - Maintain `best_score`, `best_params`, and `eval_count`.
   - Write exact schema JSON to required path.

7. **Run post-save functional verification.**
   - Reload JSON.
   - Re-evaluate objective with saved params.
   - Print score and threshold check.

8. **Run grader-facing checks if available.**
   - Execute provided tests (`pytest /tests/test_outputs.py`) when possible.

---

## Common Pitfalls

- **Skipping import smoke test**  
  In all three runs, `/workspace/objective_function.py` contained circular self-import logic; naive optimization attempts failed with `ImportError` and produced no JSON.

- **Starting long optimization before confirming callable function**  
  This wastes time and tokens; early failures showed repeated retries without a valid objective source.

- **Running from wrong working directory/module path**  
  One run hit `ModuleNotFoundError` from `/tmp` after creating a file in `/workspace`.

- **Not creating output due upstream failures**  
  Multiple intermediate attempts failed tests implicitly because `/workspace/best_params.json` was missing.

- **Terminal command formatting errors**  
  Missing newline after control keystrokes caused command concatenation warnings; keep command termination strict.

- **Overcomplicated module discovery before basic sanity checks**  
  Large filesystem/module hunts and `.pyc` disassembly did not recover a callable objective in this case.

---

## Verification Strategy

Tie verification to the observed test expectations:

1. **File existence + valid JSON**
   - `cat /workspace/best_params.json`
   - `python -c "import json; json.load(open('/workspace/best_params.json'))"`

2. **Schema + type checks**
   - Confirm keys: `x1,x2,x3,x4`
   - Confirm types: floats for `x1,x2`; ints for `x3,x4`

3. **Bounds checks**
   - `x1,x2 in [-5,5]`, `x3,x4 in [1,20]`

4. **Objective score check**
   - Evaluate objective with saved params.
   - Assert `score <= target` (e.g., `<= 1.80`).

5. **Evaluation-count check**
   - Print/confirm `eval_count >= 100` from optimizer run log.

6. **End-to-end test check**
   - Run task tests; expect pass on:
     - file exists,
     - valid JSON,
     - required fields/types/bounds,
     - objective threshold,
     - improvement over baseline.

---
```
