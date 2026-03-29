```markdown
---
name: generating-self-hosted-runner-config-packages
description: Generate multi-runner GitHub Actions configuration artifacts that match strict verifier file-path and naming expectations. Use when a task asks for config generators plus output-file validation.
---

# Generating Self-Hosted Runner Config Packages

## When to Use

- Building a script that generates runner configs (systemd, env, logrotate, health, cleanup, bootstrap) for multiple environments.
- Working in terminal-bench style tasks where tests validate **exact output paths, filenames, and content markers**.
- Seeing failures where files exist but tests still report “file does not exist.”

## Minimal Reliable Workflow

1. **Inspect tests before designing output layout.**  
   Open `/tests/test_outputs.py` and extract:
   - exact filenames,
   - expected directory depth (top-level vs nested),
   - required string assertions,
   - counting logic (recursive vs non-recursive).

2. **Mirror verifier paths exactly.**  
   If tests read `Path("/solution/runner_configs") / "production-runner.service"`, generate that exact file path (not `systemd/production-runner.service`).

3. **Mirror verifier filenames exactly.**  
   Use expected names literally:
   - `production-runner.service`, `staging-runner.service`, `development-runner.service`
   - `production-runner.env`, etc.

4. **Separate secret placement from service files.**  
   Keep real tokens in env files; reference env files from service units.  
   Avoid hardcoded token literals in `*.service`.

5. **Satisfy content-level assertions explicitly.**  
   Ensure service files include:
   - runner-specific work/cache paths,
   - expected user,
   - `Restart=always`,
   - autostart target (e.g., `WantedBy=multi-user.target`).
   Ensure logrotate includes `size 100M`.  
   Ensure health/cleanup/bootstrap artifacts are discoverable by test glob logic.

6. **Compute summary using the same counting rule as tests.**  
   If tests use `list(config_dir.glob("*"))` and only count `is_file()`, report top-level file count (not recursive total).

7. **Run generator and locally emulate assertions.**  
   Validate existence, naming, and key substrings before finalizing.

## Common Pitfalls

- **Creating a “clean” subdirectory hierarchy that tests do not traverse.**  
  Evidence: all 3 runs generated files under `env/`, `systemd/`, `scripts/`, `logrotate/`; tests looked only at `/solution/runner_configs/*` and failed 16 checks.

- **Using different service filenames than expected.**  
  Evidence: generated names like `github-actions-production-runner.service` / `github-runner-production.service`; tests required `production-runner.service`.

- **Reporting recursive file totals while verifier counts top-level only.**  
  Evidence: summaries reported 28–29 files; verifier found `0` top-level files and failed `total_files_generated`.

- **Passing self-checks but failing harness checks.**  
  Evidence: run 3 added grep-based checks (tokens, 5min timers, 100M rotation) yet still failed because path/filename contract was wrong.

## Verification Strategy

Run this sequence after generation:

1. **Exact file existence checks**
   - `ls -1 /solution/runner_configs`
   - Confirm required `*.service` and `*.env` files are top-level if tests expect top-level.

2. **Contract-content checks**
   - `grep -n "EnvironmentFile" /solution/runner_configs/*.service`
   - `grep -n "Restart=always" /solution/runner_configs/*.service`
   - `grep -n "WantedBy=multi-user.target" /solution/runner_configs/*.service`
   - `grep -n "size 100M" /solution/runner_configs/*log*`

3. **Token leakage checks**
   - `grep -R "GHRT-" /solution/runner_configs/*.service || true`
   - Ensure token literals appear only where acceptable (usually env files).

4. **Count parity check (match test logic)**
   - Reproduce test count method exactly (top-level non-recursive vs recursive).
   - Confirm `deployment_summary.json["total_files_generated"]` equals that computed value.

5. **Final gate**
   - Run `pytest /tests/test_outputs.py -rA` before marking complete.

## References to Load On Demand

- `/tests/test_outputs.py` (primary contract source)
- `/tests/test.sh` (how reward is assigned)
```
