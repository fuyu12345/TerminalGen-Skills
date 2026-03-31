---
name: normalizing-dask-worker-resource-output
description: Derive canonical worker resource declarations from heterogeneous Dask YAML configs and emit the exact JSON mapping format required by graders. Use when a task asks to validate/fix Dask worker resources but expects a separate structured output file.
---

# Normalizing Dask Worker Resource Output

## When to Use

Use this skill when:

- Input files are Dask worker YAML configs with inconsistent resource declarations (`resource`, `custom_resources`, list-based resources, uppercase keys, stringified numbers).
- A benchmark/grader expects a **separate JSON deliverable** (not edited YAML) with exact worker-to-resource mappings.
- Output format is strict (fixed keys, fixed string pattern like `gpu:2,memory_gb:64`).

## Minimal Reliable Workflow

1. **Read the task deliverable format first.**  
   Confirm whether the task wants YAML edits or a separate summary file (e.g., `/workspace/solution.json`).

2. **Inspect the reference spec and worker configs.**  
   Check required canonical form: top-level `resources`, lowercase names, numeric semantics, underscore naming.

3. **Normalize each worker’s intended resources.**  
   Convert malformed source patterns into canonical pairs:
   - `gpu:<int>`
   - `memory_gb:<int|float>`
   Preserve required worker identities exactly (`worker1`, `worker2`, `worker3`, etc.).

4. **Write the deliverable JSON exactly as requested.**  
   Use exact key names and exact string formatting/order if examples imply strictness.
   Example shell pattern:
   ```bash
   cat > /workspace/solution.json <<'EOF'
   {
     "worker1": "gpu:2,memory_gb:64",
     "worker2": "gpu:0,memory_gb:128",
     "worker3": "gpu:1,memory_gb:32"
   }
   EOF
   ```

5. **Validate JSON parseability with a baseline tool.**  
   Prefer:
   ```bash
   python3 -m json.tool /workspace/solution.json
   ```
   This worked reliably across runs even when `jq` was unavailable.

## Common Pitfalls

- **Solving the wrong artifact.**  
  Editing YAML files instead of producing the requested JSON output file can fail even if YAML fixes are correct.

- **Using wrong resource key conventions from source files.**  
  Observed bad patterns included:
  - `resource:` instead of `resources:`
  - `custom_resources:`
  - `GPU` instead of `gpu`
  - list-of-objects (`- type: gpu`) instead of map form  
  Normalize to canonical resource names in output.

- **Treating numeric resources as unit strings.**  
  Source files used `"0"`, `"128"`, or `64GB`; output needed numeric semantics represented in the required `resource:value` string format.

- **Relying on non-guaranteed tools (`jq`).**  
  One successful run showed `jq: command not found`; fallback to `python3 -m json.tool`.

- **Missing strict format consistency.**  
  Graders checked exact worker presence and consistent output structure across all workers.

## Verification Strategy

Run these checks before completion:

1. **File exists at exact path**
   ```bash
   ls -l /workspace/solution.json
   ```

2. **JSON is valid**
   ```bash
   python3 -m json.tool /workspace/solution.json
   ```

3. **Schema-level sanity**
   - Contains all required worker keys.
   - Each value is a comma-separated `resource:value` string.
   - Resource names and values match required hardware profiles exactly.

4. **If available, run tests**
   ```bash
   pytest /tests/test_outputs.py -rA
   ```
   In all three trajectories, this strategy produced 7/7 passing tests (`test_solution_file_exists`, valid JSON, all workers, per-worker resources, format consistency).

## References to Load On Demand

- Dask resource spec in task environments (often `/workspace/dask_resource_spec.md`) for canonical YAML semantics.
- Python JSON tooling (`python3 -m json.tool`) for zero-dependency validation.
