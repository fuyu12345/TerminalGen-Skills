---
name: validating-beast-xml-configurations
description: Validate BEAST XML files for structural and semantic rule violations, then emit a strict JSON report with accurate error aggregation. Use when XML may be malformed and full parsing alone would miss additional detectable issues.
---

# Validating BEAST XML Configurations

## When to Use

Use this skill when tasked with generating a `validation_report.json` for BEAST XML inputs under schema-like constraints (well-formedness, required elements, taxa consistency, sequence lengths, chain length, taxonset references, unique IDs), especially when malformed XML prevents full DOM parsing.

## Minimal Reliable Workflow

1. **Read rule sources first.**  
   Load schema/rules text and any auxiliary files before coding checks.

2. **Run dual-path validation (parser + text fallback).**
   - Attempt XML parse to detect well-formedness errors.
   - Continue with regex/text-based checks even if parsing fails.
   - Do **not** stop at parse failure.

3. **Validate required root and essential blocks defensively.**
   - Check `<beast>` root existence and `version` attribute.
   - Check presence of taxa block (`<taxa>`/`<taxon>`), data block (`<data>`/`<alignment>`), and run block (`<run>`/`<mcmc>`).

4. **Validate taxa consistency from actual XML references.**
   - Extract declared taxa IDs from `<taxon id="...">`.
   - Extract sequence taxon references (e.g., `<sequence taxon="...">`).
   - Report references missing from declarations.

5. **Validate sequence length consistency per alignment/data partition.**
   - Extract sequence payloads.
   - Normalize by removing whitespace/newlines.
   - Compare lengths within each partition and report mismatches.

6. **Validate chain length robustly.**
   - Accept either `<run>` or `<mcmc>` carrier.
   - Require `chainLength` present, integer, and `> 0`.

7. **Validate taxonset definitions vs references precisely.**
   - Build set of defined `<taxonset id="...">`.
   - Check `<taxonset idref="...">` used in calibration/prior contexts.
   - Avoid flagging unrelated `@...` references as taxonset errors.

8. **Validate global uniqueness of `id` attributes.**
   - Count all `id="..."` occurrences across the document.
   - Report duplicates once per repeated value.

9. **Emit strict output format only.**
   - Write JSON object exactly with:
     - `valid` (bool),
     - `error_count` (int),
     - `errors` (array of non-empty strings).
   - Ensure `error_count == len(errors)` and `valid == (error_count == 0)`.

## Common Pitfalls

- **Stopping validation after XML parse error.**  
  Observed in one run’s intermediate output: only one error (“not well-formed”) was reported, missing other detectable violations.  
  **Guardrail:** always run fallback text checks after parse failure.

- **Using auxiliary taxon lists with naive exact matching.**  
  One run falsely flagged expected taxa due to prefix mismatch (`taxon_...` vs bare species names).  
  **Guardrail:** normalize identifiers before comparing, or treat auxiliary lists as supplementary unless explicitly required.

- **Over-broad reference validation causing false positives.**  
  One run incorrectly flagged `@alignment` as an undefined taxon set.  
  **Guardrail:** constrain taxonset checks to `<taxonset idref="...">` and relevant calibration/prior contexts.

- **Hardcoding one BEAST tag variant.**  
  BEAST configs may use `<run>` instead of `<mcmc>`.  
  **Guardrail:** validate both alternatives for required analysis configuration and chain length.

- **Under-reporting or over-reporting duplicate IDs.**  
  Duplicate `id` values must be globally unique and reported clearly once per duplicated key.

## Verification Strategy

1. **Schema-level output verification**
   - Confirm report file exists at required path.
   - Confirm valid JSON object with exact required fields/types.
   - Confirm all errors are non-empty strings.
   - Confirm invariants:
     - `error_count == len(errors)`
     - `valid == (error_count == 0)`

2. **Rule coverage sanity verification**
   - For malformed sample XML, ensure report includes well-formedness error **and** additional semantic findings when detectable.
   - Cross-check representative violations:
     - undeclared taxa referenced in sequences,
     - inconsistent sequence lengths,
     - non-positive chain length,
     - undefined calibration taxonset reference,
     - duplicate ID.

3. **Regression check against known failure modes from trajectories**
   - Reject outputs that only contain parse error when other violations are plainly visible.
   - Reject outputs with prefix-based taxon false positives.
   - Reject outputs that misclassify generic `@...` references as taxonset errors.
