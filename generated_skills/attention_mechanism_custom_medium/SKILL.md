```markdown
---
name: repairing-attention-mechanism-implementations
description: Diagnose and fix scaled dot-product attention bugs, validate data artifacts, and produce required output files with reproducible checks. Use when attention layer tasks fail on softmax axis/scaling issues or when provided test-data files may not match their extension.
---

# Repairing Attention Mechanism Implementations

## When to Use

- Fixing `ScaledDotProductAttention`-style implementations with:
  - missing score scaling by `sqrt(d_k)`
  - softmax applied on the wrong axis
- Producing required deliverables like:
  - `attention_fixed.py`
  - `results.txt` with strict line format
- Handling terminal tasks where test data appears malformed (e.g., `.npz` path that is actually text/script content)

## Minimal Reliable Workflow

1. **Patch the attention math first (no assumptions about data file yet).**
   - Compute scores as `Q @ K.transpose(0, 2, 1) / sqrt(d_k)`.
   - Apply softmax along key dimension (`axis=-1`).
   - Compute output as `attention_weights @ V`.
   - Keep class/interface unchanged.

2. **Create `attention_fixed.py` with only required logic and imports.**
   - Preserve method signatures (`__init__`, `forward`, `softmax`).

3. **Validate the test data artifact type before loading.**
   - Do not trust extension alone.
   - If `np.load(path)` fails with pickling/format errors, inspect first bytes/text via Python (`open(...,'rb').read(16)` or `sed/head`).
   - In observed runs, `/workspace/test_data.npz` was initially a Python script (not a zip/npz), which caused:
     - `ValueError: contains pickled data` and
     - `_pickle.UnpicklingError: could not find MARK`.

4. **If the “data file” is actually a generator script, execute it in a controlled namespace to materialize real arrays/artifacts.**
   - Extract `Q/K/V` from namespace after `exec`, or let it generate a proper `.npz` if script does so.
   - Then run forward pass and compute:
     - `weights_sum_correct` (`sum(axis=-1)` close to 1.0, atol 1e-3)
     - `output_shape_correct` (`(2,4,8)` or expected shape)
     - `max_score_magnitude` from scaled scores.

5. **Write `results.txt` in exact required format (3 lines, lowercase booleans).**

6. **Run the official test command before completion.**
   - Ensure implementation correctness test passes, not just local ad-hoc checks.

## Common Pitfalls

- **Assuming `.npz` is valid binary data.**  
  Evidence: one failed run repeatedly used `np.load(..., allow_pickle=True)` and still failed because file content was plain Python text.
- **Using synthetic fallback tensors to fabricate `results.txt`.**  
  Evidence: local booleans became `true`, but grader still failed implementation correctness against real expected data flow.
- **Fixing only model code but not data-loading path.**  
  Evidence: `attention_fixed.py` was correct, yet run failed because `results.txt` was never produced due to load errors.
- **Marking task complete before re-running verification.**  
  Evidence: premature completion attempts happened while required output file was missing.

## Verification Strategy

1. **Artifact checks**
   - Confirm `attention_fixed.py` exists and is valid Python.
   - Confirm `results.txt` exists and has exactly:
     - `weights_sum_correct=...`
     - `output_shape_correct=...`
     - `max_score_magnitude=...` (numeric)

2. **Numerical checks**
   - Recompute weights sum on `axis=-1` and assert allclose to 1.0 (`atol=1e-3`).
   - Assert output shape matches expected tensor shape.

3. **Harness-aligned checks**
   - Reproduce official test command (`pytest /tests/test_outputs.py -rA`).
   - Specifically guard against prior failure mode:
     - `test_implementation_correctness` failing at `np.load('/workspace/test_data.npz')`.
   - If that error appears, inspect and normalize data artifact format before finalizing.

## References to Load On Demand

- NumPy softmax-stability pattern: subtract per-axis max before `exp`.
- Quick file-type triage without `file` utility:
  - `python -c "print(open(path,'rb').read(16))"`
  - `zipfile.is_zipfile(path)`
- Safe controlled-script execution pattern for data bootstrap (`exec` into isolated dict, then extract expected keys).
```
