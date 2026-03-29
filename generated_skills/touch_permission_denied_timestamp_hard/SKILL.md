---
name: detecting-readonly-files-by-utime-probing
description: Empirically identify files that reject timestamp updates due to read-only filesystems while preserving original timestamps. Use when a task requires reporting timestamp-update failures from a candidate file list.
---

# Detecting Read-Only Files by `utime` Probing

## When to Use

- Determine which files in a provided list cannot have timestamps changed.
- Distinguish true read-only filesystem failures from other errors.
- Produce machine-validated JSON output listing only affected existing files.
- Comply with “test by attempting modification” requirements (not mount-flag inference).

## Minimal Reliable Workflow

1. Load candidate file paths from the provided list file.
2. Skip blank lines and skip non-existent paths.
3. For each existing path:
   1. Read original `atime`/`mtime` (`st_atime_ns`, `st_mtime_ns`).
   2. Attempt a reversible timestamp change with `os.utime(...)` (change `atime`, keep `mtime`).
   3. If the call fails with `errno.EROFS`, record the path as read-only.
   4. If the call succeeds, immediately restore original timestamps with a second `os.utime(...)`.
4. Deduplicate and sort collected read-only paths alphabetically.
5. Write JSON with exactly:
   - `readonly_count` (int)
   - `readonly_files` (sorted array of absolute paths)
6. Ensure `readonly_count == len(readonly_files)`.

### Reference implementation pattern (Python)

```python
import os, json, errno

readonly = []
for p in paths:
    if not p or not os.path.exists(p):
        continue
    try:
        st = os.stat(p)
    except FileNotFoundError:
        continue

    a0, m0 = st.st_atime_ns, st.st_mtime_ns
    a1 = a0 + 1 if a0 < 2**63 - 1 else a0 - 1

    try:
        os.utime(p, ns=(a1, m0))
    except OSError as e:
        if e.errno == errno.EROFS:
            readonly.append(p)
        continue

    os.utime(p, ns=(a0, m0))  # restore
```

## Common Pitfalls

- Using mount metadata instead of empirical mutation attempts.  
  - Requirement and passing runs confirm the test must be behavioral (`utime` attempt).
- Failing to restore timestamps after successful probes.  
  - Violates “no permanent timestamp changes.”
- Treating any `OSError` as read-only.  
  - Only classify `errno.EROFS` as read-only filesystem failure.
- Including non-existent files.  
  - Must skip them entirely.
- Emitting wrong JSON shape or unsorted list.  
  - Output must have exactly two fields and sorted `readonly_files`.

## Verification Strategy

Run checks equivalent to the observed passing suite (11/11 in all three runs):

1. **Schema checks**
   - Output file exists.
   - Valid JSON.
   - Contains exactly `readonly_count` and `readonly_files`.
2. **Type/consistency checks**
   - `readonly_count` is integer.
   - `readonly_files` is array.
   - Count matches array length.
3. **Content checks**
   - `readonly_files` is alphabetically sorted.
   - Every listed file exists.
   - Every listed file comes from the input sync list.
   - Every listed file actually fails timestamp touching (read-only behavior).
   - Ground truth match for expected read-only set.

Use `pytest`/harness tests if available, plus quick manual checks (`cat` output, JSON parse) before finalizing.

## References to Load On Demand

- Python docs: `os.utime`, `os.stat`, nanosecond timestamp fields.
- POSIX errno reference: `EROFS` semantics.
