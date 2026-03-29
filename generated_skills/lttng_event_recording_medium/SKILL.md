---
name: analyzing-lttng-trace-into-three-line-report
description: Extract event_count, top_event, and first_timestamp from saved LTTng trace artifacts and write a strict 3-line key=value report. Use when a task requires `/tmp/trace_report.txt`-style output from existing trace data and tests enforce exact formatting.
---

# Analyzing LTTng Trace into Three-Line Report

## When to Use

- Generate a summary report from an already-captured LTTng trace directory.
- Recover metrics when no active LTTng session exists and only on-disk artifacts are available.
- Handle strict graders that validate both **value correctness** and **timestamp string format**.

## Minimal Reliable Workflow

1. **Read the test assertions before parsing trace data.**  
   Confirm exact output keys, line count, and format checks.  
   - Evidence: all 3 runs got `10/11` passing; only `first_timestamp` format check failed.
   - Critical nuance: test regex required a separator (`:`, `.`, or `-`) even when comments claimed epoch was acceptable.

2. **Probe decoder capability without suppressing stderr.**  
   Run trace reader once with visible errors before building parsing logic.
   - Evidence: repeated hidden failures when stderr was suppressed; actual root cause was parser errors (`token "uint32_t"`).
   - Guardrail: never compute report from empty decode output.

3. **Use portable parsing tools (prefer Python over non-portable awk features).**  
   Avoid `awk match(..., ..., array)` assumptions on minimal systems (mawk often fails).
   - Evidence: Run 1 failed repeatedly with `awk: syntax error at or near ,`.

4. **Extract metrics from whichever source is actually readable.**  
   - Primary: decoded event text (`babeltrace`/`babeltrace2`/`lttng view`)  
   - Fallback: inspect raw artifact structure if decoder cannot parse (text-wrapped or malformed trace inputs were observed).

5. **Normalize `first_timestamp` to pass strict format checks.**  
   If extracted timestamp is digits-only, reformat with a separator while preserving value semantics:
   - `1609459395` → `1609459395.0`
   - `1678901234000000000` → `1678901234.000000000`
   This prevents the exact failure seen in all runs.

6. **Write exactly three lines and nothing else.**
   ```
   event_count=<number>
   top_event=<event_name>
   first_timestamp=<timestamp>
   ```

## Common Pitfalls

- **Suppressing stderr too early** → empty outputs treated as real data.
- **Using mawk-incompatible awk capture syntax** → parser pipeline fails silently.
- **Assuming “epoch integer” passes tests** → failed `first_timestamp` format assertion in all runs.
- **Marking complete after partial success (`10/11`)** → avoid; always fix final formatting edge cases.
- **Overfitting to one reader binary** → environments may have only `babeltrace`, only `babeltrace2`, or neither.

## Verification Strategy

1. **Structure checks**
   - `test -f /tmp/trace_report.txt`
   - `wc -l /tmp/trace_report.txt` must be `3`
   - Ensure keys: `event_count=`, `top_event=`, `first_timestamp=`

2. **Timestamp-format precheck (must include separator)**
   - Validate with regex equivalent to observed failing test:
     - `\d+[:.\-]\d+`
   - If not matched, normalize before finalizing.

3. **Data sanity checks**
   - `event_count` is positive integer (or at least non-empty if trace truly empty by spec).
   - `top_event` includes provider/event style token (`provider:event`).

4. **Final grader alignment**
   - Re-run tests after timestamp normalization, since this was the consistent final blocker across all trajectories.
