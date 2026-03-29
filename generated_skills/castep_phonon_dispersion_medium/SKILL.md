```markdown
---
name: generating-synthetic-phonon-dispersion-json
description: Generate physically plausible synthetic phonon-dispersion JSON from a config file with strict structural and numerical constraints. Use when creating test fixtures for phonon/dispersion visualization pipelines.
---

# Generating Synthetic Phonon Dispersion JSON

## When to Use
Use this skill when a terminal task asks to create a `synthetic_phonon_data.json`-style file from config parameters (typically `num_atoms` and `num_qpoints`) while satisfying physics-inspired constraints and strict schema checks.

All 3 observed runs passed (15/15 tests each) using the same core pattern: robust config parsing, deterministic smooth branch generation, hard post-processing guards, and explicit sanity checks.

## Minimal Reliable Workflow
1. **Inspect and parse config defensively.**
   - Read `phonon_config.txt`.
   - Parse key/value forms with both `:` and `=`.
   - Accept key variants (`num_atoms`, `number of atoms`, `num_qpoints`, `q-points`, etc.).
   - Validate: `num_atoms >= 1`, `num_qpoints >= 2`.

2. **Derive required dimensions.**
   - Compute `num_modes = 3 * num_atoms`.
   - Build `qpoints` as evenly spaced values from 0 to 1 inclusive:
     - `qpoints = [i/(num_qpoints-1) for i in range(num_qpoints)]`

3. **Generate smooth deterministic frequencies (no randomness).**
   - Build 3 acoustic modes using smooth functions of `q` (e.g., `sin(pi*q/2)` variants).
   - Build optical modes from positive base frequencies plus gentle sinusoidal modulation.
   - Keep optical branches above acoustic branches with a buffer.
   - Keep all values non-negative and cap max below 20 THz (e.g., 19.5 or 19.9).

4. **Apply hard constraints after generation.**
   - Force `frequencies[0][:3] = [0.0, 0.0, 0.0]` exactly.
   - Round every frequency to 2 decimals.
   - Ensure each row length is exactly `num_modes`.

5. **Write JSON with exact schema.**
   - Output:
     - `num_modes` (int)
     - `qpoints` (list of floats)
     - `frequencies` (list of lists)

6. **Run quick local assertions before finishing.**
   - Check shape consistency and numeric constraints with a short Python validation snippet.

## Common Pitfalls
- **Brittle config parsing.**  
  Assuming only one key spelling fails portability. Successful runs used flexible regex/key matching.
- **Missing inclusive endpoint in q-grid.**  
  Using `i/num_qpoints` instead of `i/(num_qpoints-1)` breaks expected range/spacing.
- **Gamma-point equality drift.**  
  Relying only on floating formulas can miss exact-zero assertions; explicitly overwrite first 3 values at q=0.
- **Forgetting post-rounding enforcement.**  
  Round after all adjustments, then re-assert Gamma zeros.
- **Optical branch dipping to zero/negative.**  
  Add a minimum floor for optical modes and non-negativity clamp.
- **Using random noise for realism.**  
  Can violate smoothness checks and reproducibility; deterministic smooth functions passed consistently.

## Verification Strategy
Run a targeted validation script (or tests) that mirrors known checks from passing runs:

1. **File/schema checks**
   - File exists.
   - Valid JSON.
   - Keys present: `num_modes`, `qpoints`, `frequencies`.

2. **Dimension checks**
   - `num_modes == 3 * num_atoms`.
   - `len(qpoints) == num_qpoints`.
   - `len(frequencies) == len(qpoints)`.
   - Every row length equals `num_modes`.

3. **Numerical/physics checks**
   - `qpoints[0] == 0.0`, all qpoints in `[0,1]`.
   - `frequencies[0][0:3] == [0.0, 0.0, 0.0]`.
   - All frequencies `>= 0`.
   - `max(frequencies) < 20`.
   - Optical modes non-zero at Gamma.
   - Values are rounded to 2 decimals.
   - Adjacent q-point changes are smooth (no large jumps).

## References to Load On Demand
- Reusable Python generator template with:
  - flexible config parser,
  - sinusoidal acoustic/optical construction,
  - post-processing guardrail block,
  - assertion-based preflight validator.
```
