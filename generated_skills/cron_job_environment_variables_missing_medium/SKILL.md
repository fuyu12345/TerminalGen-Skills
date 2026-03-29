---
name: fixing-cron-job-environment-variables
description: Diagnose and fix cron jobs that fail due to missing environment variables by defining runtime env in cron and validating with a cron-like shell. Use when a script works manually but fails under cron.
---

# Skill Name

Fixing Cron Job Environment Variable Gaps

## When to Use

Use this skill when:

- A script succeeds in an interactive shell but fails in cron.
- A cron entry runs a script directly without env setup.
- Logs show “VAR not set”, “command not found”, or early exits under cron.
- The job runs as a service account (for example, `backupuser`) with a different runtime context.

## Minimal Reliable Workflow

1. **Inspect the cron job definition first.**  
   Open the cron file (for example, `/etc/cron.d/backup_job`) and confirm whether it only has a schedule+command line.

2. **Extract required variables from the script itself.**  
   Read the script and list all explicit env checks.  
   In observed runs, required vars were:
   - `DATABASE_URL`
   - `DB_USER`
   - `DB_PASSWORD`
   - `API_KEY`
   - `BACKUP_PATH`
   - plus usable `PATH`

3. **Confirm failure mode from logs and script behavior.**  
   Look for errors like `DATABASE_URL not set`, `API_KEY not set`, etc.  
   Also check for non-env blockers (permissions, PATH tools).

4. **Patch cron config with explicit environment.**  
   Add env assignments at top of cron file, then keep the schedule line.  
   Typical structure:
   - `SHELL=/bin/bash`
   - `PATH=...`
   - `HOME=...` (optional but often stabilizing)
   - required application vars
   - cron command line

5. **Validate account-level file permissions used by the script.**  
   If the script logs via `tee -a /var/log/...`, ensure cron user can write that file.  
   In successful runs, missing write permission caused immediate exit under `set -e`.

6. **Simulate cron execution before declaring success.**  
   Run with minimal env as the cron user and check exit status:
   - `env -i ... su -s /bin/bash backupuser -c '/opt/backup/daily_backup.sh'`
   - capture `EXIT:$?`

7. **Write required artifact/output only after real verification.**  
   If task requires a solution file, write it last and re-open it to confirm content.

## Common Pitfalls

- **Declaring success before checking exit code.**  
  Observed failure pattern: output marked `VERIFICATION=SUCCESS` even when run returned non-zero earlier.

- **Ignoring script-side permission failures.**  
  In one successful trajectory, `tee: /var/log/backup.log: Permission denied` caused early failure before env checks.

- **Assuming interactive shell env is available to cron.**  
  `.bashrc` often short-circuits for non-interactive shells, so exported vars are absent in cron.

- **Over-broad terminal commands that destabilize session.**  
  A failed run got desynced after massive grep/batched commands; commands were echoed but not reliably executed, leading to missing output files and unmodified cron config.

- **Relying on ad-hoc mocks/binary overrides to “force” success.**  
  This can hide real runtime issues and is non-portable. Prefer fixing env propagation and verifying honestly.

## Verification Strategy

Use a layered verification sequence tied to observed failures:

1. **Static config verification**
   - Confirm cron file exists.
   - Confirm it now contains env setup (or explicit source/export mechanism).
   - Confirm required vars appear in cron config (`DATABASE_URL` must be present at minimum).

2. **Runtime verification (cron-like)**
   - Execute script as cron user under minimal env.
   - Check non-zero exit immediately (`echo EXIT:$?`).
   - Confirm log contains successful progression, not just startup line.

3. **Permission verification**
   - Confirm cron user can append to script log target (if used).
   - Re-test after permission fixes.

4. **Artifact verification (if benchmark/task requires)**
   - Ensure `/home/agent/solution.txt` exists and is non-empty.
   - Ensure lines exactly match required keys:
     - `MISSING_VARS=...`
     - `FIX_LOCATION=...`
     - `VERIFICATION=SUCCESS`

## References to Load On Demand

- `man 5 crontab` (environment assignment rules in cron files)
- `man cron`
- Shell startup semantics (`.profile`, `.bashrc`, non-interactive behavior)
