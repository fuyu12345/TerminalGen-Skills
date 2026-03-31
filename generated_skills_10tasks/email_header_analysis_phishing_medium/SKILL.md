---
name: analyzing-email-headers-for-phishing
description: Analyze `.eml` headers to classify phishing vs legitimate messages and generate a schema-compliant JSON report. Use when investigating a mailbox corpus for phishing indicators under terminal-bench style output constraints.
---

# Analyzing Email Headers for Phishing

## When to Use
- Given multiple raw email files (typically `.eml`) and asked to split into `phishing` vs `legitimate`.
- Required to output structured JSON with full coverage of all files.
- Evaluation checks both **format correctness** and **classification accuracy**.

## Minimal Reliable Workflow
1. **Enumerate the corpus first.**
   - Run `ls -1 /emails` (or target directory) and capture the exact file list.
   - Treat this as the source of truth for later completeness checks.

2. **Do a fast triage pass on key headers for every file.**
   - Extract at least:
     - `From`, `Reply-To`, `Return-Path`
     - `Authentication-Results`, `Received-SPF`, `DKIM-Signature`
     - `Received`, `Date`, `Message-ID`, `Subject`
   - Use a loop to get quick signal across all files.

3. **Escalate to full header inspection for ambiguous or high-risk messages.**
   - Print headers up to first blank line (`sed -n '1,/^$/p' file.eml`).
   - Confirm exact SPF/DKIM/DMARC outcomes and sender identity alignment.
   - Verify relay chain plausibility and lookalike/typosquat domains.

4. **Classify with multi-signal logic (not single-header logic).**
   - Strong phishing indicators:
     - SPF/DKIM/DMARC fail or none (especially with impersonation)
     - From/Reply-To mismatch
     - Typosquatted or deceptive domains
     - Suspicious relay geography/infrastructure
     - Urgent social-engineering context paired with header anomalies
   - Strong legitimate indicators:
     - Sender-domain alignment
     - SPF/DKIM/DMARC pass
     - Coherent internal/provider relay chain

5. **Write output JSON exactly in required schema.**
   - Include:
     - `phishing_emails` (array of filenames)
     - `legitimate_emails` (array of filenames)
     - `suspicious_count` (integer)
   - Ensure every file appears exactly once across both arrays.

## Common Pitfalls
- **Relying on partial header snippets only.**  
  In observed runs, quick grep passes were useful, but full-header follow-up was needed to confirm auth failures and spoofing details.
- **Missing data due to terminal output truncation.**  
  Combined dumps can be truncated; inspect individual files when output is clipped.
- **Under-classifying because only one indicator is checked.**  
  Example pattern: messages with suspicious domains + bad relays + auth failures are clearer than any single signal alone.
- **Schema mistakes despite correct analysis.**  
  Forgetting one email, duplicating filenames, or mismatching `suspicious_count` can fail tests even if reasoning is correct.

## Verification Strategy
Run verification aligned to typical grader assertions:

1. **File existence**
   - Confirm `/solution/phishing_analysis.json` exists.

2. **JSON validity**
   - Run `python3 -m json.tool /solution/phishing_analysis.json`.

3. **Required fields and types**
   - Ensure keys exist and types are:
     - arrays for `phishing_emails`, `legitimate_emails`
     - integer for `suspicious_count`

4. **Coverage and uniqueness**
   - Check union of both arrays equals the full `/emails` file set.
   - Check no duplicates across or within arrays.

5. **Count consistency**
   - Verify `suspicious_count == len(phishing_emails)`.

6. **Classification confidence check**
   - Re-open any borderline file and confirm SPF/DKIM/DMARC + identity alignment before finalizing.

## References to Load On Demand
- RFC 7208 (SPF), RFC 6376 (DKIM), RFC 7489 (DMARC)
- Practical header triage commands:
  - Bulk key-field extraction loop
  - `sed -n '1,/^$/p'` for full header block
