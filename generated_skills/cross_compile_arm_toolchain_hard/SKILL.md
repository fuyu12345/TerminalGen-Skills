---
name: cross-compiling-static-arm64-c-binaries
description: Build a statically linked ARM64 executable from C sources using a cross-toolchain and emit a verifier-friendly result file. Use when deploying x86-developed C tools to aarch64 targets with minimal runtime libraries.
---

# Cross-Compiling Static ARM64 C Binaries

## When to Use

- Cross-compiling a C CLI tool on x86_64 for ARM64/aarch64 devices.
- Producing a fully static binary (`-static`) for minimal target environments.
- Completing tasks that require a `result.txt` containing absolute binary path metadata.

## Minimal Reliable Workflow

1. Inspect project build inputs.
   - Run: `ls -la /path/to/project && sed -n '1,200p' Makefile`
   - Identify whether the build rule uses `$(CC) $(CFLAGS)` only, or also `$(LDFLAGS)`.

2. Clean and cross-compile with explicit static flags.
   - Prefer build-system override first:
     - `make clean || true`
     - `make CC=aarch64-linux-gnu-gcc CFLAGS='-O2 -static'`
   - If Makefile supports target override, set a distinct output name:
     - `make CC=aarch64-linux-gnu-gcc CFLAGS='-O2 -static' TARGET=mytool-arm64`
   - If no usable build system exists, compile directly:
     - `aarch64-linux-gnu-gcc -O2 -static -o mytool-arm64 *.c`

3. Resolve absolute path and enforce execute bit.
   - `chmod +x "$BIN"`
   - `ABS_BIN="$(readlink -f "$BIN")"`

4. Verify architecture.
   - `file "$ABS_BIN"` must include `ELF 64-bit` and `ARM aarch64`/`AArch64`.

5. Verify static linkage with multiple checks.
   - `file "$ABS_BIN"` should include `statically linked`.
   - `readelf -l "$ABS_BIN" | grep INTERP` should return nothing.
   - `ldd "$ABS_BIN" 2>&1` should mention `not a dynamic executable` or `statically linked`.

6. Write required output file exactly.
   - ```bash
     printf 'binary_path=%s\nstatic_linked=yes\n' "$ABS_BIN" > /workspace/result.txt
     ```

7. Re-open and sanity-check format.
   - `cat /workspace/result.txt`
   - Confirm exactly two lines, correct key names, absolute path.

## Common Pitfalls

- **Relying on `LDFLAGS=-static` when the Makefile never uses `$(LDFLAGS)`.**  
  In observed runs, the Makefile link rule used `$(CC) $(CFLAGS) -o ...`, so static linking only applied when `-static` was placed in `CFLAGS`.

- **Using only one static-link verification signal.**  
  `file` may say “statically linked,” but robust validation should also confirm no `INTERP` segment via `readelf`.

- **Misreading `ldd` in cross-arch contexts.**  
  For ARM64 binaries checked on x86 hosts, `ldd` diagnostics can appear on `stderr`; some test harnesses incorrectly inspect only `stdout`, causing false failures even when binary is truly static.

- **Formatting drift in `result.txt`.**  
  Extra spaces, wrong key names, relative paths, or extra lines can fail strict parsers.

## Verification Strategy

Run this exact sequence before finalizing:

```bash
BIN="/absolute/path/to/binary"

file "$BIN"
readelf -h "$BIN" | grep -E 'Class:|Machine:|Type:'
readelf -l "$BIN" | grep -E 'INTERP|Requesting program interpreter' || true
ldd "$BIN" 2>&1
test -x "$BIN" && echo "executable=yes"

cat /workspace/result.txt
```

Expected outcomes:

- `file`: ARM64 ELF executable, statically linked.
- `readelf -h`: `Machine: AArch64`, `Type: EXEC` (or valid executable type).
- `readelf -l`: no interpreter line.
- `ldd 2>&1`: contains static/non-dynamic message.
- `result.txt`: exactly:
  - `binary_path=/absolute/path/to/binary`
  - `static_linked=yes`

If harness still fails only the static-link test while all above pass, treat it as a harness stream-capture issue (stdout vs stderr), not a build issue.
