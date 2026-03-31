---
name: hardening-gcc-builds-for-async-signal-safety
description: Add and validate compiler flags that disable unsafe red-zone stack usage in shared libraries. Use when C/C++ code is called from signal/interrupt-like asynchronous contexts and intermittent stack corruption appears.
---

# Hardening GCC Builds for Async Signal Safety

## When to Use
- Build artifacts are used inside signal handlers or interrupt-like async callbacks.
- Crashes suggest stack/local-variable corruption under asynchronous execution.
- x86_64 builds currently use normal optimization flags and may still use the red zone.
- Verification expects a specific hardening flag (commonly `-mno-red-zone`) and a rebuilt `.so`.

## Minimal Reliable Workflow
1. **Inspect current build flags before editing.**  
   Read the build file (`Makefile`, `CMakeLists.txt`, etc.) and identify where compile flags are set for the target library.

2. **Apply a minimal flag-only patch.**  
   Add `-mno-red-zone` to existing compile flags (for x86_64 async-signal safety) without rewriting recipe blocks.  
   Prefer in-place replacement (e.g., scripted replace of `CFLAGS` line) over full-file rewrite.

3. **Rebuild from clean state.**  
   Run `make clean && make` (or equivalent) to ensure the final `.so` actually reflects the new flags.

4. **Generate required task metadata/artifacts only after build succeeds.**  
   If required, write `solution.json` (or similar) with:
   - modified files
   - critical flag
   - built library path

5. **Run verifier and wait for full completion.**  
   Execute the provided verification script and do not inject additional commands while it is still running.

## Common Pitfalls
- **Breaking Makefile recipe indentation (`missing separator`).**  
  Seen in multiple runs when rewriting the whole `Makefile` via heredoc and losing tab-indented recipe lines.  
  Prevent by patching only `CFLAGS` (minimal edit), or deliberately using `.RECIPEPREFIX` if full rewrite is unavoidable.

- **Verifying before the library exists.**  
  Immediate failure occurs when `libcompute.so` was not rebuilt yet (`...libcompute.so not found`).

- **Assuming partial verifier output means done.**  
  Verifier output can pause at runtime test steps; wait/poll until final pass/fail banner appears.

- **Command interleaving during long-running verification.**  
  Sending new commands before previous process exits can cause typed text to be consumed unexpectedly and skip intended file creation (observed with missing `solution.json`).

## Verification Strategy
1. **Static build-config check**  
   Confirm the hardening flag exists in the active build config:
   - `grep -n "mno-red-zone" <build-file>`

2. **Clean rebuild check**  
   Ensure library rebuild succeeds:
   - `make clean && make`
   - verify target artifact path exists (`libcompute.so` or equivalent)

3. **Behavioral/verifier check**  
   Run the official verification script end-to-end and wait for completion:
   - `./verify.sh`
   - confirm final success text and exit code `0`

4. **Artifact/schema check (if required by task harness)**  
   Validate solution metadata file exists and is valid JSON with required keys and correct critical flag string.

## References to Load On Demand
- GNU Make recipe syntax (`missing separator` root cause and tab requirements)
- GCC x86_64 ABI red zone behavior and `-mno-red-zone`
- Signal-handler-safe coding/build considerations (async context constraints)
