```markdown
---
name: generating-autodock-vina-grid-configs
description: Transform binding-site CSV data into AutoDock Vina grid JSON configs with validator-compatible size rounding. Use when generating batch docking grid parameters from center coordinates and site radii.
---

# Generating AutoDock Vina Grid Configs

## When to Use

- Generate `/workspace/grid_configs.json` (or equivalent) from a CSV containing:
  - `protein_id`, `center_x`, `center_y`, `center_z`, `site_radius`
- Produce one JSON object per protein with fields:
  - `protein_id`, `center`, `size`, `exhaustiveness`
- Satisfy strict test harnesses that validate numeric rounding behavior exactly.

## Minimal Reliable Workflow

1. Read the input CSV with `csv.DictReader`.
2. Preserve center coordinates directly from input as floats in `[x, y, z]`.
3. Compute base grid span as `base = 2.5 * site_radius`.
4. Round size using the validator’s exact formula:
   - `size_val = round(base * 2) / 2`
   - Replicate this literally (Python `round`, ties-to-even), not ceiling or half-up.
5. Set cubic size: `size = [size_val, size_val, size_val]`.
6. Set `exhaustiveness = 8` for every entry.
7. Write a JSON array to the required output path.

## Common Pitfalls

- **Using ceiling-to-0.5 instead of nearest-to-0.5**  
  Evidence: all 3 runs failed only `test_size_calculation_and_rounding` with `1ABC: expected 21.0, got 21.5`.  
  Cause: implementations used `ceil(...)` (or equivalent “always round up”) based on “at least 2.5× radius” wording.
- **Using custom half-up rounding instead of Python’s `round` behavior**  
  In tie cases (e.g., `21.25`), Python `round(42.5)` becomes `42` (banker’s rounding), producing `21.0`, not `21.5`.
- **Assuming prose requirements override assertions**  
  When wording is ambiguous (“at least” + “nearest”), prioritize the explicit test assertion formula.

## Verification Strategy

1. Run test suite early after generation:
   - `pytest /tests/test_outputs.py -rA`
2. If only size-rounding test fails, compare formula directly against output:
   - Recompute expected with `round((2.5 * radius) * 2) / 2` and diff against JSON.
3. Spot-check tie case from observed failures:
   - `site_radius = 8.5` → `2.5 * 8.5 = 21.25` → expected `21.0` under Python `round`.
4. Confirm all non-rounding invariants:
   - JSON valid array
   - one entry per protein
   - exact required fields
   - cubic size
   - `exhaustiveness == 8`
   - centers match input.

## References to Load On Demand

- Python rounding semantics (`round` uses ties-to-even).
- AutoDock Vina grid parameter conventions (center and cubic box size fields).
```
