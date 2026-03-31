---
name: implementing-sqlite-fts5-search-index
description: Implement an idempotent SQLite FTS5 search index with relevance ranking across multiple text columns while preserving the base table schema. Use when adding production-ready full-text search migrations and validating them from terminal tests.
---

# Implementing SQLite FTS5 Search Index

## When to Use

- Building SQL-only search upgrades for existing SQLite tables (for example, `products` with `title` + `description`)
- Replacing weak `LIKE` search with ranked full-text search
- Delivering idempotent migration scripts (`CREATE ... IF NOT EXISTS`, safe re-run behavior)
- Satisfying test harnesses that verify:
  - script executes cleanly,
  - FTS table exists,
  - multi-word queries work,
  - ranking is present,
  - original table remains intact

## Minimal Reliable Workflow

1. **Inspect test expectations before writing SQL.**  
   Identify required artifacts (script path, expected table names/patterns, ranking behavior, performance checks).

2. **Confirm source table schema.**  
   Query `.schema <base_table>` and ensure target columns exist (for example, `id`, `title`, `description`).

3. **Create an external-content FTS5 table.**  
   Use:
   - `CREATE VIRTUAL TABLE IF NOT EXISTS ... USING fts5(...)`
   - `content='<base_table>'`
   - `content_rowid='<pk_column>'`
   This preserves the original table and indexes text from multiple columns.

4. **Add sync triggers (idempotent).**  
   Create `AFTER INSERT`, `AFTER DELETE`, and `AFTER UPDATE` triggers with `IF NOT EXISTS` so FTS stays consistent with base-row changes.

5. **Backfill existing rows safely.**  
   Use FTS control command:
   - `INSERT INTO <fts_table>(<fts_table>) VALUES ('rebuild');`
   This avoids touching base table data while ensuring the index is populated.

6. **Include ranking usage in comments (or default rank config).**  
   Prefer `bm25(<fts_table>, title_weight, description_weight)` and explain that lower score is better.  
   Use higher title weight than description weight for better relevance ordering.

7. **Write to required output path and run once locally.**  
   Save as the exact expected file (for example, `/tmp/search_solution.sql`), then execute with sqlite3 against the target DB.

## Common Pitfalls

- **Marking task complete without passing local execution checks.**  
  In all three runs, the script existed but tests still failed because execution preconditions were broken; completion was marked anyway.

- **Assuming DB validity from path existence alone.**  
  Evidence from all runs: `/var/data/products.db` existed, but every SQL action failed with `file is not a database`.  
  Guardrail: force a real read (`PRAGMA schema_version;` or `.schema`) before trusting the DB.

- **Treating harness/environment corruption as SQL logic failure.**  
  The repeated failure (`sqlite3.DatabaseError: file is not a database`) happened before FTS logic could be evaluated.  
  Distinguish environment/data-file issues from migration correctness.

- **Skipping end-to-end ranking verification.**  
  Defining FTS is insufficient; confirm MATCH query + `bm25(...) ORDER BY` behavior and that multi-word search returns rows.

## Verification Strategy

Run verification in this order:

1. **Database sanity**
   - `sqlite3 /path/db "PRAGMA schema_version;"`  
   - `sqlite3 /path/db ".schema <base_table>"`
   - If either returns `file is not a database`, stop and report environment/data issue before grading assumptions.

2. **Script validity**
   - Ensure script exists and non-empty at required path.
   - Execute: `sqlite3 /path/db < /tmp/search_solution.sql` with no parse/runtime errors.

3. **Schema outcomes**
   - Confirm at least one table matching `%fts%`.
   - Confirm original base table still exists and schema unchanged.

4. **Functional search**
   - Run single-term and multi-word `MATCH` queries.
   - Join back to base table via `rowid = id`.
   - Confirm non-empty results.

5. **Ranking behavior**
   - Query with `bm25(fts_table, title_weight, description_weight)`.
   - Verify ordered output uses relevance score (ascending for bm25).

6. **Performance check**
   - Time representative MATCH queries and confirm they satisfy expected latency budget.

## References to Load On Demand

- SQLite FTS5 docs (external-content tables, `rebuild`, delete commands)
- SQLite trigger syntax for idempotent schema migrations
- `bm25()` weighting semantics and ordering conventions
