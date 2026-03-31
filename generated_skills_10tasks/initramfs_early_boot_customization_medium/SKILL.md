---
name: resolving-initramfs-hook-order
description: Derive and validate a dependency-safe initramfs hook execution order from mixed-quality docs, reconcile naming mismatches, and emit a strict one-hook-per-line output list. Use when hook inventory and dependency files disagree on names or completeness.
---

# Resolving Initramfs Hook Order

## When to Use
Use this skill when an initramfs (or similar early-boot pipeline) must be reordered from documentation files, especially when:

- A **current active hook list** exists (authoritative output set).
- A **dependency file** exists but may contain **alias/stale names**.
- A **boot error log** provides operational clues not fully captured in dependencies.
- Grading/validation requires strict membership, uniqueness, and ordering constraints.

## Minimal Reliable Workflow
1. **Treat the active hook list as the output contract.**  
   Load `current_hooks.txt` (or equivalent) as the exact set of hooks that must appear in final output.

2. **Parse dependency edges conservatively.**  
   Read `hook_dependencies.txt` lines like `target: requires a, b`.  
   Build edges only for dependencies that can be applied safely to the active set.

3. **Reconcile name mismatches before sorting.**  
   Detect likely aliases (example seen in runs: `load_modules` vs `module_load`, `mount_root` vs `root_mount`).  
   Apply an explicit alias map only when strongly supported by naming/log evidence; otherwise leave unmatched names out of hard constraints.

4. **Topologically sort only the active hooks.**  
   Compute ordering constraints among hooks in the authoritative set, not all names mentioned anywhere.

5. **Use boot log as a secondary tie-breaker.**  
   For unconstrained hooks, prefer operationally sane sequencing (e.g., modules/udev/device mapper before storage scan/unlock; root/filesystem setup before application hooks).

6. **Write final output strictly.**  
   Save to target file with exactly one hook per line, no annotations.

## Common Pitfalls
- **Including non-active hooks in output.**  
  Observed in Run 1 intermediate result (`load_modules`, `filesystem_setup`, etc.) causing “extra hooks” and invalid output.
- **Blind topo-sort over dependency file universe.**  
  If dependency docs include stale/alternate names, full-graph sorting can produce a valid graph but invalid deliverable.
- **Leaving unconstrained hooks in bad positions.**  
  Runs 2/3 initially produced `application_hooks` too early because it had no explicit dependency edge; boot log showed this is operationally wrong.
- **Assuming dependency names are canonical.**  
  Dependency assertions in tests targeted relationships like “load_modules before device_mapper,” while active list used `module_load`; alias handling was required.

## Verification Strategy
Run verification in this order:

1. **File checks**
   - Output file exists and non-empty.

2. **Set integrity checks**
   - Output count equals active hook count.
   - No duplicates.
   - `set(output) == set(current_hooks)`.

3. **Dependency checks on reconciled names**
   - For each applicable edge, ensure prerequisite index `<` target index.
   - Include explicit checks matching critical assertions seen in tests:
     - `module_load/load_modules` before `device_mapper`
     - `device_mapper` before `lvm_scan`
     - `udev_trigger` before `cryptsetup`

4. **Operational sanity checks (from boot logs)**
   - Ensure late hooks like `application_hooks` do not precede filesystem/root readiness.
   - If dependency graph leaves these unconstrained, enforce via tie-break ordering policy.

## References to Load On Demand
- Kahn topological sort for deterministic ordering.
- Alias-reconciliation pattern for stale config vocabularies.
- Lightweight Python validator for set + order constraints.
