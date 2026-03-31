---
name: validating-uge-slot-allocations
description: Validate Univa/Grid Engine host and queue slot consistency, compute invalid hosts and overcommitted queues, and emit strict report files. Use when auditing migrated scheduler configs with key=value host/queue files and exact output-format requirements.
---

# Validating UGE Slot Allocations

## When to Use

Use this skill when:

- Host and queue configs are stored as flat `key=value` files (for example `hosts/*`, `queues/*`).
- Required checks include:
  - host slot divisibility constraints (for example `slots % 4 == 0`)
  - total host slot capacity
  - queue slot requests exceeding per-host capacity
- Output must match an exact line-by-line format for automated grading or CI checks.

---

## Minimal Reliable Workflow

1. **Inspect file shapes before computing anything.**  
   Confirm keys actually exist and are consistently named (`hostname`, `qname`, `slots`).

2. **Parse hosts first and compute three values in one pass logic:**
   - `invalid_hosts` list where `slots % divisor != 0`
   - `total_slots` sum across hosts
   - `max_host_slots` maximum host slot count

3. **Parse queues second using `max_host_slots`:**
   - Mark queue as overcommitted if `queue_slots > max_host_slots`
   - Build comma-separated `overcommitted_queues` list

4. **Normalize empty lists to `none`.**  
   Do this for both `invalid_hosts` and `overcommitted_queues`.

5. **Write report with exact keys/order/newlines.**  
   Always emit:
   - `invalid_hosts=...`
   - `total_slots=...`
   - `overcommitted_queues=...`

6. **Immediately `cat` the output file** to confirm exact formatting and computed values.

### Portable implementation pattern

Prefer POSIX-friendly shell loops or awk logic that does **not** depend on non-portable features:

```bash
invalid_hosts=""
total_slots=0
max_host_slots=0

for f in hosts/*; do
  h=$(grep '^hostname=' "$f" | cut -d= -f2-)
  s=$(grep '^slots=' "$f" | cut -d= -f2-)
  [ -z "$s" ] && s=0
  total_slots=$((total_slots + s))
  [ $((s % 4)) -ne 0 ] && invalid_hosts="${invalid_hosts:+$invalid_hosts,}$h"
  [ "$s" -gt "$max_host_slots" ] && max_host_slots="$s"
done
[ -z "$invalid_hosts" ] && invalid_hosts="none"

overcommitted_queues=""
for f in queues/*; do
  q=$(grep '^qname=' "$f" | cut -d= -f2-)
  s=$(grep '^slots=' "$f" | cut -d= -f2-)
  [ -z "$s" ] && s=0
  [ "$s" -gt "$max_host_slots" ] && overcommitted_queues="${overcommitted_queues:+$overcommitted_queues,}$q"
done
[ -z "$overcommitted_queues" ] && overcommitted_queues="none"

printf 'invalid_hosts=%s\ntotal_slots=%s\novercommitted_queues=%s\n' \
  "$invalid_hosts" "$total_slots" "$overcommitted_queues" > /tmp/config_report.txt
```

---

## Common Pitfalls

- **Using `awk ENDFILE` in environments where awk doesn’t support it.**  
  Observed across runs: this produced silently wrong results like `invalid_hosts=none` and `total_slots=0` despite valid input data.  
  **Prevention:** use shell loops or awk patterns that accumulate on key matches without `ENDFILE`.

- **Trusting computed output without cross-checking against visible file contents.**  
  In one run, incorrect output was caught only because the agent compared values to inspected configs.  
  **Prevention:** do a quick mental/command-line sanity check (sum slots, identify obvious non-multiples, compare queue max).

- **Formatting drift in final report.**  
  The grader expects exact 3-line order and key names.  
  **Prevention:** generate via single `printf` with explicit newline layout and verify with `cat`.

---

## Verification Strategy

Perform verification at two levels:

1. **Data correctness checks**
   - Recompute quickly:
     - `total_slots` equals sum of host `slots`
     - each `invalid_host` truly has `slots % 4 != 0`
     - each `overcommitted_queue` has `queue_slots > max_host_slots`
   - Confirm empty sets are rendered as `none` (not blank).

2. **Output contract checks**
   - File exists at required path.
   - File is non-empty.
   - Exactly 3 lines, exact key names, exact order.
   - Line formats are `key=value` with comma-separated lists where applicable.

This directly mirrors the observed test expectations (`exists`, `not empty`, `three lines`, `line format`, `value correctness`) and catches the same failure mode seen in trajectory experiments.
