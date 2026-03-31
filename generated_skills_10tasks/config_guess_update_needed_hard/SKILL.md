---
name: updating-config-guess-architecture-support
description: Add new architecture mappings to simplified shell-based config.guess scripts while preserving existing behavior and executable state. Use when build/configure detection fails for a newly required CPU architecture.
---

# Updating Config Guess Architecture Support

## When to Use

Use this skill when a legacy `config.guess`-style shell script fails on a new architecture (for example, `riscv64`) and tests require:
- a new `case` branch output like `ARCH-unknown-linux-gnu`,
- backward compatibility for existing architectures,
- executable permissions preserved,
- and a captured output file for grading/automation.

## Minimal Reliable Workflow

1. **Inspect current script before editing.**  
   Run `sed -n '1,220p' path/to/config.guess` and confirm:
   - variable used in `case` (often `ARCH`),
   - existing architecture branches,
   - exact default `*)` error branch text/casing.

2. **Apply a deterministic edit to the `case` block.**  
   Prefer direct, explicit editing (or full-file rewrite for very small scripts) over fragile string substitutions.  
   Insert:
   ```sh
   riscv64)
       echo "riscv64-unknown-linux-gnu"
       ;;
   ```
   immediately before `*)`.

3. **Keep existing branches untouched.**  
   Preserve known working outputs (`x86_64`, `i686`, `armv7l`, `aarch64`) and default error handling.

4. **Ensure executability.**  
   Run `chmod +x path/to/config.guess` even if already executable.

5. **Validate new architecture path directly.**  
   Run:
   ```sh
   MOCK_ARCH=riscv64 path/to/config.guess
   ```
   Confirm stdout is exactly `riscv64-unknown-linux-gnu`.

6. **Write required artifact from stdout.**  
   Run:
   ```sh
   MOCK_ARCH=riscv64 path/to/config.guess > /workspace/result.txt
   ```

## Common Pitfalls

- **Using brittle text-replacement patches that depend on exact spacing/casing.**  
  Observed failures: replacement logic expected different indentation or `unsupported` vs `Unsupported`, so no edit occurred and `riscv64` still fell into `*)`.

- **Targeting the wrong symbol in automated edits.**  
  One failed patch searched for `case "$machine"` while script used `case "$ARCH"`, so insertion never happened.

- **Scripted edit errors masking as “successful execution.”**  
  A Python patch crashed (`replace expected at least 2 arguments`) and left file unchanged; subsequent commands still ran, giving false progress unless re-checked.

- **Not re-reading file after patching.**  
  Missing immediate `sed/nl` verification allowed silent patch failures to persist.

- **Assuming redirection captures failures.**  
  If script errors to `stderr`, `> result.txt` can produce an empty file (0 lines), which fails content checks.

## Verification Strategy

Use a layered verification sequence tied to observed failure modes:

1. **Structural verification (file content):**
   - `sed -n '1,220p' path/to/config.guess`
   - Confirm `riscv64)` branch exists and is inside correct `case`.

2. **Behavior verification (stdout/stderr):**
   - `MOCK_ARCH=riscv64 path/to/config.guess`
   - Must print `riscv64-unknown-linux-gnu` on stdout, not error on stderr.

3. **Regression verification for existing architectures:**
   - `MOCK_ARCH=x86_64 path/to/config.guess`
   - `MOCK_ARCH=aarch64 path/to/config.guess`
   - Ensure prior outputs unchanged.

4. **Artifact verification (grading file):**
   - `MOCK_ARCH=riscv64 path/to/config.guess > /workspace/result.txt`
   - `wc -l /workspace/result.txt` must be `1`
   - `cat /workspace/result.txt` must match exactly.

5. **Permission verification:**
   - `test -x path/to/config.guess && echo executable`

All three runs ultimately passed this pattern; the most reliable approach was explicit case insertion/full rewrite plus immediate behavioral checks, not pattern-fragile auto-patching.
