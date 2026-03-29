```markdown
---
name: diagnosing-tla-plus-state-explosion
description: Identify unbounded history-tracking constructs in TLA+ specs and produce concise root-cause analysis output. Use when TLC state space or memory usage explodes despite correct protocol logic.
---

# Diagnosing TLA+ State Explosion

## When to Use
- Investigating a TLA+ model where TLC runs out of memory or explores too many states.
- Suspecting modeling granularity issues (not protocol correctness bugs).
- Producing a short, structured diagnosis file (e.g., fixed line-count deliverables).

## Minimal Reliable Workflow
1. **Inspect spec variables and state tuple first.**  
   Open the `.tla` file and locate `VARIABLES` plus `vars == <<...>>`.

2. **Trace monotonic-growth updates in `Next` actions.**  
   Search for patterns like:
   - `x' = x \cup ...`
   - ever-growing sequences/logs
   - counters (`txnId`, timestamps) embedded into stored history

3. **Check whether old history is ever removed or abstracted.**  
   Flag constructs that keep “all messages ever sent” or equivalent historical detail.

4. **Confirm relevance to properties.**  
   Verify invariants/safety properties do not require full history precision; if they only need current/in-flight facts, treat full history as likely state-space inflation.

5. **Write the diagnosis in the required compact format.**  
   For 3-line outputs:
   - Line 1: culprit variable/construct
   - Line 2: why it explodes states
   - Line 3: fix category (short, general)

6. **Validate exact formatting before submission.**  
   Use `cat -n` or `nl -ba` to confirm exact line count and content alignment.

## Common Pitfalls
- **Naming symptoms instead of the state variable.**  
  Avoid vague outputs like “state explosion from complexity”; explicitly name the construct (e.g., `messages variable`).

- **Ignoring interaction between history and IDs.**  
  In all successful runs, explosion was tied to cumulative message history plus transaction IDs, which creates many distinct but behaviorally redundant states.

- **Overwriting deliverable constraints.**  
  Failing fixed-format requirements (exactly 3 lines, short fix type) can fail tests even if diagnosis is conceptually correct.

- **Proposing implementation-specific fixes instead of fix type.**  
  Keep line 3 categorical (e.g., “Track only in-flight messages”, “Remove historical message tracking”).

## Verification Strategy
- **Content verification:** Ensure all lines point to the same root cause (single construct + matching explanation + matching fix type).
- **Format verification:** Confirm file exists and has exactly required line count.
- **Assertion-driven check:** Mirror typical grader expectations:
  - file exists
  - exact line count
  - line 1 identifies variable/construct
  - line 2 explains state explosion mechanism
  - line 3 suggests valid fix category
  - culprit is the correct one for this spec pattern

**Terminal evidence across 3/3 successful runs:**  
Each passing run identified `messages` as the culprit because it is modeled as an ever-growing set (“all messages ever sent”) and updated via union without pruning; this consistently satisfied all tests.

## References to Load On Demand
- TLA+ modeling guidance on abstraction and state reduction.
- TLC performance tuning docs (state constraints, symmetry, abstraction patterns).
- Reusable grep patterns for monotonic-state growth in specs.
```
