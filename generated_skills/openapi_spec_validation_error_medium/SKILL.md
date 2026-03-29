---
name: fixing-openapi-validation-errors
description: Repair invalid OpenAPI 3.x specifications and produce a validation summary file. Use when CI/CD fails on OpenAPI schema validation and deployment is blocked by spec errors.
---

# Fixing OpenAPI Validation Errors

## When to Use

Use this skill when an OpenAPI file is failing strict validation and the task requires:
- preserving API intent (no endpoint removal/behavior redesign),
- writing a corrected spec to a new file, and
- producing a small machine-readable summary (for graders/CI).

This workflow is based on three independent successful runs of the same task.

## Minimal Reliable Workflow

1. **Inspect and snapshot the source spec**
   - Read the full YAML (`sed -n '1,260p'`, then next chunk) before editing.
   - Copy into a new output file (for example `fixed-api-spec.yaml`) rather than mutating in place.

2. **Run a validator first to get a concrete anchor error**
   - Prefer installed tooling:
     - `openapi-spec-validator <file>` (CLI), or
     - Python API: `from openapi_spec_validator import validate_spec`.
   - Expect only the *first blocking error* initially (observed in all runs: missing `responses` on one operation surfaced first).

3. **Apply structural fixes that commonly co-occur**
   - Add missing required objects/fields (especially `responses` and response `description`).
   - Fix invalid `$ref` targets and add missing referenced schemas.
   - Correct parameter placement and schemas:
     - path params must be `in: path` and `required: true`,
     - non-body parameters need `schema`.
   - Fix invalid schema typing (`type: string` + `format: email`, not `type: email`).
   - Ensure object schemas have `type: object` where required.
   - Complete security schemes (for `type: http`, include `scheme`, optionally `bearerFormat`).

4. **Re-validate until clean**
   - Re-run validator on the fixed file until it returns OK/PASS.
   - Do not trust visual inspection alone.

5. **Write required summary artifact**
   - Use exact required format:
     - `ERRORS_FIXED=<number>`
     - `VALIDATION_STATUS=PASS|FAIL`
   - Keep `ERRORS_FIXED` as the count of distinct corrections made.

## Common Pitfalls

- **Stopping after first validator error**
  - Evidence: validator reported only `'responses' is a required property` first; additional issues were still present and had to be fixed manually/iteratively.

- **Assuming package installation is needed**
  - Evidence: one run attempted `pip install` and hit PEP 668 “externally-managed-environment”; validation still succeeded using preinstalled module/tooling.
  - Guardrail: check availability first (`which ...`, `python -c "import ..."`), avoid unnecessary installs.

- **Breaking semantics while fixing validation**
  - Over-correcting can change behavior. Keep endpoints/operations intact; make minimal spec-compliance edits.

- **Leaving dangling references**
  - Invalid refs (e.g., typoed schema name or missing component) are common and explicitly tested in CI-style checks.

- **Incorrect parameter modeling**
  - Path template variables must be path parameters; header/query params require explicit schema.

## Verification Strategy

Run both **spec validation** and **artifact checks**:

1. **Spec validator pass**
   - `openapi-spec-validator fixed-api-spec.yaml` → `OK`
   - or Python `validate_spec(...)` → no exception.

2. **Sanity assertions (mirrors common grader tests)**
   - Fixed spec file exists.
   - YAML parses cleanly.
   - Root fields exist: `openapi`, `info`, `paths`.
   - Each operation has a `responses` object.
   - No invalid/unresolved `$ref`.
   - Summary file exists and matches strict two-line format.
   - `VALIDATION_STATUS=PASS`.
   - `ERRORS_FIXED` is a positive integer.

3. **Final consistency check**
   - Confirm intended endpoints are still present and unchanged in purpose (only validation fixes applied).
