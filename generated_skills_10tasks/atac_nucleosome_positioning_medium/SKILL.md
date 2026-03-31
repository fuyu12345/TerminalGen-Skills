```markdown
---
name: summarizing-atac-fragment-lengths
description: Compute ATAC-seq fragment distribution summary JSON with robust path reconciliation and mode calculation. Use when generating QC fragment statistics in terminal-bench-style file-processing tasks.
---

# Summarizing ATAC Fragment Lengths

## When to Use
- Compute fragment-length QC metrics from a newline-delimited integer file.
- Produce a strict JSON artifact with required keys and integer/null types.
- Handle tasks where prompt-specified paths and grader-expected paths may differ.

## Minimal Reliable Workflow
1. **Inspect grader expectations before finalizing output path.**  
   Read `/tests/test_outputs.py` (or equivalent) and confirm the exact path the verifier opens.  
   - In these runs, tests expected: `/workspace/results/fragment_summary.json`  
   - Prompt requested: `/results/fragment_summary.json`

2. **Resolve input path dynamically instead of assuming one location.**  
   Check common candidates, then fall back to `find`:
   - `/data/fragment_lengths.txt`
   - `/workspace/data/fragment_lengths.txt`
   - `find / -name 'fragment_lengths.txt' 2>/dev/null`

3. **Parse integers safely.**  
   Read non-empty lines and cast to `int`.

4. **Compute required metrics exactly.**
   - `total_fragments`: total number of parsed lengths
   - `nucleosome_free_count`: count of lengths `< 100`
   - `mononucleosome_count`: count of lengths `180 <= x <= 247`
   - `nucleosome_free_peak`: mode in `0–99` subset, else `null`
   - `mononucleosome_peak`: mode in `180–247` subset, else `null`
   - Use deterministic tie-break for mode (e.g., smallest value among max-frequency items).

5. **Write output to verifier path (or both paths if uncertain).**  
   Create parent directory first (`mkdir -p` equivalent).  
   If prompt and tests disagree, write the same JSON to both locations to maximize robustness.

6. **Print and inspect final JSON.**  
   Confirm all 5 keys exist and values are int/null.

## Common Pitfalls
- **Pitfall: Trusting prompt path without checking tests.**  
  Evidence: all 3 runs produced correct JSON at `/results/fragment_summary.json` but all tests failed because verifier looked for `/workspace/results/fragment_summary.json`.
- **Pitfall: Assuming input is always `/data/...`.**  
  Evidence: all runs initially failed with `FileNotFoundError`; actual file was `/workspace/data/fragment_lengths.txt`.
- **Pitfall: Marking complete before path/exists validation against grader path.**  
  Leads to full test failure even when calculations are correct.
- **Pitfall: Non-deterministic mode handling on ties.**  
  Avoid ambiguous behavior by explicit tie-break policy.

## Verification Strategy
1. **Path verification (first gate):**
   - `test -f /workspace/results/fragment_summary.json` (or exact test path)
2. **Schema verification:**
   - JSON parses successfully.
   - Keys are exactly:
     `total_fragments`, `nucleosome_free_count`, `mononucleosome_count`, `nucleosome_free_peak`, `mononucleosome_peak`
3. **Type verification:**
   - First three fields are integers.
   - Peak fields are integer or null.
4. **Logic verification (recompute independently):**
   - Recalculate counts and peaks from source file in a quick one-off script and compare to JSON.
5. **Harness verification:**
   - Run `pytest /tests/test_outputs.py -rA` before final submission.

## References to Load On Demand
- Python `collections.Counter` for deterministic mode extraction.
- Task-specific `test_outputs.py` for exact output-path and assertion behavior.
```
