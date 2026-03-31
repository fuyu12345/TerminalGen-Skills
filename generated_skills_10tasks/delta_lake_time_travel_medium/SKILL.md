---
name: finding-last-valid-versioned-snapshot
description: Identify the most recent valid dataset version by checking versioned CSV snapshots in chronological order and stopping at the first invalid snapshot. Use when selecting a rollback point after data-quality regressions.
---

# Finding Last Valid Versioned Snapshot

## When to Use
- Determine a rollback version from `v1`, `v2`, … snapshot directories.
- Validate a rule like “all `amount` values must be `> 0`” per version.
- Produce a single-number answer file for graders/automation.

## Minimal Reliable Workflow
1. **Enumerate versions numerically, not lexicographically.**  
   Extract numeric suffixes from `v*` directories and sort ascending (`sort -n`).

2. **Validate each version’s CSV in time order.**  
   For each `vN/transactions.csv`, skip header and fail the version if any row violates the rule (`amount <= 0`).

3. **Treat this as a rollback boundary problem.**  
   Track `last_valid` and **stop at first invalid version** (temporal corruption onset model).

4. **Write only the integer result.**  
   Save to target file with `printf "%s"` (no `v` prefix, no extra text, no trailing newline).

5. **Quick-check output formatting.**  
   `cat` plus `od -An -t c` (or equivalent) to confirm single-line integer and no newline if required.

### Reliable shell pattern
```bash
last_valid=0
for v in $(find /workspace/data/transactions/versions -mindepth 1 -maxdepth 1 -type d -name 'v*' \
          | sed 's#.*/v##' | sort -n); do
  f="/workspace/data/transactions/versions/v${v}/transactions.csv"
  awk -F, 'NR==1{next} $3<=0{bad=1; exit} END{exit bad}' "$f"
  if [ $? -ne 0 ]; then
    break
  fi
  last_valid="$v"
done

mkdir -p /workspace/solution
printf "%s" "$last_valid" > /workspace/solution/last_valid_version.txt
```

## Common Pitfalls
- **Using an `awk` `END{exit 0}` that overrides earlier failure.**  
  Observed in two failed runs: script used `($3+0)<=0{exit 1} END{exit 0}`, which returns success even on bad rows, causing every version to look valid and output `8` instead of `5`.

- **Selecting “max valid anywhere” instead of “last valid before first invalid.”**  
  For rollback/time-travel tasks, evaluate sequentially and break at first bad snapshot.

- **Relying on glob order for versions.**  
  `v10` vs `v2` can misorder; always numeric sort.

- **Formatting misses.**  
  Avoid `v5`, extra words, or trailing newline when strict graders check exact file content.

## Verification Strategy
Use both **logic verification** and **output-format verification**:

1. **Independent recompute of expected version** (sequential, break on first invalid), e.g., tiny Python or a second shell method.
2. **Cross-check answer file content**:
   - File exists and non-empty.
   - Parses as integer.
   - Contains only digits (no `v` prefix).
   - Single line.
   - No trailing newline if required (`od -An -t c /path/file`).
3. **If result seems “too high,” inspect validator logic first** (especially awk exit behavior with END blocks).
