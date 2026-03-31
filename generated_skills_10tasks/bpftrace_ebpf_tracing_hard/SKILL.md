---
name: analyzing-syscall-latency-from-entry-return-traces
description: Parse timestamped syscall entry/return logs, pair complete events, compute per-syscall average latency, and emit the highest-latency syscall with rounded microseconds. Use when diagnosing syscall slowdowns from bpftrace-style trace files.
---

# Analyzing Syscall Latency from Entry/Return Traces

## When to Use
- Analyze pre-collected syscall traces with lines like: `timestamp_ns event_type syscall_name pid`
- Identify which syscall has the worst **average** latency
- Produce a strict two-line output file for automated grading or downstream tooling

## Minimal Reliable Workflow
1. **Parse line fields deterministically** as `ts`, `event`, `syscall`, `pid`.
2. **Pair events by `(pid, syscall)`**, not by syscall alone.
3. **Track unmatched entries with per-key depth/stack**:
   - On `entry`: push timestamp.
   - On `return`: pop timestamp only if one exists; otherwise ignore.
4. **Compute latency only for complete pairs**:
   - `lat_ns = return_ts - entry_ts`
   - Ignore negative latencies (clock/order anomalies).
5. **Aggregate by syscall type**:
   - `total_ns[syscall] += lat_ns`
   - `count[syscall] += 1`
6. **Compute average latency per syscall**:
   - `avg_ns = total_ns / count`
   - Select syscall with maximum `avg_ns`.
7. **Convert to microseconds and round to nearest integer**:
   - `avg_us = int(avg_ns/1000 + 0.5)`
8. **Write exactly two lines** to output:
   - Line 1: syscall name
   - Line 2: integer microseconds
9. **Print file content once** to confirm format before finishing.

## Common Pitfalls
- **Overwriting a single start timestamp per key** instead of using stack/depth.  
  - Evidence: one successful run used overwrite logic; it passed this dataset but is less robust for overlapping same `(pid, syscall)` events.  
  - Prevention: use stack/depth (used in 2/3 successful runs) to minimize assumptions.
- **Including unpaired events** (entry without return or return without entry).  
  - Prevention: only accumulate when a valid pending entry exists.
- **Wrong unit conversion** (ns vs µs) or no rounding.  
  - Prevention: divide by 1000 and round with `int(x + 0.5)`.
- **Output formatting drift** (extra lines/text/decimals).  
  - Prevention: write only two lines and ensure line 2 is an integer string.

## Verification Strategy
Use checks aligned with observed passing criteria (all three runs passed the same 6 assertions):

1. **File existence**: output file exists at required path.
2. **Non-empty content**: file has data.
3. **Exact structure**: exactly two lines.
4. **Semantic validity**:
   - Line 1 matches a syscall name from trace data.
   - Line 2 is an integer.
5. **Computation correctness**:
   - Recompute independently (e.g., quick secondary awk/python check) and confirm same syscall + latency.
6. **Terminal sanity check**:
   - `cat` output should show only:
     - syscall name
     - integer microseconds

## References to Load On Demand
- `awk` associative arrays with composite keys (`pid SUBSEP syscall`)
- Stack/depth pattern for matching nested entry/return events
- Integer rounding in awk for nearest microsecond conversion
