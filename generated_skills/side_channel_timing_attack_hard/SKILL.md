---
name: recovering-passwords-from-timing-measurements
description: Recover fixed-length secrets from noisy early-exit comparison timings by prefix-wise aggregation and robust ranking. Use when a dataset contains `(attempt, time)` pairs and longer correct prefixes produce higher latency.
---

# Recovering Passwords from Timing Measurements

## When to Use
- Analyze a CSV/log of password attempts with measured response times.
- Exploit a prefix timing leak (comparison exits on first mismatch).
- Recover a fixed-length lowercase secret (or similarly constrained alphabet) from noisy repeated measurements.
- Produce an output file with strict formatting requirements (exact length/charset).

## Minimal Reliable Workflow
1. **Validate input schema and constraints.**
   - Load data and require expected columns (e.g., `password`, `time_us`).
   - Keep only rows matching the known format (e.g., 8 lowercase letters).
   - Coerce timing to numeric and drop invalid rows.

2. **Recover the secret greedily by prefix.**
   - Initialize `prefix = ""`.
   - For each position `i`:
     - Filter rows where attempt starts with current `prefix`.
     - Group timings by candidate character at position `i`.
     - Score each candidate with a robust central tendency (trimmed mean, median+mean blend, or mean if separation is strong).
     - Prefer candidates with larger sample counts when scores are close.
     - Append best character to `prefix`.

3. **Write output in strict format.**
   - Write recovered secret to `/tmp/solution.txt`.
   - Prefer writing exactly the token required by the grader (often exactly 8 chars; newline handling may vary by harness).

4. **Sanity-check against timing signal.**
   - Print per-position top candidates with score and `n` to ensure clear separation.
   - Confirm later positions still have enough support or at least strong score gaps.

> Evidence across all 3 runs: this prefix-greedy aggregation consistently recovered the correct secret; robust scoring (trimmed mean / median+mean) and simple mean both worked because timing separation was monotonic by correct-prefix depth.

## Common Pitfalls
- **Using raw single measurements instead of aggregation.**  
  Noise exists; aggregate repeated attempts per candidate/prefix.
- **Ignoring sample-size collapse at later positions.**  
  In observed runs, support dropped sharply (large at early chars, tiny near end). Add count-aware tie-breaking or mild small-sample penalty.
- **Failing to enforce input validity.**  
  Nonconforming passwords/non-numeric times can skew ranking; filter first.
- **Stopping after finding a plausible full string without format checks.**  
  Output formatting can fail otherwise-valid recovery.
- **Overfitting to one statistic.**  
  Mean worked here, but robust estimators are safer when outliers are heavier.

## Verification Strategy
Run checks aligned to typical grader assertions (`exists`, `not empty`, `length`, `charset`, `correctness`, `max timing`):

1. **File/format checks**
   - `test -s /tmp/solution.txt`
   - Validate content matches lowercase length constraint (e.g., `^[a-z]{8}$` after optional trailing newline handling).
   - Confirm byte-length expectations if strict (`wc -c`).

2. **Signal-consistency checks**
   - Recompute grouped timing stats from source data.
   - Verify recovered string is top-ranked by aggregate timing among full attempts (or by iterative prefix ranking at each step).
   - Print top-5 per position with `(score, n)` to confirm non-accidental picks.

3. **Final quick regression script**
   - One-shot script should: load → filter → recover → write → self-check invariants.
   - Avoid manual edits to solution file after script output.

## References to Load On Demand
- Robust ranking options for noisy timings:
  - Trimmed mean
  - Median/mean blended score
  - Count-penalized score for low-`n` buckets
- Reusable Python skeleton for prefix timing attacks on fixed alphabets.
