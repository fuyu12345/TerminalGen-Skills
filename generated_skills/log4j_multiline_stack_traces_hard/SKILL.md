```markdown
---
name: parsing-log4j-multiline-stack-traces
description: Extract multiline Log4j stack traces, aggregate root exception statistics, and emit constrained JSON output. Use when logs contain Java stack traces with mixed formats, nested causes, and possible thread interleaving.
---

# Parsing Log4j Multiline Stack Traces

## When to Use
- Parsing Java/Log4j-style logs where stack traces span multiple lines.
- Producing summary JSON with:
  - total exception count,
  - top exception types,
  - per-type service coverage,
  - most common failure frame.
- Handling `Caused by:`, `Suppressed:`, `... N more`, and mixed non-stack log lines.
- Handling multiple files/services and potential interleaving by thread.

## Minimal Reliable Workflow
1. **Profile log shape before coding.**  
   Run `ls`, `wc -l`, and a targeted `grep` for exception-like lines to estimate expected magnitude and formats.
   - Evidence: one run found `552` total lines and many exception declarations; this immediately exposed an undercounting parser later.

2. **Implement robust entry-start detection for multiple timestamp/header styles.**  
   Support bracketed timestamps (e.g. `[2024-... ] [thread] LEVEL ...`) and common non-bracketed variants.

3. **Track active traces by thread context.**  
   Maintain `active_by_thread[thread_id]` and close/finalize on the next non-continuation log entry for that same thread.

4. **Start a trace only on a root exception declaration.**  
   Detect fully qualified throwable class names ending with `Exception|Error|Throwable`, and **exclude** lines beginning with `Caused by:` / `Suppressed:` from root classification.

5. **Append only valid continuation lines.**  
   Accept:
   - `at ...`
   - `Caused by: ...`
   - `Suppressed: ...`
   - `... N more`  
   Stop trace capture at next true log entry or incompatible noise line.

6. **Aggregate deterministically.**
   - `count` by root exception type.
   - `services` as sorted unique list.
   - `top_failure_location` as most frequent `at ...` frame (excluding declaration line).
   - `exception_summary` limited to top 5 by descending count (use deterministic tie-break, e.g., exception name).

7. **Write exact required JSON schema to target path** (`/tmp/stack_trace_analysis.json` in this task) and pretty-print for quick human inspection.

## Common Pitfalls
- **Missing actual header format -> severe undercount.**  
  Observed in one run: parser initially returned `total_exceptions: 3` due to weak log-start recognition; corrected parser produced `37`.
- **Treating nested exceptions as roots.**  
  If `Caused by:` is counted as root, counts and top types become wrong.
- **Not finalizing traces at proper boundaries.**  
  Over-capture or leakage into normal log lines corrupts frame frequencies.
- **Weak continuation-thread association.**  
  Continuation lines often lack thread token; blindly attaching to “latest active trace” can mis-assign in interleaved logs.
- **Nondeterministic ordering / unsorted services.**  
  Causes flaky outputs and test failures on sorted expectations.

## Verification Strategy
1. **Schema and constraints check (machine):**
   - File exists and valid JSON.
   - Required fields present.
   - `exception_summary` length `<= 5`.
   - Each item has `exception_type`, `count`, `services`, `top_failure_location`.
   - `exception_type` looks fully qualified.
   - `services` sorted.
   - Counts positive.
   - Summary sorted by descending `count`.
   - `total_exceptions == sum(item.count)`.

2. **Semantic sanity check (human + shell):**
   - Compare parser scale against raw hints:
     - `wc -l /var/logs/app/*.log`
     - `grep -nE 'Exception|Error|Throwable|Caused by:|Suppressed:' ...`
   - If parser totals are implausibly low (as seen with `3` vs many declarations), fix parser before finalizing.

3. **Run authoritative tests last:**
   - `pytest /tests/test_outputs.py -rA`

4. **Interpret failures correctly:**
   - In observed runs, issues came from parser logic (not test harness).  
     Treat suspiciously “passing but implausible” outputs as parser-quality defects and re-validate.

## References to Load On Demand
- Regex patterns for:
  - Log entry headers (bracketed and non-bracketed timestamps),
  - Root exception declarations,
  - Continuation lines (`at`, `Caused by`, `Suppressed`, `... N more`).
- Deterministic aggregation patterns with `Counter` + stable sort keys.
```
