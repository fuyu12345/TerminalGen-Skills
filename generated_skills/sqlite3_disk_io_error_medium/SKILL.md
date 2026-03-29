---
name: recovering-sqlite-dump-to-clean-json
description: Recover records from a corrupted SQLite database by importing a SQL dump with error tolerance, filtering invalid rows, and exporting strict JSON. Use when source `.db` files fail (e.g., disk I/O errors) but a dump file is available and output quality constraints are tested.
---

# Recovering SQLite Dump to Clean JSON

## When to Use

- Recover data when the original SQLite file is unreadable/corrupt but a `.sql` dump exists.
- Produce a cleaned JSON artifact with strict field/quality rules (required keys, no null/empty values, valid email shape, positive numeric amounts).
- Handle partially malformed dumps where some statements or row values may be invalid.

## Minimal Reliable Workflow

1. **Inspect inputs and constraints first.**
   - Confirm dump file exists.
   - Read test expectations (or task criteria) before coding output shape.

2. **Create a fresh recovery database and import dump with statement-level fault tolerance.**
   - Prefer:
     - `sqlite3 recovered.db` + `.bail off` + `.read dump.sql`, **or**
     - Python loop executing statements with `try/except sqlite3.Error` and continue.
   - This preserves valid statements even when some dump lines are malformed.

3. **Query only valid rows using explicit filters.**
   - Enforce at minimum:
     - `order_id IS NOT NULL`
     - `customer_email IS NOT NULL AND TRIM(customer_email) <> ''`
     - email contains `'@'` (e.g., `INSTR(customer_email,'@') > 0`)
     - `total_amount IS NOT NULL`
     - numeric positive amount (`CAST(total_amount AS REAL) > 0` or safe Python conversion)

4. **Normalize types during export.**
   - Convert to stable JSON primitives:
     - `order_id -> int`
     - `customer_email -> str`
     - `total_amount -> float`
   - Emit only required keys (no extras).

5. **Write output JSON and (if required) recovered DB.**
   - Save exact expected path (e.g., `/workspace/recovered_orders.json`).

6. **Run a strict post-write validation script before finalizing.**
   - Assert top-level is array.
   - Assert every object has exactly required keys.
   - Assert no null/empty values, emails contain `@`, amounts are numeric and `> 0`.
   - Confirm at least one recovered record exists if tests require non-empty output.

## Common Pitfalls

- **Assuming SQL-level filter guarantees Python-safe conversion.**  
  Evidence: one run failed with `ValueError: could not convert string to float: ''` while building JSON.  
  Prevent by either:
  - adding SQL guards robustly (`total_amount` non-empty and castable), and/or
  - wrapping Python conversion in `try/except` and skipping bad rows.

- **Letting one malformed statement abort the whole import.**  
  Prevent by using `.bail off` or per-statement `try/except` execution.

- **Writing wrong JSON schema (extra fields like `order_date`).**  
  Tests required exactly `order_id`, `customer_email`, `total_amount`. Enforce key set explicitly.

- **Skipping final artifact checks after script errors.**  
  In the failed intermediate attempt, output files were never created. Always verify file existence after processing.

## Verification Strategy

Run validations that mirror the grader’s assertions:

1. **File exists** at required path.
2. **Valid JSON** and top-level `list`.
3. **Schema exactness**: each row keys == `{'order_id','customer_email','total_amount'}`.
4. **Data quality**:
   - no null/empty fields,
   - email contains `@`,
   - `total_amount` numeric and positive,
   - `order_id` valid integer-like value.
5. **Recovery success**: ensure non-zero recovered rows when expected.

A compact Python verifier (post-export) is the most reliable final gate and caught/avoided the observed conversion failure mode.

## References to Load On Demand

- SQLite CLI import controls: `.bail`, `.read`
- SQLite text/validation helpers: `TRIM`, `INSTR`, `CAST`
- Python `sqlite3` exception handling for resilient statement execution
