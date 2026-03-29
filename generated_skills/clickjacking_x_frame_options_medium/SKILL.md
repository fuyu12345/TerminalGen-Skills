```yaml
---
name: hardening-flask-clickjacking-x-frame-options
description: Add global clickjacking protection to Flask by injecting an after_request X-Frame-Options header via a fixer script. Use when a task requires patching an existing Flask app from the terminal while preserving routes and covering error responses.
---
```

# Hardening Flask Clickjacking with X-Frame-Options

## When to Use

- Patch an existing Flask app to prevent iframe embedding (`X-Frame-Options: DENY` or equivalent).
- Deliver a **scripted** fix (e.g., `/tmp/fix_clickjacking.py`) that edits `app.py`.
- Ensure protection applies to both normal and error responses.
- Work in noisy environments where:
  - `app.py` may already be corrupted by prior attempts,
  - `curl` may be unavailable,
  - Flask `test_client()` may fail due dependency mismatch.

## Minimal Reliable Workflow

1. **Inspect current `app.py` before writing any patch logic.**  
   Detect whether it is a real Flask app or a previously written self-modifying script.

2. **Create a fixer script that performs structural checks, not string-only checks.**  
   Require Flask app indicators (for example: Flask import + `app = Flask(...)`) before deciding “already fixed.”

3. **Inject clickjacking protection with `@app.after_request`.**  
   Add a handler that sets:
   - `response.headers['X-Frame-Options'] = 'DENY'`
   - returns `response`  
   Insert immediately after app initialization for clarity and repeatability.

4. **Make the fixer idempotent safely.**  
   Skip modification only when both decorator and header logic already exist in valid Flask code.  
   Avoid naive checks like “`X-Frame-Options` exists anywhere in file.”

5. **If file is not a valid Flask app, restore baseline app first, then apply protection.**  
   This was necessary in multiple runs because `app.py` contained a script, not routes.

6. **Execute fixer script and re-open `app.py` to confirm exact resulting code.**

7. **Run runtime verification using tools available in environment.**  
   Prefer standard-library HTTP checks (`urllib`) against a running server if `curl` is missing or `test_client()` breaks.

## Common Pitfalls

- **False idempotency success** from marker-only checks.  
  Observed failure mode: fixer exited “already present” because header strings existed inside a broken script, leaving app unusable.

- **Assuming `app.py` is baseline Flask code.**  
  In all runs, initial `app.py` was already replaced by a script and could not export `app`.

- **Relying only on `flask.test_client()` in unstable dependency environments.**  
  Observed `werkzeug.__version__` AttributeError blocked this path despite correct app logic.

- **Relying only on `curl`.**  
  Observed “`curl: command not found`”; verification must have fallback.

- **Treating harness import errors as task failure root cause.**  
  All three grader runs failed at test collection with missing `requests` in `/tests/test_outputs.py`; this is harness-side and not evidence of incorrect clickjacking fix.

## Verification Strategy

1. **Static verification (file-level):**
   - Confirm `/tmp/fix_clickjacking.py` exists and runs with `python /tmp/fix_clickjacking.py`.
   - Confirm `app.py` contains:
     - `@app.after_request`
     - `X-Frame-Options`
     - original routes (`/`, `/api/status`, `/admin`).

2. **Runtime verification (HTTP-level):**
   - Start app without reloader in background (`import app; app.app.run(...)`).
   - Query:
     - `/`
     - `/api/status`
     - `/admin`
     - non-existent path (expect 404)
   - Assert `X-Frame-Options: DENY` appears on **all** responses, including 404.

3. **Environment-resilient verification fallback order:**
   - First choice: `urllib` (stdlib).
   - Optional: `curl` if installed.
   - Avoid blocking on `test_client()` if Werkzeug/Flask mismatch appears.

4. **Harness sanity check:**
   - If grader fails before tests run (e.g., `ModuleNotFoundError: requests` during collection), classify as test-environment issue and rely on direct runtime verification evidence for task correctness.
