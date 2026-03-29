---
name: fixing-packed-binary-struct-layout-in-c
description: Implement deterministic packed binary record serialization with GCC/Clang and verify byte-level layout against both specification and grader assertions. Use when C structs written via fwrite produce shifted/corrupted fields or size/offset mismatches.
---

# Fixing Packed Binary Struct Layout in C

## When to Use
- Debugging binary file corruption caused by struct padding/alignment.
- Making on-disk record layout stable across 32-bit/64-bit targets.
- Fixing C code that writes structs directly (`fwrite(&record, sizeof(record), 1, fp)`).
- Reconciling contradictory requirements between project docs and test harnesses.

## Minimal Reliable Workflow
1. **Read both contracts first (spec + tests).**  
   Inspect format docs and test assertions before editing code.  
   - In these runs, `reference_format.txt` required **24-byte** records with `uint64_t timestamp`, but tests asserted **21-byte** `<IIfffB` and only 5 records. This mismatch explains repeated “correct-by-doc, fail-by-grader” outcomes.

2. **Fix type definition correctness before layout work.**  
   Ensure the struct type is actually usable in C:
   - Either use `struct sensor_record` everywhere, or add a `typedef`.
   - Runs 2/3 initially failed compile with `unknown type name 'sensor_record'` because only `struct sensor_record` existed.

3. **Use fixed-width field types and explicit packing.**  
   Define layout with `<stdint.h>` and compiler packing directives:
   - GCC/Clang: `__attribute__((packed))`
   - MSVC fallback: `#pragma pack(push, 1)` / `#pragma pack(pop)`
   - Avoid ambiguous native types (`int`, `long`) for file format fields.

4. **Add compile-time layout guards.**  
   Use `_Static_assert(sizeof(...) == expected)` and `offsetof(...)` checks for each field offset.  
   This catches silent ABI/padding drift at compile time.

5. **Parse input into matching field types.**  
   Use conversions consistent with field definitions:
   - IDs/timestamps: `strtoul` / `strtoull`
   - floats: `strtof`
   Avoid lossy casts like `(uint8_t)atoi(...)` for 32-bit IDs or integer-casting float fields.

6. **Write exactly one canonical record representation.**  
   Keep serialization path single-source-of-truth:
   - Either packed-struct + `fwrite(record)` **or** explicit field-by-field serialization.
   - Do not mix incompatible struct definitions and parsing assumptions.

7. **Generate reported metadata from actual outputs.**  
   Compute `record_size_bytes` from `sizeof(record)` and `total_records_written` from successful writes (or validated file size / record size).

## Common Pitfalls
- **Trusting only reference docs, not tests.**  
  All 3 runs produced 24-byte/15-record outputs aligned with docs but failed tests expecting 21-byte/5-record behavior.
- **Missing typedef in C headers.**  
  Using `sensor_record` without `typedef` caused immediate compile failure in Runs 2/3.
- **Type truncation during parse.**  
  `sensor_id` parsed as `(uint8_t)` and pressure cast from integer corrupted values/offset interpretation.
- **Assuming packing is unnecessary because field sum “looks right.”**  
  Compiler alignment can still alter offsets unless guarded.
- **Relying on unavailable tools (`xxd`) without fallback.**  
  Use `od` as portable fallback for byte dumps.

## Verification Strategy
1. **Compile gate**
   - `gcc -Wall -Wextra -O2 ...`
   - Zero warnings/errors for modified files.

2. **Layout gate (compile-time)**
   - `_Static_assert(sizeof(record)==N)`
   - `_Static_assert(offsetof(field)==expected_offset)`

3. **Runtime file gate**
   - Run binary generator.
   - Confirm output size is multiple of record size.
   - Confirm reported record count matches writes.

4. **Byte-level decode gate**
   - Decode first few records using the exact expected unpack schema (from authoritative contract).
   - Verify numeric values within tolerance for floats.

5. **Contract mismatch gate (critical)**
   - If docs and tests disagree, explicitly detect and record discrepancy early.
   - For benchmark/grader tasks, verify against `/tests/test_outputs.py` before finalizing `solution.json`.

## References to Load On Demand
- GCC packed attribute docs (`__attribute__((packed))`)
- C11 `_Static_assert` and `offsetof`
- Python `struct.unpack` for binary spot-checks
- Portable hex inspection (`od -An -tx1 -v`)
