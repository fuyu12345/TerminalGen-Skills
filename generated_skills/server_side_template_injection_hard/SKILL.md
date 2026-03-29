---
name: hardening-flask-ssti-with-sandboxed-jinja
description: Harden Flask SSTI-prone rendering by using a sandboxed Jinja environment with fixed templates and explicit context variables. Use when patching user-influenced template output while preserving legitimate substitution and satisfying security-oriented tests.
---

# Hardening Flask SSTI with Sandboxed Jinja

## When to Use
- Patching Flask endpoints that call `render_template_string` on strings influenced by request data.
- Blocking known Jinja SSTI payloads (`__class__`, `__globals__`, `__import__`, etc.) without breaking normal rendering.
- Completing terminal tasks that require both runtime exploit blocking and code-level security signals (e.g., sandbox import/config checks).

## Minimal Reliable Workflow
1. **Inspect vulnerability and test expectations first**
   - Read `app.py`, exploit payload file, and test file(s).
   - Confirm whether tests require explicit mitigation markers (e.g., `SandboxedEnvironment`, `autoescape=True`).

2. **Replace vulnerable rendering pattern**
   - Remove user-data interpolation into template source (no f-string HTML with request fields).
   - Define a **fixed template string** with placeholders.
   - Import and initialize sandboxed Jinja:
     - `from jinja2.sandbox import SandboxedEnvironment`
     - `SandboxedEnvironment(autoescape=True)` (or equivalent explicit autoescape setup).
   - Render by passing user input only as context values.

3. **Keep legitimate behavior intact**
   - Preserve expected variables like `customer_name`, `feedback_text`, `feedback_date`, `email`.
   - Keep route contracts and response structure stable.

4. **Run syntax + app startup checks**
   - `python3 -m py_compile app.py`
   - Start Flask and confirm listening.

5. **Replay exploits using Python requests**
   - Do not assume `curl` exists.
   - Submit all payloads from `exploits.txt`.
   - Check response body for execution indicators (`uid=`, `/etc/passwd`, `root:x:`).

6. **Run legitimate functionality test script**
   - Ensure app is already running before `test_legitimate.py`.

7. **Write required deliverable exactly (if requested)**
   - Example:
     ```
     FIXED=yes
     METHOD=sandboxing
     ```

## Common Pitfalls
- **Using static template + `render_template_string` without sandbox markers**  
  - Even if runtime behavior seems safe, security tests may fail on code-policy assertions (observed failure: missing `SandboxedEnvironment`/security import and `render_template_string` policy checks).
- **Claiming exploit blocking from missing tooling**  
  - `curl: command not found` produced misleading “blocked” output in one run; use Python-based checks instead.
- **Running functionality tests before starting Flask**  
  - `test_legitimate.py` can fail only because server is down, not due to patch quality.
- **Sending malformed command batches**  
  - Missing trailing newline caused command concatenation warning; end each command with newline in terminal-bench style execution.

## Verification Strategy
1. **Static/code-policy verification**
   - Confirm presence of sandbox/security primitives in source (`jinja2.sandbox`, `SandboxedEnvironment`, and/or explicit `autoescape`).
   - Confirm no user input is embedded into template source construction.

2. **Exploit regression verification**
   - Programmatically iterate all provided payloads and POST them into relevant fields.
   - Assert HTTP success + absence of command-execution artifacts in response text.

3. **Legitimate behavior verification**
   - Run provided legitimate test suite (`python3 test_legitimate.py`) with Flask running.
   - Verify substitutions still appear for normal inputs and date remains rendered.

4. **Final grader-aligned verification**
   - Run official tests (`pytest ...`) when available.
   - Re-check deliverable file format exactly (line content/order/casing).

## References to Load On Demand
- Jinja2 sandbox docs (`jinja2.sandbox.SandboxedEnvironment`)
- Flask templating safety guidance
- SSTI payload taxonomy and detection patterns
