---
name: fixing-redlock-simulator-with-scenario-driven-validation
description: Implement and validate a Redlock-style distributed lock simulator with majority consensus, expiry, and safe release semantics. Use when a lock simulator allows multiple clients to acquire the same lock or scenario files encode expected lock outcomes.
---

# Fixing Redlock Simulator with Scenario-Driven Validation

## When to Use
- Fixing a broken distributed lock simulator (especially Redlock-style quorum logic).
- Diagnosing mutual exclusion bugs where multiple clients can acquire the same lock.
- Handling scenario datasets with sequential `acquire`/`release` actions and delays.
- Producing both corrected code and a required `results.json` summary artifact.

## Minimal Reliable Workflow
1. **Inspect implementation and scenario schema first.**  
   Read the existing simulator and confirm scenario structure before coding. In these runs, `clients` was a JSON-encoded **string**, not a native list.

2. **Normalize scenario input parsing.**  
   Accept both:
   - `clients` as JSON string → `json.loads(...)`
   - `clients` as list → use directly

3. **Implement per-node lock semantics with expiry cleanup.**  
   For each storage node:
   - Purge expired lock entries before reads/writes.
   - Allow acquisition only if lock absent after purge.
   - Release only if `client_id` matches owner.

4. **Implement distributed acquire with quorum + rollback.**  
   - Compute `quorum = (num_nodes // 2) + 1`.
   - Attempt set across all nodes.
   - Succeed only if acquired on quorum.
   - If quorum not reached, release partial writes (rollback).

5. **Implement release across all nodes.**  
   - Attempt owner-checked release on every node.
   - Return success based on consistent policy (recommended: client held quorum before release).

6. **Simulate delays via virtual time, not `sleep`, when replaying scenarios.**  
   Increment a `current_time` accumulator by each step delay and pass `now=current_time` into lock operations. This avoids slow/flaky runtime and still validates timeout behavior.

7. **Evaluate each scenario step-by-step against `should_succeed`.**  
   Track mismatch details for debugging; aggregate into:
   - `tests_passed`
   - `tests_failed`
   - `success` (`tests_failed == 0`)

8. **Write exact required output structure to `results.json`.**  
   Keep only required summary fields unless task explicitly requests extras.

## Common Pitfalls
- **Treating `clients` as a list when it is a JSON string.**  
  Seen in all runs’ dataset inspection; parsing is required.
- **Using real `time.sleep` for delays.**  
  One run stalled due to cumulative delay; virtual time was more reliable.
- **Forgetting newline in terminal command batches.**  
  Produced concatenated commands/warnings in one run; always terminate keystrokes with `\n`.
- **Incorrect quorum threshold.**  
  Buggy baseline used `required_nodes = 1`; must require majority.
- **No rollback on failed acquire.**  
  Leaves partial lock state and breaks subsequent actions.
- **Partial release (subset of nodes only).**  
  Baseline released only first two nodes; must release across all nodes.
- **Wrong expiry computation.**  
  Baseline used `expiry_time = now`; must be `now + timeout`.

## Verification Strategy
1. **Structural checks**
   - `fixed_simulator.py` exists, non-empty, valid Python.
   - `results.json` exists, valid JSON, exact required fields/types.

2. **Behavioral checks against scenario file**
   - Parse all scenarios successfully.
   - Replay actions in order with cumulative time.
   - Assert each operation matches `should_succeed`.

3. **Targeted assertions derived from observed bug classes**
   - Second client fails while first lock is unexpired.
   - New client succeeds after timeout expiry.
   - Release by non-owner fails.
   - Re-acquire by same client without release fails (if non-reentrant contract is expected).
   - Competing clients never both succeed for same active lock window.

4. **Final consistency check**
   - Ensure `tests_failed == 0` and `success == true`.
   - Ensure `tests_passed` equals number of scenarios executed.

## References to Load On Demand
- Redlock quorum rule: majority of independent nodes required.
- Deterministic simulation technique: inject `now` into time-dependent methods.
- Terminal automation hygiene: newline-terminated commands, short polling waits instead of long blocking sleeps.
