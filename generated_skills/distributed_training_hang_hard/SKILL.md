---
name: diagnosing-ddp-hangs-from-mismatched-collectives
description: Identify root-cause deadlocks in PyTorch DDP by tracing rank participation in collective ops and synchronization points. Use when distributed jobs initialize successfully but stall before/early in training with no explicit error.
---

# Diagnosing DDP Hangs from Mismatched Collectives

## When to Use
- Process group initialization succeeds on all ranks, then training stalls.
- No exception is raised, but workers become idle.
- Recent code changes added rank-conditional logic near barriers/collectives.
- Need to report exact file:line root cause (not just a symptom).

## Minimal Reliable Workflow
1. **Inspect training entrypoint and data path with line numbers.**  
   Use `nl -ba` on main trainer and data utilities to anchor exact line reporting.
2. **Search for collective/sync APIs and rank-conditional branches.**  
   Grep for `barrier`, `all_reduce`, `broadcast`, `gather`, `if rank`, `DistributedSampler`, `set_epoch`, `drop_last`.
3. **Validate collective participation invariant.**  
   For every collective call, verify all ranks reach it in the same control flow.  
   - Flag patterns like:
     - `if rank == 0: dist.barrier()` (deadlock)
     - Barrier/collective inside uneven loop bodies
4. **Prioritize the earliest blocking point in execution order.**  
   If hang occurs before first training logs, focus on pre-loop sync points (post-init, pre-dataloader/train loop).
5. **Write concise root-cause output with exact location.**  
   Format as:
   - Line 1: `/path/to/file.py:<line>`
   - Line 2: one-sentence technical cause (short, specific).

## Common Pitfalls
- **Treating rank-conditional barrier as harmless logging sync.**  
  Evidence across all 3 runs: `train_ddp.py:58` had `dist.barrier()` inside `if rank == 0`, which is a guaranteed deadlock because only one rank enters.
- **Over-focusing on dataloader complexity before checking collectives.**  
  DistributedSampler issues can hang later, but an earlier mismatched barrier blocks first and is primary root cause.
- **Reporting a general file-level issue without exact line.**  
  Verification required precise `file:line`; vague answers fail strict checks.
- **Confusing test-induced mismatch with real task issue.**  
  Here, tests consistently matched task requirements (all runs passed with same root-cause line), so no harness anomaly.

## Verification Strategy
- **Static correctness check:** confirm collective-call symmetry by control-flow inspection.
- **Execution-order check:** ensure identified line occurs before first stalled phase (e.g., before training-loop metrics).
- **Output-format check:** validate exactly two lines and correct `path:line` format.
- **Task-alignment check (from observed tests):**
  - first line points to trainer file and barrier line,
  - second line is non-empty, technical, and concise.
- **Consistency check across runs:** all three successful trajectories independently converged on the same root cause (`rank-conditional barrier`), increasing confidence and reproducibility.

## References to Load On Demand
- PyTorch DDP collective semantics (`barrier`, `all_reduce`) and requirement that all ranks participate in identical collective order.
- DistributedSampler epoch/length consistency guidance (`set_epoch`, `drop_last`) for secondary hang diagnostics.
