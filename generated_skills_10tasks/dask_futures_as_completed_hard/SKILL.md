---
name: processing-futures-as-completed
description: Process heterogeneous async workloads in completion order using futures, while preserving full accounting and summary metrics. Use when tasks have variable runtimes, partial failures are expected, and output must prove non-blocking concurrency.
---

# Processing Futures as Completed

## When to Use

Use this skill when a pipeline currently waits for all futures (or processes in submission order) and needs to:

- Consume results as soon as each task finishes
- Avoid slow-task head-of-line blocking
- Tolerate per-item failures without stopping the batch
- Produce strict aggregate outputs (counts, timing, async-efficiency metric)

This pattern was validated across 3 independent runs with 1000 tasks and mixed latencies (0.1–3.0s), consistently passing runtime and correctness checks.

## Minimal Reliable Workflow

1. **Inspect generator and worker contracts first.**  
   Identify input schema, task count, expected failure behavior, and per-item runtime distribution.

2. **Submit all work to an executor with bounded concurrency.**  
   Use `ThreadPoolExecutor(max_workers=...)` for IO/sleep-heavy tasks.  
   Keep `future -> submission_index` metadata for completion-order analysis.

3. **Consume with `concurrent.futures.as_completed(...)`.**  
   Iterate futures in completion order (not submission order).  
   This is the core fix over `wait(..., ALL_COMPLETED)` bottlenecks.

4. **Handle result/exception per future immediately.**  
   - On success: increment `total_processed`  
   - On expected validation failure: increment `total_failed`  
   - On unexpected exception: increment `total_failed` and continue

5. **Track async-efficiency metric during completion loop.**  
   Compute deviation using completion rank vs submission index (e.g., absolute difference), then average over all tasks.  
   Positive value proves out-of-order completion.

6. **Enforce no-loss accounting guard.**  
   Assert `total_processed + total_failed == expected_total`; raise if mismatched.

7. **Emit required JSON only.**  
   Write `/workspace/results.json` with required fields and numeric types:
   - `total_processed`
   - `total_failed`
   - `processing_time_seconds`
   - `average_completion_order_deviation`

## Common Pitfalls

- **Using `wait(..., ALL_COMPLETED)` then processing results afterward.**  
  Observed root issue in the broken implementation; defeats completion-order handling and increases bottleneck risk.

- **Not mapping futures to submission metadata.**  
  Without `future -> submission_index`, you cannot compute completion-order deviation correctly.

- **Letting exceptions abort the run.**  
  Expected validation failures must be counted, not fatal; otherwise totals won’t hit expected count.

- **Missing final accounting assertion.**  
  Runs can appear “successful” while silently dropping entries unless `processed + failed == total` is checked.

- **Terminal orchestration mistakes during long runs (bench/harness context).**  
  In one trajectory, command concatenation/interruption caused `results.json` not to exist despite correct code.  
  Prevent by waiting for process completion before issuing follow-up commands.

## Verification Strategy

Run the solution end-to-end, then verify exactly what tests assert:

1. **Execution sanity**
   - `python /workspace/solution.py` exits cleanly.

2. **Artifact checks**
   - `/workspace/results.json` exists.
   - JSON parses.

3. **Schema checks**
   - Required keys exist.
   - Field types are numeric where expected.
   - No negative values.

4. **Correctness constraints**
   - `total_processed + total_failed == 1000`
   - `processing_time_seconds < 60`
   - `average_completion_order_deviation > 0`
   - Success/failure split remains reasonable (not pathological).

5. **Performance confidence**
   - If close to timeout, increase worker count moderately and re-run.
   - Reconfirm accounting and deviation remain valid after tuning.
