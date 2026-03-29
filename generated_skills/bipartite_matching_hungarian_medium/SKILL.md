---
name: solving-square-assignment-json
description: Compute an optimal one-to-one assignment from an N×N cost matrix and write strict JSON output (`assignments`, `total_cost`). Use when a terminal task provides bipartite matching/driver-route costs and grades optimality plus output schema.
---

# Solving Square Assignment JSON

## When to Use

- Receive a file where line 1 is `N` and next `N` lines are an `N×N` integer cost matrix.
- Need minimum-cost one-to-one row→column assignment (classic assignment problem).
- Must output JSON at a fixed path with exact keys, typically:
  - `assignments`: permutation of `0..N-1`
  - `total_cost`: sum of chosen costs
- Expect tests for file existence, JSON validity, permutation validity, cost consistency, and optimality.

## Minimal Reliable Workflow

1. **Inspect input shape before solving.**
   - Read file, parse `N`, parse `N` rows of `N` ints.
   - Fail fast if matrix is not square.

2. **Solve assignment optimally (not greedily).**
   - Prefer Hungarian algorithm for general `N` (polynomial, robust).
   - Use brute-force permutations only when `N` is clearly small enough.

3. **Build assignment in required orientation.**
   - Ensure `assignments[i] = chosen_column_for_row_i` (driver index → route index).

4. **Compute `total_cost` from assignment.**
   - Recalculate directly from matrix; do not hardcode or trust intermediate values.

5. **Write strict JSON to required path.**
   - Include exactly required fields unless task explicitly permits extras.

6. **Print/read back output file.**
   - Confirm content and shape before final submission.

## Common Pitfalls

- **Using non-optimal heuristics** (row-min, greedy) and failing optimality tests.
- **Wrong assignment direction** (column→row instead of row→column).
- **Mismatched `total_cost`** from arithmetic or stale variable errors.
- **Schema drift** (extra keys, missing key names, wrong array length).
- **Assuming brute force always scales**; it worked at `N=6` in one run but is fragile for larger `N`.

## Verification Strategy

Run checks mirroring grader expectations:

1. **File and JSON**
   - Confirm output file exists.
   - Parse JSON successfully.

2. **Schema**
   - Verify keys include required fields (`assignments`, `total_cost`).
   - Verify `len(assignments) == N`.

3. **Permutation validity**
   - Confirm sorted assignments equals `list(range(N))`.

4. **Cost consistency**
   - Recompute `sum(cost[i][assignments[i]] for i in range(N))`.
   - Assert equals `total_cost`.

5. **Optimality sanity check**
   - If `N` is small, cross-check with brute force once.
   - Otherwise rely on tested Hungarian implementation.

**Terminal evidence across 3 successful runs:** both exhaustive search and Hungarian implementation produced the same result on the provided matrix (`assignments [3,0,4,1,5,2]`, `total_cost 434`), and all 7 tests passed (existence, JSON validity, required fields, array length, permutation, cost match, optimality). This supports Hungarian as the safer default and brute force as a bounded-size cross-check.

## References to Load On Demand

- Hungarian algorithm implementation template (1-indexed potentials version).
- Small-`N` brute-force verifier snippet for regression checks.
