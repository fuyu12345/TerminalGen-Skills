---
name: validating-qemu-disk-image-spec-compliance
description: Validate and remediate VM disk images against a JSON spec, then emit a deterministic property report. Use when automating qemu-img compliance checks in CI or terminal-bench tasks with strict output assertions.
---

# Validating QEMU Disk Image Spec Compliance

## When to Use

- Validate whether a disk image already matches required `format`, virtual size, and `cluster_size`.
- Recreate the image if any required property is missing or mismatched.
- Generate a strict `key=value` validation report from **actual** `qemu-img info` output.
- Handle noisy environments where JSON shape may differ from documented schema (object vs single-item list).

## Minimal Reliable Workflow

1. **Inspect schema before parsing.**  
   Read `/workspace/disk_spec.json` and detect whether top-level JSON is an object or a one-item list. Normalize to one spec object in code.

2. **Extract expected values deterministically.**  
   Read:
   - `format`
   - `virtual_size_gb` → convert via `* 1024**3` (GiB bytes)
   - `expected_cluster_size`

3. **Inspect existing image safely.**  
   If image exists, run `qemu-img info --output=json <img>` and parse required fields (`format`, `virtual-size`, `cluster-size`).

4. **Recreate only when needed.**  
   If missing or mismatched, remove existing file and create with:
   - `qemu-img create -f <format> -o cluster_size=<cluster> <path> <size>`
   - Use explicit byte size or `<n>G` consistently.

5. **Re-read final image properties.**  
   Never trust creation success alone; always re-run `qemu-img info` and parse actual values.

6. **Write exact report format and order.**  
   Emit exactly:
   - `format=<actual>`
   - `virtual_size_bytes=<actual-bytes>`
   - `cluster_size=<actual-bytes>`

7. **Keep execution quoting-safe.**  
   Prefer a Python heredoc or temporary script over deeply nested `bash -lc` + `jq` quoting chains.

## Common Pitfalls

- **Assuming spec is always a JSON object.**  
  In all 3 runs, failures originated from `TypeError: list indices must be integers or slices, not str` due to array-wrapped spec input.

- **Misattributing root cause to qemu-img output shape.**  
  One run initially blamed `qemu-img info` JSON shape; the real hard failure came earlier from spec parsing.

- **Breaking shell with nested quotes.**  
  `bash -lc` + embedded single-quoted `jq` filters caused `unexpected EOF` and partial execution.

- **Leaving terminal in broken prompt state.**  
  Unterminated quote required `C-c`; missing newline on control input produced parser warnings and command concatenation risk.

- **Declaring completion before verifier-style checks.**  
  Runs produced correct image/report but still failed tests because the verifier parsed `disk_spec.json` with strict object indexing.

- **Using brittle one-liners for multi-step remediation.**  
  Longer inline scripts increased quoting and state errors; a self-contained Python block was more reliable.

## Verification Strategy

1. **Validate artifacts exist**
   - `test -f /workspace/vm_disk.img`
   - `test -f /workspace/validation_report.txt`

2. **Validate report schema**
   - Exactly 3 lines, exact keys, exact order.
   - Each line must contain one `=`.

3. **Cross-check report vs actual image**
   - Parse `qemu-img info` and compare `format`, `virtual-size`, `cluster-size` to report values.

4. **Cross-check actual image vs normalized spec**
   - Compare final image properties against normalized spec object (`dict` or first list item).

5. **Guard against harness/schema mismatch**
   - If downstream tests/tools index spec as `spec['format']`, detect list-wrapped spec early and normalize compatibility (in-memory; persist only if required by harness contract).

## References to Load On Demand

- `qemu-img info --output=json <img>`
- `qemu-img create -f qcow2 -o cluster_size=65536 <img> 8G`
- Python pattern: normalize `spec = data[0] if isinstance(data, list) else data`
