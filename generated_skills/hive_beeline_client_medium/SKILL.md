---
name: querying-hive-beeline-client-output
description: Extract table metrics via a Beeline-style CLI and write deterministic JSON output. Use when validating Hive client connectivity and producing machine-checked query summaries from terminal output.
---

# Querying Hive Beeline Client Output

## When to Use

- Validate that a Beeline-compatible client can query a Hive table.
- Compute simple aggregates (for example, total row count, top entity by frequency).
- Save results into a strict JSON artifact for downstream tests or automation.

## Minimal Reliable Workflow

1. Confirm client and table availability.
   - Run `SHOW TABLES;`
   - Run `DESCRIBE <table>;`
2. Run the aggregate queries with **simple, broadly supported SQL**.
   - Prefer `SELECT COUNT(*) FROM <table>;`
   - Prefer `SELECT key_col, COUNT(*) FROM <table> GROUP BY key_col ORDER BY COUNT(*) DESC, key_col ASC LIMIT 1;`
3. Parse Beeline’s ASCII table output by selecting only data rows.
   - Split on `|` and trim whitespace.
   - Accept numeric fields only for counts (`^[0-9]+$`).
   - Skip header/separator rows.
4. Echo extracted shell variables before writing JSON.
   - Example checks: `echo "count=$count"` and `echo "top=$top"`.
5. Write `/tmp/query_results.json` with exactly required keys and correct types.
   - `total_records` as integer
   - `top_customer` as string
6. Print the JSON file and visually confirm no missing values.

## Common Pitfalls

- **Using unsupported SQL variants in this client stub**  
  Evidence across all three runs: verifier failed on `SELECT COUNT(*) as cnt FROM customer_orders` with nonzero exit, even when produced JSON was correct.  
  Guardrail: prefer simplest query forms without aliases when validating manually against a stubbed client.

- **Fragile parsing that captures separators/header instead of data**  
  Evidence (Runs 2 and 3): parsing initially produced `count=` or `top=+------------------+...`, resulting in invalid JSON (`"total_records": ,`).  
  Guardrail: parse only `| ... |` rows, trim fields, and require numeric regex for count.

- **Writing JSON before validating extracted values**  
  Evidence (Runs 2 and 3): invalid intermediate files were written before variable checks.  
  Guardrail: always echo variables and only write JSON after both are non-empty and type-valid.

## Verification Strategy

1. **Artifact checks**
   - Ensure `/tmp/query_results.json` exists.
   - Validate JSON parses and has exactly required keys.
2. **Type checks**
   - Confirm `total_records` is integer, `top_customer` is string.
3. **Data checks via fresh queries**
   - Re-run supported queries (no alias assumptions) and compare results to JSON values.
4. **Harness sanity check (important)**
   - If JSON looks correct but tests fail on client query execution, inspect failing query text first.
   - In this task family, failures were test-induced by unsupported alias syntax (`AS cnt`), not by incorrect task completion.

## References to Load On Demand

- Robust extraction pattern (count):
  - `awk -F'|' '/^\|/{v=$2; gsub(/^ +| +$/,"",v); if(v~/^[0-9]+$/){print v; exit}}'`
- Robust extraction pattern (top key):
  - `awk -F'|' '/^\|/{k=$2;c=$3; gsub(/^ +| +$/,"",k); gsub(/^ +| +$/,"",c); if(k!="customer_name" && c~/^[0-9]+$/){print k; exit}}'`
