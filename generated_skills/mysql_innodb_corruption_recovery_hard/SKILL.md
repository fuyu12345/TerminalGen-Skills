---
name: recovering-mysql-innodb-corruption
description: Recover corrupted MySQL dump files into a clean InnoDB database with accurate restore metrics and test-compatible root authentication. Use when SQL dumps have syntax/truncation corruption and validation connects via PyMySQL.
---

# Recovering MySQL InnoDB Corruption

## When to Use
- Restore partially corrupted `.sql` dumps (missing semicolons, truncated INSERTs, bad quotes, duplicate keys).
- Maximize recoverable rows instead of requiring perfect lossless restore.
- Produce a summary JSON with accurate table and row counts.
- Pass automated checks that connect with `pymysql` as `root` (not just local `mysql` socket CLI).

## Minimal Reliable Workflow
1. **Inspect tests first (critical).**
   - Confirm how verifier connects (host/user/password/plugin assumptions).
   - In these runs, all failures were `OperationalError(1698): Access denied for user 'root'@'localhost'` from PyMySQL, even when CLI imports looked successful.

2. **Start and confirm MySQL service.**
   - Verify `mysqladmin ping` and basic SQL execution.
   - Guard against `ERROR 2002` (socket not found) before doing any recovery work.

3. **Make root authentication test-compatible (not only socket-auth).**
   - Ensure `root@localhost` can authenticate the same way as the verifier (PyMySQL/TCP path).
   - If needed, alter root plugin/password policy so Python client login works without interactive socket auth.

4. **Create a fresh target DB and clean InnoDB tables.**
   - Prefer manual, known-good DDL when dump `CREATE TABLE` is corrupted.
   - Keep schema permissive enough to load salvageable data (defer strict FK enforcement).

5. **Sanitize inserts from dumps into load files.**
   - Extract recoverable INSERT statements.
   - Normalize terminators (`;`), convert to `INSERT IGNORE`, skip clearly truncated/unbalanced statements.
   - Handle common quote/encoding hazards (e.g., apostrophes in words like `Men's`, `O'Reilly`).
   - Keep per-table files for easier debugging.

6. **Load in safe order with tolerant session settings.**
   - Use:
     - `SET FOREIGN_KEY_CHECKS=0`
     - relaxed `sql_mode` (as needed)
     - `mysql --force`
   - Import parent tables before dependent ones when possible.

7. **Compute counts from real table queries, not estimates.**
   - `tables_restored`: count tables in `information_schema.tables` for `recovered_db`.
   - `total_rows_loaded`: sum `SELECT COUNT(*)` per restored table.
   - Write `/root/recovery_summary.json` exactly with required keys/types.

## Common Pitfalls
- **Passing local CLI checks but failing verifier auth**  
  Evidence: all 3 runs failed with PyMySQL `1698 Access denied`, while summary JSON existed and data loads appeared successful.
- **Not starting MySQL before import**  
  Evidence: run logs showed `ERROR 2002` until service start.
- **Over-escaped sanitizer regex causing zero recovered rows**  
  Evidence: one run’s sanitizer kept `0` statements due incorrect regex escaping.
- **Using corrupted dump DDL directly**  
  Evidence: malformed `CREATE TABLE` caused missing-table import cascades.
- **Row total miscalculation via piped `while` loop subshell**  
  Evidence: table had rows but computed total stayed `0`.
- **Using approximate `information_schema.table_rows` for totals**  
  Use explicit `COUNT(*)` queries instead.

## Verification Strategy
Run these checks **before finalizing**:

1. **Auth parity check (must mimic tests):**
   - Python one-liner using `pymysql.connect(host='localhost', user='root', password='')`.
   - Fail fast if this does not connect.

2. **Database/object checks:**
   - `SHOW DATABASES LIKE 'recovered_db';`
   - `SHOW TABLES FROM recovered_db;`
   - Confirm every restored table engine is `InnoDB`.

3. **Data/queryability checks:**
   - `SELECT COUNT(*)` from each table.
   - Run simple `SELECT ... LIMIT 1` per table to ensure queryability.

4. **Summary accuracy checks:**
   - Recompute `tables_restored` and `total_rows_loaded` from live DB.
   - Compare to `/root/recovery_summary.json`.

5. **JSON validity check:**
   - Validate with `python3 -m json.tool /root/recovery_summary.json`.

## References to Load On Demand
- MySQL auth plugin compatibility (`auth_socket` vs password plugins) for Python clients.
- Robust SQL statement tokenization/parsing for corrupted dumps.
- Safe bulk-load modes (`--force`, `sql_mode`, FK/unique checks).
