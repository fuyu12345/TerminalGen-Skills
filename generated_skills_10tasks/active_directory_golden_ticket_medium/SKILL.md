---
name: detecting-active-directory-golden-ticket-from-artifacts
description: Determine whether a golden ticket attack occurred by correlating Kerberos ticket anomalies, domain policy, and auth event patterns, then emit a strict 3-line verdict file. Use when investigating AD compromise artifacts in terminal tasks with format-validated output.
---

# Detecting Active Directory Golden Ticket from Artifacts

## When to Use
- Investigating suspected Kerberos abuse in Active Directory from static artifacts (ticket dump + auth logs + domain config).
- Required to produce a strict, machine-checked verdict file (fixed lines/prefixes/format).
- Need to avoid false conclusions from a single indicator by correlating multiple sources.

## Minimal Reliable Workflow
1. **Inspect all evidence sources first.**  
   Read:
   - `domain_config.txt` (ticket policy, KRBTGT info, SIDs)
   - `kerberos_tickets.json` (ticket fields, anomalies, PAC fields)
   - `auth_events.csv` (EventID patterns and timing)

2. **Establish expected baselines from domain policy.**  
   Extract max ticket lifetime, max renewal window, expected encryption types, and KRBTGT account details.

3. **Identify forged-TGT indicators in ticket data.**  
   Flag tickets showing combinations like:
   - Lifetime/renewal far beyond policy
   - Missing `initial` flag
   - Client address `0.0.0.0` or hostless behavior
   - Encryption downgrade or unusual type for context
   - PAC with high-privilege group memberships
   - Explicit KRBTGT hash usage fields (if present)

4. **Correlate with auth events to confirm issuance mismatch.**  
   Look for service-ticket activity (e.g., repeated 4769) without corresponding TGT issuance events (e.g., missing 4768) for the same identity/time window.

5. **Decide detection status from combined evidence, not one signal.**  
   Mark detected when multiple independent indicators agree (ticket structure + event mismatch + privileged PAC/hash evidence).

6. **Write verdict in exact required format.**  
   Use deterministic write (e.g., `printf`) to avoid formatting drift:
   - `DETECTED: yes|no`
   - `KRBTGT_HASH: <32-lowercase-hex|unknown>`
   - `FORGED_USER: <lowercase username|none>`

7. **Perform immediate format sanity checks.**  
   Verify exact line count and rendered content before completion.

## Common Pitfalls
- **Using only one artifact source.**  
  In all successful runs, correct outcome came from correlating JSON ticket anomalies *and* CSV event patterns *and* domain policy.
- **Failing strict output formatting.**  
  Tests validated exact 3-line structure, prefixes, lowercase username, and hash format. Extra lines, wrong case, or wrong prefixes can fail despite correct analysis.
- **Not enforcing lowercase output usernames.**  
  Evidence may show `Administrator`; output must be lowercase when required (`administrator`).
- **Skipping line-count verification.**  
  Heredoc/manual edits can introduce accidental blank lines; verify with `wc -l`.
- **Treating RC4 alone as definitive.**  
  RC4 may appear legitimately in some environments; use it as supporting evidence only when paired with stronger forged-ticket indicators.

## Verification Strategy
Use a two-layer check:

1. **Analytic verification (content correctness):**
   - Confirm suspicious ticket violates domain ticket/renewal policy.
   - Confirm missing/abnormal issuance pattern in auth events (e.g., 4769 activity without matching 4768).
   - Confirm forged identity and KRBTGT hash source from ticket/PAC/domain data.

2. **Output-contract verification (test-aligned):**
   - File exists at required path.
   - Exactly 3 lines.
   - Exact prefixes: `DETECTED:`, `KRBTGT_HASH:`, `FORGED_USER:`.
   - Hash is 32-char lowercase hex when detected.
   - Username is lowercase and consistent with evidence.
   - Detection line consistent with supplied hash/user fields.

(These checks match the observed grader behavior across all three successful runs: format, consistency, lowercase username, and expected detected/user values.)

## References to Load On Demand
- Kerberos Event IDs quick map (4768/4769/4770 semantics)
- Golden ticket forensic indicators (PAC abuse, lifetime anomalies, TGT issuance mismatch)
- Shell-safe file emission patterns (`printf` vs heredoc) for exact-line outputs
