---
name: hardening-grep-pcre-patterns
description: Rewrite backtracking-prone PCRE log patterns into linear-time equivalents while preserving expected matches. Use when grep -P searches hang, spike CPU, or timeout on large log files.
---

# Hardening Grep PCRE Patterns

## When to Use

Use this skill when all of the following are true:

- A pattern set is executed with `grep -P` over large logs.
- Existing regexes contain nested/overlapping quantifiers (for example `(X.*)+`, `(A|B)*` after `.*`, repeated greedy groups).
- Searches are slow or appear hung.
- A fixed output file must keep pattern order and preserve sample-match behavior.

---

## Minimal Reliable Workflow

1. **Inspect originals and expected examples first.**  
   Print numbered originals and sample cases:
   ```bash
   nl -ba /workspace/patterns/original.txt
   nl -ba /workspace/test/sample_matches.txt
   ```
   Look for catastrophic structures such as:
   - `(token.*)+`
   - `(group|alt)*` after broad `.*`
   - nested greedy repeats.

2. **Preserve intent, then simplify structure.**  
   Replace nested quantified groups with single-pass token ordering:
   - Prefer `\btoken\b[^\n]*\btoken2\b` over `(token.*)+...`.
   - Use explicit classes for bounded subparts (for service names, IDs, etc.).
   - Keep one line-scanning quantifier between required anchors/tokens.

3. **Write exactly one pattern per line, in original order.**  
   Save to target file:
   ```bash
   cat > /workspace/solution/fixed.txt <<'EOF'
   ...
   EOF
   ```

4. **Validate file shape defensively.**  
   Check both numbered display and line count:
   ```bash
   nl -ba /workspace/solution/fixed.txt
   wc -l /workspace/solution/fixed.txt
   ```
   (Numbered display catches missing trailing-newline confusion better than `wc -l` alone.)

5. **Validate semantic matching per pattern section.**  
   Extract each sample block and confirm each corresponding regex matches all lines in that block.

6. **Validate runtime with available timing tool.**  
   If `/usr/bin/time` is missing, use shell built-in:
   ```bash
   TIMEFORMAT='elapsed=%R sec'
   time bash -lc 'while IFS= read -r p; do grep -P "$p" /workspace/logs/app.log >/dev/null; done < /workspace/solution/fixed.txt'
   ```
   Ensure total runtime is under the requirement (for this task class: <5s).

7. **Run verifier-aligned checks before finalizing.**  
   Confirm your local parsing assumptions match the grader/test parser format exactly.

---

## Common Pitfalls

- **Trusting `wc -l` alone for “number of patterns.”**  
  In observed runs, a 5th pattern without trailing newline made `wc -l` report `4`. Use `nl -ba` to confirm actual entries.

- **Using hardcoded `/usr/bin/time` in minimal containers.**  
  Multiple runs hit `bash: /usr/bin/time: No such file or directory`. Fall back to shell `time` + `TIMEFORMAT`.

- **Keeping catastrophic shape while only changing literals.**  
  Replacing words but leaving nested greediness (`(X.*)+`) does not remove worst-case backtracking risk.

- **Passing ad-hoc checks but failing verifier due format mismatch.**  
  Observed failures were caused by test parsing assumptions, not regex correctness/performance. Always compare your local validation logic to actual test assertions.

---

## Verification Strategy

Use a 4-layer verification stack:

1. **PCRE compile validity**
   ```bash
   while IFS= read -r p; do grep -P "$p" /dev/null >/dev/null; done < /workspace/solution/fixed.txt
   ```

2. **Structural correctness**
   - File exists.
   - Exactly 5 regex lines in required order.
   - No comments or extra text.

3. **Behavioral correctness**
   - Each pattern matches all examples in its corresponding section.
   - Avoid cross-section assumptions; test per section.

4. **Performance correctness**
   - Time all patterns over full log in one run.
   - Use shell `time` fallback when GNU `time` path is unavailable.

5. **Verifier parity check (critical from observed failures)**
   - Open the test script and confirm section delimiters/parsing regex align with dataset format.
   - If mismatch is test-induced, record as external blocker; do not overfit regex changes to compensate for broken harness logic.
