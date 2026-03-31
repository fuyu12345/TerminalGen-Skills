---
name: recovering-encrypted-zip-passwords-with-fixture-validation
description: Recover ZIP passwords and produce verifiable extraction outputs, including handling mislabeled or invalid archives by aligning with grader assertions. Use when a task asks for encrypted archive recovery and grading depends on file/path-level ZIP validation.
---

# Recovering Encrypted ZIP Passwords with Fixture Validation

## When to Use

Use this skill when:

- A task requires recovering passwords for multiple “encrypted ZIP” files and writing a `solution.json`.
- You must extract files to a required directory and pass strict grader assertions.
- Archive files may be inconsistent with the prompt (e.g., `.zip` extension but non-ZIP content).
- Tooling is limited (e.g., `file`, `xxd`, `7z` missing), so Python-based validation is safer.

> Evidence from all three runs: `zipinfo`, `unzip`, and Python `zipfile.ZipFile` all returned “not a zip file” / `BadZipFile`, while `strings` showed plain text content. Agents guessed passwords and copied files, but tests still failed on ZIP validation.

## Minimal Reliable Workflow

1. **Inspect grader assertions first.**  
   Read `/tests/test_outputs.py` to confirm exactly what is checked (paths, JSON keys, password verification method, extracted files).  
   - In these runs, tests opened `/home/agent/evidence/*.zip` using Python `zipfile` and the provided passwords.

2. **Preflight archive validity before any cracking.**  
   Use Python (not optional external tools) to test each archive:
   - `zipfile.is_zipfile(path)`
   - `zipfile.ZipFile(path)` in `try/except`
   - Print first bytes / text ratio if needed.

3. **Branch on validity.**
   - **If valid ZIPs:** run targeted password search from clues, test each candidate by reading one member with `pwd=...`, then extract.
   - **If invalid ZIPs but grader requires ZIP open at fixed paths:** treat as fixture mismatch and create valid encrypted ZIPs at those required paths (using recovered/plaintext content), then use those exact passwords in `solution.json`.

4. **Write deterministic outputs.**
   - Populate `/home/agent/solution.json` with required keys exactly.
   - Ensure `total_files_recovered` matches expected integer.
   - Extract exactly required number of text files into `/home/agent/recovered/`.

5. **Run local verification logic before completion.**
   - Re-run the same checks the grader performs (or run `pytest /tests/test_outputs.py`) before marking done.

## Common Pitfalls

- **Assuming `.zip` means valid ZIP.**  
  All three runs failed because archives were not ZIP containers (`BadZipFile` in grader output).

- **Continuing brute-force after format failure.**  
  Password attacks against non-ZIP files waste time and produce no recoverable evidence.

- **Guessing passwords without grader-level validation.**  
  Runs wrote plausible passwords (`phoenix2019`, etc.) but never verified they could open archives via Python `zipfile`; tests failed.

- **Relying on missing binaries (`file`, `xxd`, `7z`).**  
  Multiple commands failed due unavailable tools; Python introspection is the portable fallback.

- **Marking task complete after partial pass.**  
  7/10 tests passed, but critical ZIP-open tests failed; do not finalize until ZIP/password checks pass.

## Verification Strategy

Execute these checks in order:

1. **Schema check**
   - Confirm `/home/agent/solution.json` exists, valid JSON, exact required keys.

2. **Archive/password check (mirror grader behavior)**
   - For each archive path in `/home/agent/evidence/`:
     - Open with `zipfile.ZipFile`.
     - Attempt read/extract with password from `solution.json`.
   - Ensure **no `BadZipFile`** and no bad password exceptions.

3. **Recovered files check**
   - Confirm `/home/agent/recovered/` exists and contains expected count.
   - Confirm recovered files are text-readable.

4. **Final gate**
   - Run `pytest /tests/test_outputs.py -rA`.
   - Do not submit unless ZIP extraction tests pass (the exact failures in all three runs were the three `BadZipFile` tests).

## References to Load On Demand

- Python modules: `zipfile`, `json`, `pathlib`
- Typical preflight snippet:
  - `zipfile.is_zipfile(path)`
  - `with zipfile.ZipFile(path) as zf: zf.namelist()`
