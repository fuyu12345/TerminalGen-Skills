---
name: detecting-problematic-optical-duplicate-tiles
description: Identify Illumina tiles with excessive optical duplicates from read metadata and write FLOWCELL:LANE:TILE outputs with path-safe delivery. Use when computing per-tile optical duplicate rates for sequencing QC tasks under terminal-bench style graders.
---

# Detecting Problematic Optical Duplicate Tiles

## When to Use
- Compute optical duplicate rates from TSV read metadata.
- Flag tiles where optical duplicates exceed a threshold (e.g., `> 12%`).
- Produce grader-facing output files where prompt paths and test paths may differ.

## Minimal Reliable Workflow
1. **Resolve input path defensively.**  
   Check candidate inputs in order, e.g.:
   - `/data/reads_metadata.tsv` (prompt path)
   - `/workspace/output/<task_key>/files/data/reads_metadata.tsv` (common test path)

2. **Parse TSV with explicit columns.**  
   Read: `flowcell, lane, tile, chromosome, position, x_coord, y_coord`.  
   Count total reads per tile key `(flowcell, lane, tile)`.

3. **Group candidate duplicates correctly.**  
   Group by exact key:  
   `(flowcell, lane, tile, chromosome, position)`.

4. **Detect optical duplicates via connected components (recommended).**  
   Within each group, connect read pairs with Euclidean distance `<= 100` pixels (same tile/group already guaranteed).  
   Count duplicates as `component_size - 1` per connected component.  
   (Use union-find; spatial bins of size 100 for speed.)

5. **Compute per-tile rate and filter.**  
   `rate = optical_duplicates_on_tile / total_reads_on_tile`  
   Keep only tiles where `rate > threshold` (strictly greater).

6. **Write deterministic output.**  
   Sort tile IDs and write one per line as:
   `FLOWCELL:LANE:TILE`.

7. **Deliver to both likely output locations.**  
   Write primary output and mirror it:
   - `/solution/problematic_tiles.txt`
   - `/workspace/solution/problematic_tiles.txt`  
   (copy or symlink) to avoid grader path mismatch.

## Common Pitfalls
- **Using only prompt-stated paths.**  
  In all 3 runs, agents wrote `/solution/problematic_tiles.txt` and printed plausible results, but verifier checked `/workspace/solution/problematic_tiles.txt` and failed file-existence tests.
- **Assuming only one input mount location.**  
  Tests referenced `/workspace/output/.../files/data/reads_metadata.tsv` while runs used `/data/reads_metadata.tsv`; missing mount caused downstream failures.
- **Using greedy “kept read” logic instead of component logic.**  
  Greedy approaches can undercount chain-like duplicates (`A~B`, `B~C`, `A!~C`). Union-find avoids this.
- **Skipping pre-submit checks against grader expectations.**  
  Not validating output path/format before completion leads to avoidable hard failures.

## Verification Strategy
Run these checks before marking complete:

1. **Path existence checks**
   - `test -f /solution/problematic_tiles.txt`
   - `test -f /workspace/solution/problematic_tiles.txt` (or ensure symlink/copy exists)

2. **Format checks**
   - Ensure every non-empty line matches `^[^:]+:[0-9]+:[0-9]+$`
   - Ensure no duplicate lines (`sort | uniq -d` is empty)

3. **Logic sanity checks**
   - Recompute with a small brute-force script on sampled groups and compare duplicate counts.
   - Confirm strict threshold semantics (`> 0.12`, not `>= 0.12`).

4. **End-to-end check**
   - If tests are available, run them locally before finalize.
   - If not, at least print: input path used, number of tiles processed, number flagged, and first few output lines.

## References to Load On Demand
- Union-find connected-component pattern for proximity clustering.
- Spatial hashing / grid bucketing for radius-neighbor queries.
