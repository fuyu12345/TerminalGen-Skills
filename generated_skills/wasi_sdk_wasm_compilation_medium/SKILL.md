---
name: compiling-wasi-wasm-with-size-and-artifact-validation
description: Compile C sources to WASI WebAssembly, enforce strict size limits, and generate deployment/result metadata with portable validation commands. Use when producing `.wasm` artifacts in terminal tasks that require path/status confirmation files.
---

# Compiling WASI WASM with Size and Artifact Validation

## When to Use
- Building a C program into a WASI-compatible `.wasm` using an installed WASI SDK.
- Meeting hard artifact constraints (for example, `<50KB`).
- Producing a companion result file (for example, `path=...` and `valid=yes|no`).
- Working in minimal containers where common tools like `xxd` may be missing.

## Minimal Reliable Workflow
1. **Confirm inputs and toolchain paths.**
   - Check source file and compiler:
     - `ls -l /workspace/app/main.c /opt/wasi-sdk/bin/clang`

2. **Compile with size-focused flags first.**
   - Start with:
     - `/opt/wasi-sdk/bin/clang --target=wasm32-wasi -Oz -Wl,--strip-all -o /workspace/app/output.wasm /workspace/app/main.c`
   - If environment requires explicit sysroot, add:
     - `--sysroot=/opt/wasi-sdk/share/wasi-sysroot`
   - If still too large, add stronger reductions:
     - `-ffunction-sections -fdata-sections -Wl,--gc-sections -flto`

3. **Validate artifact using portable tools (`od`, `stat`, `wc`) instead of `xxd`.**
   - Magic bytes:
     - `od -An -t x1 -N 4 /workspace/app/output.wasm | tr -d ' \n'` → expect `0061736d`
   - Size:
     - `stat -c%s /workspace/app/output.wasm` (or `wc -c < ...`) and compare with limit.

4. **Write deterministic result file in exact required format.**
   - Emit exactly:
     ```
     path=/workspace/app/output.wasm
     valid=yes
     ```
   - Write `valid=no` if any check fails.

5. **Print final state before completion.**
   - Show artifact size, magic check output, and `cat /workspace/result.txt`.

## Common Pitfalls
- **Using unavailable utilities (`xxd`) for validation.**  
  Evidence: all three runs hit `bash: xxd: command not found`.  
  Prevention: standardize on `od` (or `hexdump`) in all checks.

- **Compiling with insufficient size optimization.**  
  Evidence: one run produced `146264` bytes (fails `<50KB`) with `-Os` and no strip/GC.  
  Prevention: include linker stripping (`-Wl,--strip-all`) and prefer `-Oz`; escalate to GC sections/LTO if needed.

- **Marking completion before fixing validation logic.**  
  Evidence: initial command batches produced wasm successfully but wrote incorrect `valid=no` due to failed magic-byte check command.  
  Prevention: always re-run validation and overwrite result file after any command/tool failure.

- **Overfitting to one environment assumption (implicit sysroot/tool defaults).**  
  Evidence: successful runs differed (`--sysroot` present/absent) but both passed.  
  Prevention: keep sysroot configurable; verify outcome via artifact checks rather than assumptions.

## Verification Strategy
Tie checks directly to observed test expectations (`exists`, `not empty`, `magic bytes`, `version`, `size`, `result format`, `valid status`, binary nature):

1. **Existence + non-empty**
   - `[ -s /workspace/app/output.wasm ]`

2. **WASM signature (magic + version)**
   - `od -An -t x1 -N 8 /workspace/app/output.wasm | tr -d ' \n'`
   - Expect prefix: `0061736d01000000`

3. **Size constraint**
   - `size=$(stat -c%s /workspace/app/output.wasm)` and assert `< 51200`

4. **Result file correctness**
   - Ensure exactly two lines and exact keys:
     - `path=/workspace/app/output.wasm`
     - `valid=yes` (or `no` on failure)

5. **Final sanity print**
   - `ls -l /workspace/app/output.wasm /workspace/result.txt`
   - `cat /workspace/result.txt`

## References to Load On Demand
- WASI SDK clang usage (`--target=wasm32-wasi`, `--sysroot`)
- LLVM size optimization flags (`-Oz`, `--strip-all`, `--gc-sections`, LTO)
- WASM binary header format (`\0asm` + version `0x01 00 00 00`)
