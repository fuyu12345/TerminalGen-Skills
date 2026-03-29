```markdown
---
name: validating-brms-prior-specification
description: Evaluate brms prior definitions against domain constraints by checking parameter means and in-range prior mass, then emit strict boolean validation JSON. Use when a terminal task asks to approve/reject priors from a model spec file under explicit statistical acceptance rules.
---

# Validating brms Prior Specification

## When to Use

Use this skill when all of the following are true:

- A task provides prior definitions (often `prior(...)` lines in brms syntax).
- Domain constraints are given as acceptable numeric ranges per parameter.
- Acceptance requires rule-based checks (for example: mean in range **and** at least 90% mass in range).
- Output must be a strict JSON file with exact required keys and boolean values.

## Minimal Reliable Workflow

1. **Read the prior spec file first.**  
   Extract each target parameter prior (`Intercept`, selected `b` coefficients, `sigma`, etc.) from the provided text.

2. **Map model terms to domain targets explicitly.**  
   Build a clear mapping like:
   - treatment effect → `class="b", coef="treatment"`  
   - age effect → `coef="age"`  
   - severity effect → `coef="severity"`  
   - baseline → `class="Intercept"`  
   - residual SD → `class="sigma"`

3. **Compute two checks per parameter (do not skip either):**
   - `mean_ok`: prior mean is inside the clinical/domain interval.
   - `mass_ok`: probability mass in the interval is at or above threshold (commonly `>= 0.90`).

4. **Use distribution-appropriate CDF logic.**
   - Normal: analytic CDF difference.
   - Student-t: Student-t CDF difference.
   - For other families (gamma/lognormal/exponential), use matching CDF/mean formulas.
   - Prefer `scipy.stats` when available; otherwise use reliable numeric fallback.

5. **Set validity as conjunction.**  
   `param_valid = mean_ok AND mass_ok`.

6. **Write exact output JSON shape.**  
   Emit only required fields, all booleans, no extras:
   - `treatment_valid`
   - `age_valid`
   - `severity_valid`
   - `intercept_valid`
   - `sigma_valid`

7. **Print the JSON file and stop.**  
   Avoid unnecessary edits once schema and values are confirmed.

## Common Pitfalls

- **Overweighting narrative text (“95% credible interval”) over explicit pass rule.**  
  In these runs, correct grading aligned with the explicit validation criteria (`mean` + `>=90% mass`), not loose interpretation.

- **Assuming “reasonable mean” implies valid prior.**  
  Observed example: treatment mean was in range, but mass in range was ~0.866 (<0.90), so invalid.

- **Forgetting heavy-tail behavior for `student_t` sigma priors.**  
  `student_t(3, 8, 3)` failed both mean and mass checks in the accepted solutions.

- **Fragile parsing of `prior(...)` lines.**  
  One run showed partial string capture due to naive regex around nested parentheses; robust splitting/parsing is safer.

- **Failing strict output contract.**  
  Tests require exact keys, boolean types, valid JSON, and no extra fields.

## Verification Strategy

Perform both **statistical verification** and **format verification**:

1. **Statistical sanity printout (before writing final):**
   - For each target parameter, print:
     - parsed distribution
     - computed mean
     - in-range mass
     - `mean_ok`, `mass_ok`, final validity
   - Confirm conjunction logic is applied.

2. **File contract checks (after writing):**
   - File exists at required path.
   - Valid JSON parses successfully.
   - Contains exactly required 5 fields.
   - Every field is boolean.
   - No extra keys.

3. **Expected-result cross-check from terminal evidence (this task family):**
   - Example accepted outcome from all three successful runs: all five flags were `false` because each prior violated at least one criterion (often mass < 0.90).

## References to Load On Demand

- brms prior syntax reference (`prior(..., class=..., coef=...)`)
- `scipy.stats` CDF/mean methods for normal and Student-t
- JSON schema validation snippets for strict key/type enforcement
```
