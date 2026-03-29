---
name: analyzing-yambo-bse-optical-convergence
description: Determine converged Yambo BSE optical-spectrum parameters by extracting physically meaningful first peaks and comparing higher-parameter runs with strict delta thresholds. Use when analyzing multiple parameterized absorption-spectrum directories and producing a single converged parameter report.
---

# Analyzing Yambo BSE Optical Convergence

## When to Use
- Analyze precomputed absorption spectra across runs named with parameters (e.g., bands/kpoints/cutoff).
- Select the **minimum converged** parameter set using peak-energy and peak-intensity stability criteria.
- Produce a machine-checked summary file (e.g., `analysis.txt`) with exact key/value formatting.

## Minimal Reliable Workflow
1. **Locate real data roots before analysis.**  
   Check common mount points (`/data`, `/inputs`, project subdirs), not only `/workspace`.

2. **Enumerate runs and parse parameters from directory names.**  
   Extract `(bands, kpoints, cutoff)` via regex from folder names like `bands_120_kpoints_64_cutoff_8.0`.

3. **Load spectrum data robustly.**  
   Ignore comments/blank lines; parse two numeric columns `(energy, intensity)`.

4. **Extract a physically meaningful first peak (not the first numeric wiggle).**  
   Use a constrained detector:
   - Search local maxima in a physical window (for Si-like tasks, `~3.0–3.5 eV`; broader fallback `2.5–4.5 eV`).
   - Exclude endpoints and tiny pre-edge noise using a significance threshold (e.g., fraction of local/global max).
   - Apply one consistent method across all runs.

5. **Evaluate convergence against higher-parameter runs.**  
   For each candidate run, compare to runs with `bands>=, kpoints>=, cutoff>=` and at least one strictly higher:
   - `|Δpeak_energy| < 0.05 eV`
   - `|Δpeak_intensity| / peak_intensity < 5%`
   - Peak energy must remain in the expected physical range.

6. **Select the minimum converged candidate and write exact output format.**  
   Write exactly:
   - `bands=<int>`
   - `kpoints=<int>`
   - `cutoff=<float>`
   - `peak_energy=<float>`

## Common Pitfalls
- **Using global “first local max” without physics constraints.**  
  In all runs, this produced false peaks (e.g., ~0.1 eV) and boundary artifacts (~10 eV), corrupting convergence logic.
- **Searching filesystem too broadly (`find /`) and drowning in `/proc`/`/sys` noise.**  
  Use targeted roots (`/data`, project dirs).
- **Declaring “no converged candidate” due to inconsistent peak definition.**  
  Changing detector rules across attempts flipped outcomes (e.g., selecting highest-parameter fallback). Keep one stable peak rule.
- **Assuming test failure always means wrong science result.**  
  Here, 7/8 tests passed consistently; failing test checked a different data path prefix than runtime data location. Treat as harness-path mismatch, not convergence-method failure.

## Verification Strategy
1. **Numerical sanity checks**
   - Print per-run table: params, peak energy, peak intensity.
   - Confirm selected peak is physically plausible (e.g., 3.0–3.5 eV for silicon tasks).

2. **Convergence checks**
   - Print max `ΔE` and max `%ΔI` for selected candidate versus all dominating higher-parameter runs.
   - Confirm thresholds are satisfied with the same detector used for all runs.

3. **Output contract checks**
   - Ensure output file exists and has exactly 4 lines in required `key=value` format.
   - Re-read and parse values as the verifier would.

4. **Directory existence checks (task + harness compatibility)**
   - Verify selected parameter directory exists in the actual dataset root.
   - If verifier expects a different mirror path, check that path too (or create a compatibility symlink/copy when allowed).  
   - Do **not** change scientific selection solely to satisfy a path-construction bug.

## References to Load On Demand
- Reusable Python snippet for:
  - regex parameter parsing from directory names
  - constrained first-peak detection with fallback windows
  - dominance-based convergence comparison (`>=` in all params, one strict `>`)
