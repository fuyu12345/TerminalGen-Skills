---
name: fixing-cpp-batch-memory-leaks-with-verifier-contract
description: Diagnose and fix per-iteration C++ heap leaks while preserving build/test contract and emitting required metadata files. Use when batch processing memory grows across inputs and graders require compile/run plus structured solution output.
---

# Fixing C++ Batch Memory Leaks with Verifier Contract

## When to Use
- Investigating a C/C++ utility that processes many files and shows rising memory usage across iterations.
- Fixing `new`/`new[]` allocations that are not released in per-file/per-iteration code paths.
- Completing terminal-bench style tasks that also require:
  - successful compile,
  - successful batch script completion,
  - required `solution.json` metadata with file/line/fixed fields.

## Minimal Reliable Workflow
1. **Inspect execution path before editing.**  
   Read `run_batch.sh`, `Makefile`, and all source files (`nl -ba src/*.cpp` or per-file views).

2. **Identify true leak sites in hot path.**  
   Prioritize allocations inside per-file functions (e.g., `char* workBuffer = new ...`, `char* resultBuffer = new ...`) that lack matching `delete[]`.  
   In all runs, the primary leak pattern was exactly this in `processFile()`.

3. **Apply minimal, local fix first.**  
   Add matching deallocation in same scope:
   - `delete[] workBuffer;`
   - `delete[] resultBuffer;`
   Optionally clean one-time globals (`delete globalConfig`) for hygiene.

4. **Restore buildability if repository is inconsistent.**  
   Do not trust prompt claims blindly (“working Makefile”).  
   In all runs, compile initially failed due missing headers (`processor.h`, `utils.h`).  
   Create minimal headers matching actual `.cpp` signatures to unblock build.

5. **Rebuild cleanly.**  
   Run `make clean && make` and resolve *all* compiler errors before batch validation.

6. **Run batch script in isolation.**  
   Run `./run_batch.sh` alone; wait for completion before sending new commands.

7. **Write required metadata file only after final line numbers are known.**  
   Use `nl -ba` to confirm line number and then create:
   ```json
   {
     "file": "src/main.cpp",
     "line": <verified_line>,
     "fixed": true
   }
   ```

## Common Pitfalls
- **Trusting task text over terminal reality.**  
  All runs showed missing headers despite “working Makefile” claim. Treat compiler output as source of truth.

- **Fixing leak but ignoring compile blockers.**  
  Memory fix alone is insufficient if `make` fails; grader checks both compile and batch completion.

- **Over-editing headers with wrong declarations/namespaces.**  
  One run introduced mismatched `utils.h` declarations (`namespace Utils` API that did not match `utils.cpp`), causing new errors (e.g., `trim` undeclared). Keep declarations aligned to current implementation.

- **Command stream interference during long-running script.**  
  Multiple runs injected follow-up commands while `run_batch.sh` was still running, producing corrupted output like:
  `Memory usage: cat /workspace/solution.json`.  
  Wait/poll instead of stacking commands.

- **Incorrect control key usage.**  
  Sending literal `C-c\n` can become shell text (`bash: C-c: command not found`). Use proper interrupt keystroke format for the environment/tool.

- **Stale or invalid `solution.json` line number.**  
  Line changed across edits (e.g., 104/106/68 observed). Re-read numbered file after final edits and only then write JSON.

## Verification Strategy
1. **Compile gate**
   - `make clean && make`
   - Require zero compiler errors.

2. **Batch gate**
   - Run `./run_batch.sh`.
   - Confirm all five inputs are processed (`Processing input file 1...` through `5...`).
   - Confirm terminal ends with `Batch processing complete.`

3. **Leak-fix gate (code inspection)**
   - Confirm each `new[]` in per-file path has matching `delete[]` on normal exit path.
   - Confirm no accidental removal of required logic.

4. **Metadata gate**
   - `cat /workspace/solution.json`
   - Validate exactly fields: `file` (string), `line` (int), `fixed` (bool true).
   - Ensure `file` path is relative to project root and `line` exists in file.

## References to Load On Demand
- Quick inspection commands:
  - `nl -ba src/main.cpp`
  - `nl -ba src/processor.cpp`
  - `nl -ba src/utils.cpp`
- Build and run:
  - `make clean && make`
  - `./run_batch.sh`
- Metadata emit:
  - heredoc write to `/workspace/solution.json` after final `nl -ba` check.
