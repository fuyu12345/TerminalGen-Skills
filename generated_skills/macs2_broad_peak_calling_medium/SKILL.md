---
name: calling-broad-chipseq-peaks-from-bed-intervals
description: Identify broad ChIP-seq enrichment regions from treatment/control BED signal intervals using overlap-aware fold-enrichment, interval merging, and output normalization. Use when treatment and control coordinates are shifted and a strict 4-column broad peak file is required.
---

# Calling Broad ChIP-seq Peaks from BED Intervals

## When to Use

- Process treatment/control BED-like interval files (`chrom start end signal`) into broad peaks.
- Enforce rules like:
  - treatment ≥ 3× control
  - merged peaks within a gap threshold (e.g., 500 bp)
  - minimum peak width (e.g., 1000 bp)
  - minimum combined peak signal (e.g., 100)
- Produce strict, testable output (`chrom\tstart\tend\tpeak_signal`) with no header/comments.

## Minimal Reliable Workflow

1. **Inspect input compatibility before computing enrichment.**  
   Check row counts and first-coordinate alignment; do not assume row-wise matching.
   - If coordinates differ (common), use overlap-aware comparison.

2. **Parse treatment and control intervals into chromosome-grouped, start-sorted lists.**  
   Ignore malformed lines and zero/negative-length intervals.

3. **Compute control background per treatment interval using overlap weighting.**  
   For each treatment interval, scan same-chromosome control intervals:
   - skip non-overlaps
   - compute overlap length
   - accumulate control contribution proportionally to overlap  
   Then apply enrichment rule (`treatment >= 3 * control_background`).

4. **Keep enriched treatment intervals and sort by chromosome/start.**

5. **Merge adjacent enriched intervals using the allowed gap (e.g., 500 bp).**  
   While merging:
   - extend end coordinate to max end
   - sum treatment signal into merged peak signal

6. **Filter merged peaks by final thresholds.**  
   Keep only peaks with:
   - `end - start >= min_width`
   - `merged_signal >= min_peak_signal`

7. **Write final output exactly as required.**  
   - 4 tab-separated columns
   - signal rounded to 2 decimals
   - no header, no comments
   - sorted by chromosome then start

## Common Pitfalls

- **Using exact coordinate keys between treatment/control.**  
  Evidence: successful runs showed treatment/control were not aligned and even had different row counts. Exact matching can misclassify shifted overlaps as missing control.
  
- **Depending on unavailable external tools (e.g., `bedtools`) without fallback.**  
  Evidence: one run failed mid-pipeline with `bedtools: command not found`, producing empty intermediates.

- **Not checking for empty intermediates after command failure.**  
  Evidence: downstream merge step ran on an empty file and produced `0` output peaks until recomputed.

- **Skipping output normalization constraints (format/order/thresholds).**  
  Tests explicitly check 4 columns, sorted order, minimum width/signal, no headers/comments, fold enrichment, and chromosome validity.

## Verification Strategy

Run lightweight structural and rule checks before submission:

```bash
# 1) File exists and non-empty
test -s /workspace/broad_peaks.txt

# 2) 4 fields, numeric coords/signal, thresholds, sorted
awk 'BEGIN{ok=1; pc=""; ps=-1}
NF!=4 {print "BAD_FIELDS",NR,$0; ok=0}
$2!~/^[0-9]+$/ || $3!~/^[0-9]+$/ || $4!~/^[0-9]+(\.[0-9]+)?$/ {print "BAD_TYPES",NR,$0; ok=0}
($3-$2)<1000 {print "BAD_WIDTH",NR,$0; ok=0}
($4+0)<100 {print "BAD_SIGNAL",NR,$0; ok=0}
(pc!="" && ($1<pc || ($1==pc && $2<ps))) {print "BAD_SORT",NR,$0; ok=0}
{pc=$1; ps=$2}
END{if(ok) print "VALID"}' /workspace/broad_peaks.txt
```

If task tests are available, run them (e.g., `pytest /tests/test_outputs.py -rA`) to confirm fold-enrichment and expected-region assertions.

## References to Load On Demand

- Python implementation template for overlap-weighted enrichment and merging.
- AWK-only fallback implementation for environments without Python dependencies.
