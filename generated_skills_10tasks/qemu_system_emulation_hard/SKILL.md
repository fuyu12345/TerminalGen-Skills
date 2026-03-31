---
name: validating-qemu-disk-image-specs
description: Validate and remediate VM disk images against a JSON spec, then emit a deterministic key=value report. Use when a task requires checking qemu image format/size/cluster properties and recreating non-compliant images.
---

# Validating QEMU Disk Image Specs

## When to Use

- Validating `/path/to/image` against a JSON spec (`format`, virtual size, cluster size).
- Remediating missing or mismatched images with `qemu-img create`.
- Producing a strict `key=value` report for CI grading.
- Handling uncertain spec shape (object vs one-element array), as seen in all three runs.

## Minimal Reliable Workflow

1. **Inspect spec shape before parsing assumptions.**  
   Run `cat spec.json` (or `jq type spec.json`) first.

2. **Normalize spec input to one object.**  
   Accept:
   - object: `{...}`
   - one-element array: `[{...}]`  
   Extract:
   - `format`
   - `virtual_size_gb`
   - `expected_cluster_size`

3. **Convert GB to bytes using GiB math.**  
   Compute `virtual_size_bytes = virtual_size_gb * 1024^3`.

4. **Inspect existing image (if present) with machine-readable output.**  
   Use `qemu-img info --output=json <image>` and compare top-level:
   - `.format`
   - `."virtual-size"`
   - `."cluster-size"`

5. **Recreate image only when absent or mismatched.**  
   Use:
   `qemu-img create -f <format> -o cluster_size=<cluster> <image> <virtual_size_bytes>`  
   (or `<N>G`, but bytes are safest for exact matching).

6. **Re-read final image properties and assert exact equality.**  
   Never assume creation succeeded.

7. **Write report in exact required format/order.**  
   Example:
   - `format=<actual>`
   - `virtual_size_bytes=<actual_bytes>`
   - `cluster_size=<actual_cluster>`

## Common Pitfalls

- **Assuming spec is always a JSON object.**  
  In all 3 runs, initial attempts failed with `TypeError: list indices must be integers or slices, not str` (or jq “Cannot index array with string”).  
  Guardrail: normalize list/dict spec before field access.

- **Trusting task prompt sample JSON over actual file contents.**  
  Prompt showed object form, but file was array-wrapped.  
  Guardrail: inspect real file first.

- **Using unverified creation path.**  
  Writing the report before re-reading `qemu-img info` can drift from actual image properties.  
  Guardrail: always generate report from final inspected values, not expected values.

- **Reading nested `children[].info` instead of top-level qcow2 fields.**  
  `qemu-img info --output=json` may include nested file-node info; required checks are top-level image properties.

## Verification Strategy

1. **Artifact existence**
   - `test -f <image>`
   - `test -f <report>`

2. **Image property verification**
   - `qemu-img info --output=json <image> | jq '{format, "virtual-size", "cluster-size"}'`
   - Confirm exact match to normalized spec-derived expected values.

3. **Report format verification**
   - Ensure exactly 3 lines, exact keys, deterministic order.
   - Parse report and compare each value to actual `qemu-img info` output.

4. **If grader tests fail with `TypeError` on `spec['format']` while your checks pass**
   - Classify as **test-harness mismatch** (spec treated as dict though file is list), not task logic failure.
   - Preserve robust task behavior (list/dict normalization + actual-image validation).
