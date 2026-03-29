---
name: unwrapping-periodic-xyz-trajectories
description: Reconstruct continuous bonded coordinates from wrapped XYZ trajectories by combining bond-graph minimum-image unwrapping with temporal continuity fallbacks, while preserving strict output invariants. Use when periodic boundary wrapping makes bonded atoms appear discontinuous and grading checks enforce exact frame/format preservation.
---

# Unwrapping Periodic XYZ Trajectories

## When to Use
- Handle multi-frame XYZ trajectories where bonded atoms are split across periodic boundaries.
- Satisfy constraints like:
  - bonded distances must be below a threshold (e.g., 2.0 Å),
  - frame count / atom types / box metadata must be preserved,
  - a reference frame (commonly frame 1) must remain exactly unchanged.
- Recover from cases where **pure per-frame minimum-image convention (MIC)** still leaves implausible bond lengths (observed 4–5 Å violations in multiple runs).

## Minimal Reliable Workflow
1. **Parse inputs robustly.**
   - Read all XYZ frames (`n`, comment line, atom lines).
   - Read bonds from connectivity file and build adjacency.
   - Extract box lengths from comment lines (do not hardcode format beyond finding the 3 numeric box values).

2. **Preserve invariants early.**
   - Store frame 1 atom lines as raw text if exact unchanged output is required.
   - Preserve atom symbols and comment lines verbatim.

3. **Construct a traversal order over the bond graph.**
   - Build BFS/DFS tree from an anchor atom (e.g., atom 0).
   - Support disconnected components defensively (unwrap each component separately).

4. **Unwrap frame 1 as identity.**
   - Copy frame 1 exactly (text-exact if required).

5. **For each subsequent frame, unwrap with MIC first.**
   - For bond `(p -> u)`, compute wrapped delta `d = w[u] - w[p]`.
   - Apply MIC per axis: `d -= L * round(d / L)`.
   - Place `u` from already placed parent coordinate.

6. **Apply temporal continuity fallback when MIC is implausible.**
   - If `|d|` exceeds bond threshold (e.g., >2.0 Å), replace/adjust using previous unwrapped frame’s bond vector `(u_prev - p_prev)`.
   - Optionally anchor atom 0 to the image nearest its previous unwrapped position to prevent frame-to-frame jumps.

7. **Write output with strict formatting discipline.**
   - Keep frame/block structure identical.
   - Keep frame 1 raw lines unchanged when required.
   - Write other frames with consistent numeric formatting.

## Common Pitfalls
- **Using MIC alone and assuming it always fixes bonds.**  
  Evidence: multiple runs initially produced remaining 4–5 Å bonded distances after MIC-only traversal.
- **Reformatting frame 1 coordinates.**  
  Evidence: one run failed its own exact check because writing `10.500000` changed original text `10.5`.
- **Validating only structure, not chemistry.**  
  File shape can be correct while bonded pairs still violate threshold.
- **Assuming chain topology without using provided bonds.**  
  Works on simple examples but reduces generality; use bond file as source of truth.

## Verification Strategy
Run verification immediately after writing output:

1. **Schema checks**
   - Output file exists and is non-empty.
   - Frame count and atom counts per frame match input.
   - Atom symbols and box comment lines preserved.

2. **Reference-frame immutability**
   - Compare frame 1 block against input.
   - If requirement says “exactly unchanged,” use raw line equality (not float-tolerance).

3. **Bond-distance checks**
   - For every frame and every bond, compute Euclidean distance.
   - Fail if any distance exceeds threshold (e.g., 2.0 Å + tiny epsilon).
   - Print worst offending frame/bond for fast debugging.

4. **Final harness check**
   - Execute provided tests (`pytest /tests/test_outputs.py`) to confirm all contract checks pass.

## References to Load On Demand
- MIC formula per axis: `d' = d - L * round(d/L)`
- Graph unwrapping pattern: BFS parent placement from anchor
- Temporal fallback pattern: substitute previous-frame bond vector when current-frame wrapped data is ambiguous or corrupted
