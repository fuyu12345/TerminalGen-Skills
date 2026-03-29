```markdown
---
name: debugging-super-resolution-training-convergence
description: Diagnose and fix non-converging image super-resolution training loops, including optimizer-order bugs, bad hyperparameters, and data/config blockers. Use when a training script runs or starts but fails to converge reliably in short CPU runs.
---

# Debugging Super-Resolution Training Convergence

## When to Use
- Training loss is flat/unstable despite no immediate crash.
- A task claims “exactly N training bugs,” but runtime also shows environment/data/config issues.
- Terminal automation is fragile (long-running commands, heredocs, newline-sensitive command batching).

## Minimal Reliable Workflow
1. **Establish clean execution context first.**
   - Run a single command per step for long jobs.
   - End every command with newline.
   - Wait for prompt return before sending the next edit/parse command.

2. **Baseline-read the script and capture first runtime failure.**
   - Inspect `train.py` and config.
   - Run training once to collect the *actual* blocking traceback before editing.

3. **Patch the canonical convergence triad first (most reusable fix set).**
   - Set practical LR (`1e-3`/`1e-4`, not extreme tiny values).
   - Enforce training step order:
     - `optimizer.zero_grad()`
     - forward
     - loss compute
     - `loss.backward()`
     - `optimizer.step()`
   - Confirm patch applied via `sed`/`grep` immediately after edit.

4. **Unblock runtime prerequisites if training cannot execute.**
   - If config is malformed type (e.g., list instead of dict), normalize or fallback safely.
   - If dataset files are unreadable/corrupted, regenerate valid image pairs or add robust loader handling.
   - Keep these as execution unblockers; do not confuse them with core convergence bugs unless task requires.

5. **Run full short training and capture logs.**
   - Use `python -u ... | tee train_run.log` for deterministic log capture.
   - Avoid appending parser commands while training is still running.

6. **Derive output artifact from logs, not assumptions.**
   - Parse epoch losses from `train_run.log`.
   - Compute `converged = (loss_epoch_10 < loss_epoch_1)`.
   - Write required `solution.json` schema exactly.

## Common Pitfalls
- **Brittle text replacement that silently fails.**  
  Observed repeatedly: exact multi-line replace missed due spacing/comment drift, leaving buggy order intact.
  - Guardrail: verify edited lines after each patch, not just “patched” printouts.

- **Command concatenation in interactive terminal.**  
  Observed in all runs: parser/heredoc commands got injected into active training process.
  - Guardrail: run long training alone; poll with empty command/wait until prompt returns.

- **Treating `C-c` as literal shell text.**  
  Observed: `bash: C-c: command not found`.
  - Guardrail: send control sequence in the executor’s expected format, not plain text.

- **Assuming only “3 bugs” matter operationally.**  
  Observed blockers: malformed `config.json`, unreadable `.png` dataset files.
  - Guardrail: separate “task-stated model bugs” from “runtime unblockers,” and handle both to get verifiable convergence.

- **Declaring convergence from partial run.**  
  Observed mid-run loss looked good, then later epochs worsened.
  - Guardrail: require epoch 1 and epoch 10 comparison from completed log.

## Verification Strategy
1. **Static verification of intended fixes**
   - Confirm LR value is practical.
   - Confirm loop order includes `zero_grad -> backward -> step` in correct positions.

2. **Runtime verification**
   - Complete full 10-epoch run.
   - Check for absence of NaN/Inf in logged losses.
   - Verify `loss_epoch_10 < loss_epoch_1`.

3. **Artifact verification**
   - `solution.json` exists and is valid JSON.
   - Exact fields: `bugs_fixed` (int), `final_loss` (float rounded to 4 decimals), `converged` (bool).
   - Ensure `final_loss` equals final logged epoch loss (rounded), not a guessed value.

## References to Load On Demand
- Robust patching patterns (line-based edits with post-edit diff checks).
- Safe long-running command orchestration in newline-sensitive terminal agents.
- Minimal image dataset regeneration snippet for corrupted SR training fixtures.
```
