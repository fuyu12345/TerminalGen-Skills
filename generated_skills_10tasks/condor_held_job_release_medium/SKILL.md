---
name: releasing-held-batch-jobs-from-csv
description: Analyze a job-queue CSV and generate a numerically sorted release list of safely releasable held jobs using hold-reason and resource-limit filters. Use when triaging held batch/HTCondor-style jobs from structured queue exports.
---

# Releasing Held Batch Jobs from CSV

## When to Use

Use this skill when a task requires creating a `release_list.txt` (or equivalent) from a queue CSV by applying **all** of the following:

- job state filter (e.g., only `held`)
- allowlisted hold reasons (resource-related only)
- resource limit checks (memory/disk/CPU thresholds)
- strict output formatting (ID-only, one per line, sorted numerically)

This pattern was validated across three independent successful runs with identical test expectations.

## Minimal Reliable Workflow

1. **Read queue data with schema-aware parsing.**  
   Use `csv.DictReader` and parse fields explicitly (`job_id`, `status`, `hold_reason`, resource columns).

2. **Define release policy as constants.**  
   Keep allowlisted hold reasons and max resource limits in named constants/sets.

3. **Filter in a strict gate sequence.**  
   Keep only rows that satisfy all conditions:
   - status is `held`
   - hold reason is in resource allowlist
   - resource requests are `<=` configured limits

4. **Parse IDs numerically and sort numerically.**  
   Convert `job_id` to `int`, collect, then `sort()`.

5. **Write output as plain ID lines.**  
   Write exactly one job ID per line, no headers, no commentary.

6. **Always create output file.**  
   Open output in write mode even if no jobs qualify so an empty file exists.

7. **Execute script and inspect output immediately.**  
   Run script, then `cat` the output to confirm expected IDs and format.

## Common Pitfalls

- **Including non-held jobs** (e.g., `running` rows).  
  Tests explicitly reject this class of mistake.

- **Including non-resource hold reasons** (e.g., missing input/network issues).  
  Only allowlisted resource reasons should pass.

- **Ignoring resource caps after reason filter.**  
  Resource-related reason alone is not enough; jobs exceeding limits must remain held.

- **Sorting IDs lexicographically instead of numerically.**  
  Treat IDs as integers before sorting to avoid ordering bugs.

- **Writing wrong file format.**  
  Avoid headers, commas, JSON, or extra text. Output must be ID-only, one per line.

- **Failing to create output when result set is empty.**  
  The empty-file case is usually asserted.

## Verification Strategy

Perform verification in two layers:

1. **Functional spot-check**
   - Run the script.
   - Confirm output file exists.
   - Confirm each listed ID satisfies all gates (status, reason, limits).
   - Confirm excluded examples fail at least one gate.

2. **Format and ordering checks (mapped to observed grader behavior)**
   - Ensure file is present.
   - Ensure IDs are numerically sorted.
   - Ensure no running/non-resource/exceeds-limit jobs appear.
   - Ensure one-ID-per-line formatting.

If a pytest harness is provided, run it after manual checks; in the observed runs, passing conditions aligned with assertions for:
- file existence,
- correct membership,
- numeric sort,
- exclusion of invalid categories,
- output format.
