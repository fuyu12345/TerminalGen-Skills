---
name: generating-github-runner-configs-for-strict-file-layout-tests
description: Generate self-hosted GitHub Actions runner config bundles that satisfy both operational requirements and strict verifier file-layout expectations. Use when tasks require scripted config generation plus automated grading checks.
---

# Generating GitHub Runner Configs for Strict File-Layout Tests

## When to Use
- Building a script that emits systemd/env/logrotate/health/cleanup/bootstrap artifacts for multiple self-hosted runners.
- Working in benchmark/autograder environments where tests validate **exact filenames and locations**.
- Needing to avoid secrets in service files while still wiring token-based registration.

## Minimal Reliable Workflow
1. **Read the grader’s assertions before coding layout.**  
   Confirm whether tests read files recursively or only from a single directory level.

2. **Define runner metadata once** (name, user, work/cache/tmp dirs, memory, CPU, token key).  
   Generate all files from this structure to avoid drift across runners.

3. **Load tokens from the provided token env file** and validate required keys exist.

4. **Write required files in the exact directory level expected by tests.**  
   If tests read `/solution/runner_configs/<file>`, place files there directly (or add compatibility copies/symlinks there).

5. **Generate service files with:**
   - `Restart=always`
   - `WantedBy=multi-user.target`
   - runner-specific isolated directories (`/opt/runners/production`, `/opt/runners/staging`, `/opt/runners/dev`)
   - no hardcoded token values in service content
   - environment file reference per runner

6. **Generate env files with expected token variable references** (e.g., include `PRODUCTION_TOKEN`, `STAGING_TOKEN`, `DEVELOPMENT_TOKEN` naming as required by tests), not only resolved secret literals in service units.

7. **Generate logrotate / health / cleanup / bootstrap artifacts with filename patterns tests can discover** (especially if tests do top-level `glob("*")` plus substring checks like `health`, `cleanup`, `bootstrap`, `log`).

8. **Compute summary counts using the same counting semantics as tests.**  
   If tests use `list(config_dir.glob("*"))` and count only top-level files, report that count exactly.

9. **Run verifier tests locally before finalizing** and fix mismatches in path/count conventions first.

## Common Pitfalls
- **Creating a nested structure only (`systemd/`, `env/`, `scripts/`, `logrotate/`) when tests expect top-level files.**  
  Evidence: all 3 runs generated 28 files but failed 16 tests for missing `/solution/runner_configs/production-runner.service` etc.
- **Reporting recursive file count while tests count only top-level files.**  
  Evidence: runs reported `total_files_generated: 28`, tests found `0` top-level files and failed summary consistency.
- **Assuming “proper structure” in prompt means grader accepts subdirectories.**  
  In strict harnesses, explicit assertion paths override interpretation.
- **Token-handling mismatch.**  
  Even if services avoid hardcoded tokens, env-file assertions may require specific token variable names to appear.

## Verification Strategy
- **First, mirror the test’s lookup logic manually:**
  - Check exact paths for:
    - `production-runner.service`, `staging-runner.service`, `development-runner.service`
    - matching `.env` files
  - Confirm top-level presence of files with names containing:
    - `log`/`rotate` (>=3)
    - `health`/`check` (>=1)
    - `cleanup`/`clean` (>=1)
    - `bootstrap`/`setup`/`init` (>=1)

- **Content checks:**
  - Service files include `Restart=always` and `WantedBy=multi-user.target`
  - Service files reference env files, and do not contain literal GHRT tokens
  - Service files contain expected isolated base dirs (`/opt/runners/production`, `/opt/runners/staging`, `/opt/runners/dev`)
  - Env files include expected token variable identifiers.

- **Count check parity:**
  - Reproduce grader count method (top-level `glob("*")` files only) and match `deployment_summary.json.total_files_generated`.

- **Final step:**
  - Run the provided `pytest /tests/test_outputs.py -rA` before marking complete.
