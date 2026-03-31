---
name: implementing-lzw-cli-compression
description: Implement a robust LZW-style compress/decompress CLI with compact integer-code serialization and corruption handling. Use when fixing or building dictionary-based archival tools that must pass round-trip tests and compression-ratio thresholds.
---

# Implementing LZW CLI Compression

## When to Use
Use this skill when a task requires:

- A single script with `compress`, `decompress`, and `test` commands
- Dictionary-based compression (LZW-like) over text/byte data
- Explicit edge-case handling (empty input, single char, repeated patterns, printable ASCII)
- A hard compression-ratio gate (for example `<= 0.70`)
- Graceful handling of corrupted compressed archives

## Minimal Reliable Workflow
1. **Inspect evaluation inputs before coding.**  
   Parse test-case format exactly (including cases like `|0` for empty input and inputs with leading/trailing spaces).

2. **Implement LZW on bytes with bounded dictionary growth.**  
   - Initialize compressor/decompressor dictionaries with single-byte symbols (`0..255`).
   - Cap dictionary size (commonly `4096` for 12-bit codes).
   - Implement the LZW decompression special case `k == next_code` (`entry = w + w[:1]`).

3. **Serialize integer codes compactly.**  
   Avoid naive storage (e.g., text integers or always-16-bit codes) when ratio matters.  
   Use bit-packed codes (fixed 12-bit or dynamic 9→12-bit) with a small binary header.

4. **Harden decompression against corruption.**  
   Validate:
   - magic/header
   - code count vs payload length
   - code range validity
   - truncation / malformed padding
   Raise clear errors instead of crashing or silently emitting bad bytes.

5. **Implement CLI contract exactly.**  
   Support:
   - `python solution.py compress <input_file> <output_file>`
   - `python solution.py decompress <input_file> <output_file>`
   - `python solution.py test` (writes `/workspace/results.json` with required schema)

6. **Compute ratio from on-disk compressed bytes, not internal code list length.**  
   Compare actual archive size to original file size.

7. **Write results JSON with exact required fields and types.**  
   Include: `tests_passed`, `tests_failed`, `compression_ratio`, `all_tests_passed`.

## Common Pitfalls
- **Using a storage format that ruins ratio despite correct LZW logic.**  
  Evidence: one run passed round-trip but failed ratio at `0.7394` with fixed 16-bit code storage; switching to bit-packed coding passed (`0.4785` / `0.5551`).

- **Ignoring whitespace-sensitive test inputs.**  
  Stripping lines can break inputs like `"   spaces   test   "`.

- **Forgetting explicit empty-input handling.**  
  Test files may encode empty input via a leading delimiter (`|0`).

- **Omitting decompressor special-case logic (`k == next_code`).**  
  Causes failures on valid LZW streams with self-referential dictionary growth patterns.

- **Not validating archive structure before decode.**  
  Missing checks for header/payload mismatch leads to fragile corruption handling.

- **Letting compressor/decompressor dictionary policies diverge.**  
  Any mismatch in growth/cap behavior breaks round-trip.

## Verification Strategy
Run verification in layers:

1. **Static/CLI sanity**
   - Ensure script is executable.
   - Run `python solution.py test` with zero crashes.

2. **Results contract**
   - Confirm `/workspace/results.json` exists and is valid JSON.
   - Confirm required keys and types are exact.

3. **Functional correctness**
   - Ensure `tests_failed == 0`.
   - Ensure `all_tests_passed == true`.

4. **Compression gate**
   - Explicitly check `compression_ratio <= required_threshold` (e.g., `0.70`).
   - If ratio fails but round-trip passes, optimize serialization first (not necessarily core LZW logic).

5. **Edge/corruption checks**
   - Round-trip: empty, single-char, repeated sequences, printable ASCII range.
   - Corruption: malformed header/truncated payload/invalid codes must fail gracefully.

## References to Load On Demand
- Canonical LZW compressor/decompressor state transitions
- Bit-packing patterns for fixed-width and variable-width code streams
- Robust binary container validation checklist (magic/version/count/padding)
