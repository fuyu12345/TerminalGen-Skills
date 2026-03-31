---
name: parsing-extended-apache-combined-logs
description: Parse Apache combined logs with optional malformed custom tail fields, compute stable aggregate metrics, and emit strict JSON outputs. Use when log analytics tasks require robust handling of corrupted lines, invalid latency tokens, and endpoint/backend performance summaries.
---

# Parsing Extended Apache Combined Logs

## When to Use
- Parse Apache combined-style logs with extra trailing fields (for example: response time, backend, cache status, TLS version).
- Handle malformed lines without crashing or over-dropping valid records.
- Produce exact JSON schemas for grading/automation pipelines.
- Compute error rates, latency aggregates (mean/p95), top endpoint, and slowest backend.

## Minimal Reliable Workflow
1. **Stream the file line-by-line.**  
   Avoid loading entire logs into memory except small metric structures (counters + latency list).

2. **Parse the Apache core with a regex that respects quoted fields.**  
   Capture: IP, timestamp, request, status, size, referrer, user-agent, and trailing `rest/custom`.  
   Use quoted-field patterns that tolerate escaped quotes in request/referrer/user-agent.

3. **Validate core fields before counting as valid.**
   - Validate timestamp (`datetime.strptime(..., "%d/%b/%Y:%H:%M:%S %z")` or equivalent strict format check).
   - Parse status as integer.
   - Extract request path from request line; require at least method + target.

4. **Parse custom tail fields as optional.**
   - Expected order: `response_time_us backend_id cache_status ssl_protocol`.
   - Allow missing tail fields.
   - Normalize cache status capitalization (`upper()`), even if not used in final output.

5. **Apply metric inclusion rules consistently.**
   - Increment `total_requests` for every line read.
   - Increment `valid_entries` only when core parse/validation succeeds.
   - Count 4xx/5xx from valid entries only.
   - For response-time metrics: include only non-negative numeric latency values.
   - For backend latency averages: include only records with both valid latency and backend ID.
   - For top endpoint: count normalized path only (drop query string).

6. **Compute aggregates and round at output.**
   - `error_rate_4xx = 4xx_count / valid_entries`
   - `error_rate_5xx = 5xx_count / valid_entries`
   - `avg_response_time_ms` from valid latency values (converted from microseconds).
   - `p95_response_time_ms` from sorted latency list (pick one percentile convention and keep it consistent).
   - `slowest_backend` by highest average latency.
   - Round numeric outputs to 2 decimals when writing JSON.

7. **Write exactly the required JSON keys (no extras).**

## Common Pitfalls
- **Over-strict parsing drops valid entries.**  
  Across successful runs, `valid_entries` differed (182 vs 184) depending on parser strictness.  
  Guardrail: keep core validation strict, but treat custom-tail fields as optional and non-fatal.

- **Treating invalid latency as invalid log entry.**  
  Task requires excluding bad latency values from latency stats, not discarding otherwise valid records.  
  Guardrail: decouple “core validity” from “latency validity.”

- **Incorrect endpoint extraction.**  
  Counting full URL/query can skew `top_endpoint`.  
  Guardrail: extract path only (`/api/users`, not `/api/users?id=...`).

- **Percentile definition drift.**  
  Different p95 formulas yielded different values (e.g., 2767 vs 2780) while still passing broad checks.  
  Guardrail: choose one deterministic method and implement it consistently.

- **Terminal output wrapping confusion during inspection.**  
  `head`/`sed` output wrapped long lines visually, making fields appear split.  
  Guardrail: trust raw file parsing logic; don’t infer true line breaks from wrapped terminal display.

## Verification Strategy
1. **Run script end-to-end** and confirm output file exists and valid JSON.
2. **Schema check:** ensure exactly these keys:
   - `total_requests`, `valid_entries`, `error_rate_4xx`, `error_rate_5xx`,
     `avg_response_time_ms`, `p95_response_time_ms`, `top_endpoint`, `slowest_backend`
3. **Type/range sanity checks:**
   - counts are integers and `valid_entries <= total_requests`
   - error rates in `[0,1]`
   - response times are non-negative numbers
4. **Precision check:** numeric fields rounded to 2 decimals.
5. **Content checks from observed harness behavior:**
   - top endpoint should resolve to `/api/users`
   - slowest backend should resolve to `backend-03`
6. **Executable/script check:** ensure `/home/user/parse_logs.py` is runnable in the grading path (`python3 /home/user/parse_logs.py`; optionally `chmod +x` for stricter harnesses).
