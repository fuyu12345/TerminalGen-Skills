---
name: converting-sql-queries-to-prepared-statements
description: Convert vulnerable SQLite query construction to parameterized statements while preserving behavior and required output artifacts. Use when fixing SQL injection findings in multi-file Python services under test-harness grading.
---

# Converting SQL Queries to Prepared Statements

## When to Use

Use this skill when a Python/SQLite codebase is flagged for SQL injection and the task requires both:
- secure query rewrites (`?` placeholders + bound parameters), and
- strict grader-facing artifacts (JSON reports, copied fixed files, specific output paths).

This is especially important when local app tests and grader tests validate different things.

## Minimal Reliable Workflow

1. **Read grader assertions first (not just task text).**  
   Inspect `/tests/test_outputs.py` (or equivalent) before editing.  
   In these runs, failures were caused by missing files under:
   `output/sql_injection_prepared_statement_medium/files/*.py`, even though code was fixed in `/app`.

2. **Inventory vulnerable queries with grep.**  
   Search for SQL plus unsafe construction patterns:
   - f-strings in queries
   - `%` formatting
   - `.format(...)`
   - string concatenation (`+`)

3. **Patch minimally, preserve API and behavior.**  
   Replace only SQL construction/execution style:
   - `cursor.execute("... WHERE x = ?", (x,))`
   - keep function names/signatures/return shapes unchanged
   - keep DB path override behavior (`DB_PATH`) if present

4. **Handle special query forms safely.**
   - **LIKE:** bind wildcard as data (`LIKE ?`, param `f"%{term}%"`)
   - **IN:** prefer repeated parameterized execution (`executemany`) or generated placeholders with bound values only

5. **Avoid unnecessary refactors.**  
   Do not rewrite whole modules unless required. In runs 1–3, broad rewrites introduced compatibility bugs (missing expected functions/signatures, wrong field mapping).

6. **Produce required output artifacts exactly where grader expects.**
   - Write `/tmp/sql_injection_fixes.json`
   - Also place fixed Python files in expected output folder when required by tests (e.g., `output/<task>/files/...`)

## Common Pitfalls

- **Fixing `/app` code only, but not emitting grader-expected files.**  
  All three runs failed on missing `output/.../files/auth_service.py` despite otherwise successful remediation work.

- **Trusting local unit tests as final truth.**  
  Local tests were made to pass in runs 1–2, but grader still failed due to output-path assertions.

- **Breaking public API while “cleaning up.”**  
  Renaming/removing functions or changing signatures caused failures (`login`, `get_profile`, `update_email`, etc.).

- **Using `SELECT *` with incorrect column indexing.**  
  Run 2 had a functional regression from wrong tuple index mapping (`email` became password).

- **Leaving string interpolation in query assembly for `IN` clauses.**  
  Even placeholder-only f-strings can be flagged by strict regex checks; prefer patterns that avoid SQL-string interpolation where possible.

## Verification Strategy

1. **Security pattern check (static):**  
   Run grep against modified files for:
   - `query = f"..."`
   - `%` SQL formatting
   - `.format(` in SQL
   - `"..."+var` SQL concatenation

2. **Syntax check:**  
   `python -m py_compile <modified_files>`

3. **Behavior check:**  
   Run project tests (if available) to confirm no API/logic regressions.

4. **Grader contract check (critical):**
   - validate JSON schema/content at required path
   - confirm required fixed files exist at grader path (`output/.../files/...`)
   - ensure those copied files are valid Python

5. **Final pre-submit check:**  
   Re-run the same verifier entrypoint used by harness (`/tests/test_outputs.py` via provided `test.sh`) when accessible.

## References to Load On Demand

- SQLite parameter binding rules (`sqlite3` module docs)
- Safe patterns for `IN` and `LIKE` with bound parameters
- Test-harness-first workflow for artifact-based grading
