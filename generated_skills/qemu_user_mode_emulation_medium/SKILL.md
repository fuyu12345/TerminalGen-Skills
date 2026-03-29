---
name: executing-obfuscated-python-write-capture-cross-arch
description: Execute obfuscated Python payloads in constrained cross-architecture environments and extract runtime write path/content reliably. Use when architecture/tooling constraints prevent straightforward tracing but dynamic execution is required.
---

# Executing Obfuscated Python Write Capture Cross-Arch

## When to Use

- Analyze a suspicious Python script that is said to be ARM-targeted but workstation is x86_64.
- Execute behavior dynamically (not static-only reversing) and extract:
  - file path written
  - exact content written
- Work in minimal containers where common tools may be missing (`file`, `strace` were missing in multiple runs).
- Need deterministic output in strict two-line format for graders/tests.

## Minimal Reliable Workflow

1. **Probe environment and run script once natively.**
   - Run:
     - `uname -m`
     - `which qemu-arm qemu-arm-static python3 || true`
     - `python3 /workspace/suspicious_script.py`
   - Rationale from runs: native execution may already succeed even if script mentions ARM (Run 2).

2. **Prefer dynamic instrumentation when visibility is poor.**
   - If no output, unknown write location, or no `strace`, execute via `runpy` harness and hook write APIs:
     - `builtins.open` (write modes)
     - optional: `pathlib.Path.write_text/write_bytes`, `os.open/os.write`
     - optional: force `platform.machine = lambda: "armv7l"` to satisfy arch checks.
   - This succeeded robustly in Runs 1 and 3 and did not require `strace` or ARM userspace.

3. **Record write events to a side log.**
   - Save captured events to `/workspace/runtime_writes.json` (or similar).
   - Select non-artifact target path (exclude own logs/result file).

4. **Read exact payload from discovered target file.**
   - `cat <discovered_path>` (or Python `open(...).read()`).
   - Prefer reading actual file content over reconstructed strings to avoid mismatch.

5. **Write required result file with exact schema.**
   - Create `/workspace/analysis_result.txt`:
     - `PATH: <absolute_path>`
     - `CONTENT: <exact_content>`

## Common Pitfalls

- **Assuming QEMU is mandatory before trying native execution.**
  - In Run 2, script executed directly because architecture check was non-blocking.
- **Relying on unavailable tools (`file`, `strace`).**
  - Runs showed both commands absent; instrumentation via Python hooks was the reliable fallback.
- **Using noisy filesystem scans as primary evidence.**
  - Broad `find / -mmin` output is noisy (`/proc` flood in Run 2). Use hook logs or direct target file checks.
- **Violating “must execute” constraint by static-only decoding.**
  - Even if source is readable, still execute script behavior dynamically.
- **Formatting errors in final output file.**
  - Tests require exact two labeled lines; avoid extra prefixes, swapped order, or missing labels.

## Verification Strategy

Run these checks before completion:

1. **Schema check**
   - Ensure `/workspace/analysis_result.txt` exists and is non-empty.
   - Ensure exactly two logical lines with prefixes:
     - line 1 starts `PATH: `
     - line 2 starts `CONTENT: `

2. **Value check**
   - Confirm `PATH` is absolute and points to the file actually written during execution.
   - Confirm `CONTENT` exactly matches file bytes/text written by script.

3. **Programmatic preflight (recommended)**
   - Use a short Python check:
     - parse `analysis_result.txt`
     - assert two lines and correct prefixes
     - compare `CONTENT` against `open(PATH).read()` when safe.

This mirrors the observed grader expectations (existence, two-line format, path validity, and exact path/content match).

## References to Load On Demand

- Python runtime instrumentation pattern:
  - `runpy.run_path(..., run_name="__main__")`
  - monkeypatch `platform.machine`, `open`, and optional `os.open/os.write`
- QEMU user-mode fallback:
  - use only when true ARM interpreter/binary is required and available.
