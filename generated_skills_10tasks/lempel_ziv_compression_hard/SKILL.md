---
name: implementing-lz77-cli-compressor
description: Build a binary-safe sliding-window compressor/decompressor CLI with reproducible ratio reporting. Use when tasks require lossless round-trip validation across mixed text/binary files and graded output JSON.
---

# Implementing LZ77 CLI Compressor

## When to Use

Use this skill when a task asks for:

- A `compress` / `decompress` command-line tool
- Sliding-window (LZ-style) matching
- Exact byte-for-byte round trips on multiple files
- A computed `results.json` with compression ratios
- Test-harness checks that compare reported ratios to actual file sizes

---

## Minimal Reliable Workflow

1. **Create a deterministic on-disk format.**
   - Add a short magic header + version byte.
   - Encode two token types: literals and back-references.
   - Keep offsets/lengths bounded and validated.

2. **Implement compression with a bounded match search.**
   - Use a sliding window and hash/indexed candidate lookup.
   - Enforce `MIN_MATCH`, `MAX_MATCH`, and `WINDOW_SIZE`.
   - Limit candidate checks for performance (`MAX_CANDIDATES`) to stay fast on larger files.

3. **Implement decompression with strict safety checks.**
   - Reject bad magic/version.
   - Reject truncated tokens.
   - Reject invalid offsets (`offset <= 0` or `offset > len(output)`).
   - Support overlapping back-reference copy correctly.

4. **Keep all file I/O binary.**
   - Always use `"rb"` / `"wb"` for both text and binary fixtures.

5. **Expose exact CLI contract.**
   - Support:
     - `python3 compressor.py compress <input_file> <output_file>`
     - `python3 compressor.py decompress <input_file> <output_file>`
   - Return non-zero on invalid usage/errors.

6. **Run full round-trip on every required fixture.**
   - Compress each file.
   - Decompress each output.
   - Compare with `cmp -s` (or equivalent bytewise check).

7. **Generate `results.json` from actual file sizes.**
   - Compute `compressed_size / original_size` for each required file key.
   - Write exact required keys (e.g., `small_ratio`, `medium_ratio`, `large_ratio`, `binary_ratio`).

---

## Common Pitfalls

- **Rebinding outer variables inside nested functions (Python closure trap).**  
  In one run, `out += ...` inside a nested `flush_literals()` caused:
  `cannot access local variable 'out' where it is not associated with a value`.  
  Prevent this by mutating instead of rebinding (`out.extend(...)`) or declaring scope explicitly.

- **Continuing pipeline after compression failed.**  
  When `.lz` files were never produced, downstream decompress and ratio steps failed with `FileNotFoundError`.  
  Gate each stage: stop and fix the first failure before computing ratios.

- **Writing ratios not tied to produced artifacts.**  
  Tests checked that reported JSON ratios matched actual compressed files.  
  Compute ratios directly from filesystem sizes after successful compression.

- **Skipping binary-safe handling.**  
  Text-mode I/O can silently corrupt non-text fixtures. Always use byte mode.

---

## Verification Strategy

Run verification in the same order tests logically require:

1. **Artifact existence**
   - Confirm `compressor.py` exists at required path.
   - Confirm `results.json` exists.

2. **Round-trip correctness (per file)**
   - For each fixture (small/medium/large/binary):
     - compress
     - decompress
     - `cmp -s original decompressed` and require exit code `0`.

3. **Compression-ratio requirement**
   - Compute all ratios from real output sizes.
   - Ensure at least one ratio is `<= 0.70`.

4. **JSON format + consistency**
   - Ensure required keys are present and numeric.
   - Recompute ratios and confirm they match `results.json` values.

This strategy matched all observed successful runs and directly prevents the only observed failure mode.

---

## References to Load On Demand

- LZ77/LZSS token design patterns (literal-run + match tokens)
- Python bytearray mutation vs rebinding behavior in closures
- Fast match-finding structures (hash chains, deque/list pruning)
