---
name: extracting-sapt-basis-recommendations
description: Parse heterogeneous SAPT output files, normalize energies, filter failed runs, and emit a compliant recommendation.txt selecting the largest converged basis. Use when terminal tasks require convergence-based basis-set recommendation from mixed-format quantum chemistry logs.
---

# Extracting SAPT Basis Recommendations

## When to Use
- Process SAPT result folders containing mixed file formats (`.out`, `.log`, `.dat`, `.txt`) and mixed units (kcal/mol, kJ/mol, Hartree).
- Determine a recommended basis from multiple basis-set runs with possible failures/incomplete outputs.
- Produce strict `key=value` output files that are grader-tested.

## Minimal Reliable Workflow
1. **Enumerate candidate files and inspect all runs.**  
   Detect basis labels, total SAPT energy, four primary components (electrostatics, exchange, induction, dispersion), units, and status markers.

2. **Classify each run as valid or invalid before ranking basis size.**  
   Mark invalid if any of these appear:
   - explicit failure/incomplete markers (`ERROR`, `FAILED`, `N/A`, `incomplete`, `did not converge`)
   - missing total interaction energy
   - missing/zero primary components

3. **Normalize energies to kcal/mol.**  
   Use:
   - Hartree → kcal/mol: `value * 627.509474`
   - kJ/mol → kcal/mol: `value / 4.184`

4. **Identify the two largest successfully converged basis sets.**  
   Compute:
   `CONVERGENCE_DELTA = abs(E_largest - E_second_largest)` (kcal/mol, 2 decimals).

5. **Apply recommendation rule conservatively: choose the largest converged basis if delta ≤ threshold.**  
   In these runs, TZ and QZ converged with delta `0.05`, and 5Z failed; therefore choose **QZ**, not TZ.

6. **Write exact output format (3 lines only):**
   - `RECOMMENDED_BASIS=<canonical basis name>`
   - `CONVERGED_ENERGY=<recommended basis energy in kcal/mol, 2 decimals>`
   - `CONVERGENCE_DELTA=<abs diff of two largest converged bases, 2 decimals>`

7. **Use canonical basis string from file content, not directory alias.**  
   Prefer `aug-cc-pVQZ` over `basis_set_qz`/`basis_set_tz`.

## Common Pitfalls
- **Choosing “best balance” (smaller basis) instead of largest converged basis.**  
  Evidence: all 3 runs failed only `test_correct_recommended_basis`; 10/11 tests passed. Runs 1–2 chose `aug-cc-pVTZ`, run 3 chose `basis_set_tz`.
- **Using directory names as basis names.**  
  Evidence: run 3 failed with `basis_set_tz` instead of canonical basis string.
- **Including failed 5Z run in “largest basis” logic.**  
  5Z had dispersion failure and incomplete total (`N/A`), so exclude from converged candidates.
- **Ignoring strict formatting constraints.**  
  Output must be exactly three lines, numeric fields parseable, two decimals.

## Verification Strategy
1. **Content sanity checks**
   - Confirm recommended basis is one of valid basis strings parsed from successful files.
   - Confirm recommended basis equals largest converged basis (after excluding failed/incomplete runs).
   - Confirm `CONVERGENCE_DELTA <= 0.5`.

2. **Cross-check values**
   - Recompute delta from two largest converged totals independently.
   - Ensure `CONVERGED_ENERGY` matches recommended basis energy exactly (2 decimals).

3. **Run grader tests, then target the known failure**
   - `pytest /tests/test_outputs.py -rA`
   - If only `test_correct_recommended_basis` fails, fix basis selection/name mapping logic first (largest converged + canonical name).  

## References to Load On Demand
- Common failure markers in QC logs: `FAILED`, `ERROR`, `N/A`, `incomplete`, `did not converge`.
- Unit conversion constants:
  - `1 Eh = 627.509474 kcal/mol`
  - `1 kcal = 4.184 kJ`
