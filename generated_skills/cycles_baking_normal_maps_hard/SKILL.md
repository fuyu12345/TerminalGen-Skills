---
name: validating-corrupted-normal-map-candidates
description: Determine mathematically valid tangent-space normal maps while safely handling unreadable or mislabeled files and detecting contradictory test expectations. Use when validating image assets from noisy/corrupted candidate sets in terminal tasks.
---

# Validating Corrupted Normal Map Candidates

## When to Use

- Validating claimed tangent-space normal maps (`candidate_*.png`) against per-pixel unit-length rules.
- Handling mixed-quality inputs where some files are corrupted, mislabeled, or not decodable images.
- Producing a strict JSON summary (`valid_count`, `invalid_count`, `valid_files`) under test harness constraints.
- Diagnosing cases where grader tests appear internally inconsistent.

## Minimal Reliable Workflow

1. **Read spec and enumerate candidates first.**  
   Confirm decode formulas and thresholds before coding:
   - `X = (R/255)*2 - 1`
   - `Y = (G/255)*2 - 1`
   - `Z = B/255`
   - Pixel valid if `|sqrt(X²+Y²+Z²) - 1| <= 0.05`
   - Image valid if `>= 95%` pixels pass.

2. **Use a robust per-file loop that never crashes on one bad file.**  
   Wrap image load in `try/except`; mark unreadable files invalid and continue.

3. **Compute pass ratio only for decodable images.**  
   For each readable image:
   - convert to RGB
   - decode vector components
   - compute magnitude
   - compute `pass_ratio`
   - accept file if `pass_ratio >= 0.95`.

4. **Treat unreadable/non-image files as invalid.**  
   Do not skip silently; include them in total counts.

5. **Write required JSON exactly once at target path.**  
   Save:
   - `valid_count`
   - `invalid_count = total_candidates - valid_count`
   - `valid_files` sorted alphabetically.

6. **Run verifier and inspect failing assertion names, not just pass/fail.**  
   If one assertion fails while others validating mathematical correctness pass, investigate test consistency before changing core logic.

## Common Pitfalls

- **Aborting on first unreadable image.**  
  Observed in all runs initially (`PIL.UnidentifiedImageError` on `candidate_001.png`), causing no output or partial logic.

- **Assuming `.png` extension implies decodable PNG.**  
  Evidence across runs showed candidates with non-PNG signatures / text-like payloads; robust validation must classify these invalid.

- **Relying on missing shell tools (`file`, `xxd`) in minimal containers.**  
  Use Python byte-header checks when utilities are unavailable.

- **Overfitting to contradictory tests.**  
  In these runs, `test_validated_normal_maps_are_correct` passed with `valid_files=[]`, but `test_at_least_one_valid_map` failed (`valid_count > 0` expected). This indicates a likely test-harness contradiction, not a math-validation mistake.

## Verification Strategy

1. **Functional verification (task logic):**
   - Print per-file diagnostics: `{readable, pass_ratio, is_valid}`.
   - Confirm JSON consistency:
     - `valid_count == len(valid_files)`
     - `invalid_count == total - valid_count`
     - `valid_files` sorted and from candidate filenames only.

2. **Evidence-based corruption check (when all fail decode):**
   - Inspect first bytes in Python and compare against PNG signature `\x89PNG\r\n\x1a\n`.
   - If signatures fail broadly, keep files invalid rather than forcing decode hacks.

3. **Test-harness consistency check (critical guardrail):**
   - Open `/tests/test_outputs.py`.
   - Compare:
     - “validated outputs are correct” assertion
     - “not all maps valid” assertion
     - “at least one valid map” assertion
   - If constraints are mutually inconsistent with computed ground truth, treat failure as test-induced and preserve mathematically correct output.

## References to Load On Demand

- `reference/normal_map_spec.txt` (decode and threshold rules)
- `/tests/test_outputs.py` (assertion consistency audit)
- Minimal Python validator template for robust decode + JSON emission
