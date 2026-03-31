```markdown
---
name: diagnosing-systemd-dropin-dependency-errors
description: Identify and report incorrect systemd unit/drop-in dependency lines by inspecting override files, validating referenced targets, and producing exact incorrect/correct replacements. Use when a service starts manually but fails during boot due to suspected dependency misconfiguration.
---

# Diagnosing Systemd Drop-in Dependency Errors

## When to Use
- Service starts manually (`systemctl start <svc>` works) but fails on boot.
- A unit override/drop-in (for example `.../service.d/override.conf`) is suspected.
- Task requires reporting the **exact bad line** and a corrected replacement, not necessarily applying the fix.
- Runtime is containerized or constrained, and `systemctl` may not be fully usable.

## Minimal Reliable Workflow
1. **Read the drop-in file first.**  
   Run `cat /etc/systemd/system/<service>.service.d/override.conf` (or relevant drop-in path) and capture suspicious dependency directives (`After=`, `Wants=`, `Requires=`, `Before=`).

2. **Inspect base unit file from disk.**  
   Read `/lib/systemd/system/<service>.service` and/or `/usr/lib/systemd/system/<service>.service` to understand expected dependency style and avoid over-correcting.

3. **Handle `systemctl` unavailability gracefully.**  
   If `systemctl cat` fails with “System has not been booted with systemd as init system (PID 1),” continue with file-based inspection.  
   (Observed in all runs; file inspection alone was sufficient.)

4. **Validate referenced targets/services exist.**  
   Check unit presence under common paths (`/etc/systemd`, `/lib/systemd`, `/usr/lib/systemd`) or enumerate known targets.  
   Treat non-existent dependency names as likely root cause.

5. **Produce output with exact required formatting.**  
   Write output using deterministic heredoc to avoid formatting drift:
   - `INCORRECT_LINE=<exact line as it appears>`
   - `CORRECT_LINE=<single corrected directive>`
   - `FILE_PATH=<path to faulty file>`

6. **Verify structure before finishing.**  
   Confirm exact line count and content with:
   - `wc -l <output>`
   - `cat -n <output>`

## Common Pitfalls
- **Depending on live `systemctl` introspection in non-systemd containers.**  
  In all three runs, `systemctl cat ssh` initially failed due to PID 1 not being systemd. Prevent failure by falling back to on-disk unit files immediately.

- **Not preserving the exact incorrect line text.**  
  Tests commonly require byte-accurate matching of the bad line from override config; paraphrasing fails even if diagnosis is conceptually right.

- **Correcting too much at once.**  
  Replace only the invalid dependency token(s) in the specific directive rather than rewriting the whole unit logic.

- **Formatting mistakes in solution artifact.**  
  Extra lines, missing keys, wrong key names, or wrong file path break grading even with correct diagnosis.

- **Assuming target validity without checking.**  
  Confirm whether suspicious targets actually exist; in observed runs, `network-ready.target` was absent and removing it produced the valid corrected line.

## Verification Strategy
- **Semantic verification**
  - Confirm the identified incorrect line exists verbatim in the drop-in.
  - Confirm corrected line uses valid directive syntax and references valid/expected targets only.
  - Confirm incorrect and correct lines are different.

- **Output-contract verification**
  - Ensure output file exists and is non-empty.
  - Ensure exactly 3 lines.
  - Ensure required keys are present exactly once:
    - `INCORRECT_LINE=...`
    - `CORRECT_LINE=...`
    - `FILE_PATH=...`

- **Practical checks**
  - Run `cat -n /root/solution.txt`
  - Run `wc -l /root/solution.txt`
  - Re-open source file and compare exact bad line text.

## References to Load On Demand
- `man systemd.unit`
- `man systemd.special`
- `man systemd.service`
- Distro unit directories: `/etc/systemd/system`, `/lib/systemd/system`, `/usr/lib/systemd/system`
```
