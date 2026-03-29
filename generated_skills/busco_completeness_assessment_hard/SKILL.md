```markdown
---
name: assessing-busco-assembly-completeness
description: Consolidate BUSCO short summaries across multiple assemblies, rank assemblies by completeness/duplication/fragmentation rules, and write a strict 4-line recommendation file. Use when BUSCO outputs are scattered and a deterministic selection report is required.
---

# Assessing BUSCO Assembly Completeness

## When to Use

- Compare multiple BUSCO `short_summary.txt` outputs and select one assembly for downstream work.
- Produce a machine-validated output file with exact formatting constraints.
- Handle missing/unreadable/malformed BUSCO summaries without crashing.
- Apply warning thresholds (`POOR`, `HIGH_DUP`) while still selecting the best valid assembly.

## Minimal Reliable Workflow

1. **Enumerate all expected assembly result paths first.**  
   Use a fixed assembly list (for example: `alpha`, `beta`, `gamma`) and map each to:
   `/data/busco_results/run_assembly_<name>/short_summary.txt`.

2. **Read every summary file explicitly.**  
   Treat missing/unreadable files as invalid assemblies.  
   Keep processing remaining assemblies instead of failing the whole run.

3. **Parse BUSCO metrics robustly.**  
   Extract at least:
   - Completeness `C`
   - Duplication `D`
   - Fragmentation `F`  
   Prefer parsing the compact BUSCO line:
   `C:..%[S:..%,D:..%],F:..%,...`  
   Reject assemblies whose metrics cannot be parsed or are out of range (0–100).

4. **Compute warnings for valid assemblies.**
   - Add `<assembly>:POOR` if `C < 85.0`
   - Add `<assembly>:HIGH_DUP` if `D > 10.0`

5. **Select recommendation deterministically among valid assemblies.**
   - If completeness differs by more than 2.0%, choose higher `C`.
   - If within 2.0%, choose lower `D`.
   - If still tied, choose lower `F`.
   - If still tied, apply deterministic fallback (for example lexical assembly name).

6. **Handle no-valid-assembly case explicitly.**
   Write:
   - `RECOMMENDED=NONE`
   - `COMPLETENESS=N/A`
   - `DUPLICATION=N/A`
   - `WARNINGS=ALL_FAILED`

7. **Write exact output file format (`/results/assembly_recommendation.txt`).**  
   Exactly 4 lines:
   - `RECOMMENDED=<assembly|NONE>`
   - `COMPLETENESS=<one-decimal|N/A>`
   - `DUPLICATION=<one-decimal|N/A>`
   - `WARNINGS=<comma-list|NONE|ALL_FAILED>`

## Common Pitfalls

- **Skipping directory inspection before writing output.**  
  In successful runs, all three assembly directories were listed/read first; this aligns with tests that verify BUSCO files were actually examined.

- **Hardcoding recommendation from assumed data.**  
  One successful run manually wrote final values only *after* inspecting summaries. Keep this order; do not hardcode without parsing.

- **Non-deterministic ranking when metrics are close.**  
  Encode the “within 2% completeness => use duplication” rule explicitly, then fragmentation tie-breaker.

- **Formatting drift in output file.**  
  Common breakpoints: wrong line count, missing trailing newline, wrong key names, extra spaces, or non-`N/A` strings.

- **Ignoring invalid/malformed files.**  
  Invalid assemblies must be excluded from recommendation, not treated as zero-values.

## Verification Strategy

Run these checks before marking complete:

1. **Structural checks**
   - `test -s /results/assembly_recommendation.txt`
   - `wc -l /results/assembly_recommendation.txt` must be `4`
   - `sed -n '1,4p' /results/assembly_recommendation.txt` to confirm exact key order.

2. **Format checks**
   - `RECOMMENDED` is one of valid assembly names or `NONE`.
   - `COMPLETENESS`/`DUPLICATION` are one decimal (e.g., `94.5`) or `N/A` only when `RECOMMENDED=NONE`.
   - `WARNINGS` is `NONE`, `ALL_FAILED`, or comma-separated `<assembly>:<FLAG>` tokens.

3. **Logic checks against parsed metrics**
   - Confirm all expected BUSCO summaries were attempted/read.
   - Confirm warnings reflect thresholds.
   - Confirm selection rule application order (C gap >2%, then D, then F).

**Terminal evidence across 3/3 successful runs:** this workflow consistently produced:
`RECOMMENDED=alpha`, `COMPLETENESS=94.5`, `DUPLICATION=2.1`, `WARNINGS=beta:POOR,gamma:HIGH_DUP`, and passed all 13 tests.
```
