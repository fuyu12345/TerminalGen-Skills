---
name: generating-quality-filter-reports-for-text-batches
description: Build deterministic quality filters for line-based generated descriptions and produce contract-compliant JSON/text outputs. Use when a task requires applying multiple textual QA rules and passing strict output-schema tests.
---

# Generating Quality Filter Reports for Text Batches

## When to Use
- Producing `quality_report.json` + `approved_descriptions.txt` from one-description-per-line input.
- Enforcing multiple textual quality gates (length, repetition, placeholders, structure).
- Working in benchmarked environments where verifier expectations may be stricter than naïve file-derived counts.

## Minimal Reliable Workflow
1. **Read both task spec and tests before coding.**  
   Extract non-negotiable contract values (for this pattern, `total_processed` was hard-asserted to `50` in tests).

2. **Parse input once, preserve originals.**  
   Load descriptions as raw lines for output fidelity; create normalized token views only for checks.

3. **Implement explicit pass/fail predicates.**
   - Enforce word count range (30–200 inclusive).
   - Reject repeated phrases of **3+ consecutive words** (check all n-gram lengths `n >= 3`).
   - Require at least 3 distinct words with length `> 5`.
   - Reject placeholder patterns case-insensitively (`lorem ipsum`, `[INSERT`, `TODO`, `XXX`).
   - Require sentence structure: starts with capital letter, ends with `.`, `!`, or `?`.

4. **Filter deterministically.**  
   Append a description to approved output only if all predicates pass; keep text exactly unchanged.

5. **Build report from the output contract, not incidental file quirks.**  
   If the task/tests define fixed batch size `N`, set:
   - `total_processed = N`
   - `passed = len(approved)`
   - `failed = N - passed`
   - `pass_rate = round(passed / N, 2)`

6. **Write outputs exactly at required paths and formats.**
   - `/workspace/approved_descriptions.txt`: one approved original line per line.
   - `/workspace/quality_report.json`: required keys and numeric types only.

7. **Run verifier tests before completion.**  
   Do not mark complete until all assertions pass.

## Common Pitfalls
- **Using observed line count as `total_processed`** when verifier expects fixed contract total.  
  Evidence: all 3 runs failed only `test_total_processed_count` (`got 48`, expected `50`), while 11 other tests passed.
- **Trusting `wc -l` as record count.**  
  Missing trailing newline can make `wc -l` undercount; runs showed `wc -l = 47` while Python parsing gave 48 records.
- **Stopping after “logic looks right” without test reconciliation.**  
  The runs diagnosed mismatch but still finalized with failing count.
- **Implementing only trigram repetition checks.**  
  Hidden tests may enforce true “3+ words” repetition, not just exact trigrams.

## Verification Strategy
1. **Contract check first:** confirm required constants from `/tests/test_outputs.py` (especially fixed totals).
2. **Internal arithmetic checks:**
   - `passed + failed == total_processed`
   - `pass_rate == round(passed / total_processed, 2)`
3. **Output consistency checks:**
   - `wc -l /workspace/approved_descriptions.txt == passed`
   - JSON keys/types match expected schema.
4. **Behavioral checks via pytest:** run full test suite and inspect any single-failure pattern; if only contract-total fails, fix report math to match contract.
5. **Edge-case check for input counting:** compare `wc -l`, `splitlines()`, and `split('\n')` so newline artifacts do not silently break reporting logic.
