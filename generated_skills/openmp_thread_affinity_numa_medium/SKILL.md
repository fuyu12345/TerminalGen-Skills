```markdown
---
name: configuring-openmp-thread-affinity-for-numa-topologies
description: Derive and write NUMA-aware OpenMP affinity settings into a machine-checked JSON config by reading topology files, selecting core binding policy, and validating schema/values. Use when generating per-host OpenMP affinity guidance from NUMA topology snapshots.
---

# Configuring OpenMP Thread Affinity for NUMA Topologies

## When to Use

Use this skill when a task asks for a single JSON config mapping multiple servers to OpenMP affinity strings (for example `OMP_PLACES` + `OMP_PROC_BIND`), especially when topology files describe NUMA nodes, core layout, and SMT.

## Minimal Reliable Workflow

1. **Inspect required output contract first.**  
   Confirm output path, required keys, and whether values must be strings.

2. **Read all topology inputs before writing config.**  
   Extract, per server:
   - NUMA node count
   - Physical core count
   - Whether SMT/logical CPUs are present

3. **Select affinity primitives that are valid and NUMA-aware.**
   - Set `OMP_PLACES=cores` to bind at physical-core granularity.
   - Set `OMP_PROC_BIND` to a valid policy (`close` or `spread`) based on workload intent:
     - Prefer `close` for locality-sensitive phases.
     - Prefer `spread` for cross-domain bandwidth distribution.
   - Optionally add `OMP_NUM_THREADS=<physical_cores>` to avoid SMT oversubscription.

4. **Write exactly the required JSON shape.**
   - Use exactly the required server keys (no extras, no omissions).
   - Keep each server value as a single space-separated string of env assignments.

5. **Run lightweight local validation before completion.**
   - `python3 -m json.tool /workspace/affinity_config.json`
   - `cat /workspace/affinity_config.json` for visual key/value check.

## Common Pitfalls

- **Skipping topology inspection and copying a blind template.**  
  All successful runs read `README.md` and all server topology files first.
- **Violating schema constraints.**  
  Tests explicitly check: file exists, valid JSON, exactly three expected keys, and string values.
- **Using invalid OpenMP tokens.**  
  Tests check valid `OMP_PLACES` and `OMP_PROC_BIND` values; typoed values fail.
- **Ignoring SMT on large NUMA hosts.**  
  On systems with 2x logical threads per core, omitting `OMP_NUM_THREADS` can cause unintended thread count behavior. Two successful runs mitigated this with physical-core counts.
- **Assuming only one binding policy is acceptable.**  
  Evidence shows both `close` and `spread` can pass when used with `OMP_PLACES=cores` and valid NUMA-aware strings; choose based on workload objective, not guesswork.

## Verification Strategy

Tie checks directly to observed test assertions:

1. **Structural checks**
   - File exists at required path.
   - JSON parses cleanly.
   - Keys are exactly the required server set.
   - All values are strings.

2. **Semantic checks**
   - Every value contains `OMP_PLACES=<valid>` (prefer `cores` for NUMA/core pinning).
   - Every value contains `OMP_PROC_BIND=<valid>` (`close|spread|master`, per allowed set).
   - Ensure config reflects NUMA-aware intent (core placement + bind policy present together).

3. **Final confidence pass**
   - Re-open produced JSON and confirm no accidental extra whitespace/newlines broke heredoc.
   - If available, run task test suite (`pytest /tests/test_outputs.py -rA`) before marking complete.

## References to Load On Demand

- OpenMP environment variable semantics: `OMP_PLACES`, `OMP_PROC_BIND`, `OMP_NUM_THREADS`
- NUMA topology interpretation basics (nodes, distances, SMT vs physical cores)
```
