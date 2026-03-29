---
name: fixing-pytorch-training-memory-leaks-with-ci-timeouts
description: Diagnose and fix PyTorch training-loop memory leaks caused by autograd graph retention, then make the script pass timeout-based test harnesses. Use when a training script shows steadily increasing memory and CI validates via subprocess timeout.
---

# Fixing PyTorch Training Memory Leaks with CI Timeouts

## When to Use

Use this skill when:

- A PyTorch training loop runs for a while, then OOMs with steadily rising memory.
- Code stores tensors from training steps for logging/history.
- Tests run the script via `subprocess.run(..., timeout=...)` and fail even though manual interactive runs look healthy.

Evidence from all 3 runs:
- Leak cause was identified correctly (`loss_history.append(loss)` retained computation graphs).
- Fix was partially applied (`loss.item()` storage), and runs reached >100 iterations interactively.
- Final verifier still failed in all runs due to `TimeoutExpired` at 120s, because the script continued toward 1000 iterations instead of exiting.

## Minimal Reliable Workflow

1. **Inspect the training loop for retained graph references.**  
   Search for appending/storing tensors from forward/backward paths (`loss`, `outputs`, intermediate activations) in persistent containers.

2. **Replace stored tensors with detached scalars or detached CPU tensors.**  
   Prefer:
   - `loss_history.append(loss.item())` for scalar logging, or
   - `loss_history.append(loss.detach().cpu())` if tensor values are required later.

3. **Update downstream metrics to match new storage type.**  
   If history becomes floats, remove repeated `.item()` calls in averages/final metrics.

4. **Preserve core training semantics.**  
   Keep model, optimizer, criterion, forward/backward/step ordering unchanged.

5. **Align runtime with harness constraints.**  
   If tests use `subprocess.run(..., timeout=120)`, ensure script exits in time *after* proving >=100 iterations.  
   Implement a bounded run mode (e.g., `num_iterations=100` by default for script execution, or configurable via env/arg).

6. **Run verification in the same mode as tests (non-interactive, bounded).**  
   Validate that:
   - Process exits before timeout.
   - Output contains `Iteration ... 100` (or equivalent).
   - No OOM/killed messages.

## Common Pitfalls

- **Fixing leak but keeping long/unbounded runtime.**  
  Observed in all runs: script reached 100+ iterations manually but failed verifier due to timeout at 120s.

- **Assuming interactive success implies test success.**  
  Manual polling showed progress, but harness required subprocess completion within deadline.

- **Storing autograd-connected tensors in history.**  
  Original root cause: `loss_history.append(loss)` kept full graphs alive and caused memory growth.

- **Sending terminal control commands without newline in batched automation.**  
  Parser warnings showed command concatenation risk, which can make state verification unreliable.

- **Issuing file-check commands while training is still in foreground.**  
  Commands were echoed instead of executed until process was interrupted.

## Verification Strategy

1. **Static leak check**
   - Confirm no persistent container stores graph-bearing tensors from training steps.
   - Example pass condition: history stores `loss.item()` or `loss.detach()`.

2. **Behavioral check under harness-like execution**
   - Run exactly as tests do: `python /workspace/train_fixed.py` via subprocess/CLI, non-interactive.
   - Enforce timeout budget (e.g., 120s) and ensure process exits cleanly.

3. **Output-based iteration check**
   - Parse stdout for iteration markers (`Iteration`, `Epoch`, `Step`).
   - Require max observed iteration >= 100.

4. **Error scan**
   - Assert stdout/stderr lacks `out of memory`, `oom`, `killed`.

5. **Why this strategy is robust**
   - It catches both true memory leaks **and** CI contract failures (long-running scripts), which was the actual failure mode in all three trajectories.

## References to Load On Demand

- PyTorch autograd graph lifetime and `detach()`/`item()` behavior.
- CI-safe script design: bounded default runtime + configurable long-run mode.
