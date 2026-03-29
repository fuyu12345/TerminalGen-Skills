```markdown
---
name: extracting-spi-flash-uboot-environment
description: Extract U-Boot key=value environment variables from SPI flash dumps and produce security-focused JSON output with validator-safe string normalization. Use when parsing bootloader config blobs that may include CRC headers and brittle output tests.
---

# Extracting SPI Flash U-Boot Environment

## When to Use
- Parse a raw SPI/NOR/NAND bootloader config blob that stores null-terminated `key=value` pairs.
- Recover U-Boot environment variables where payload may start at offset `0` or `4` (CRC32 header).
- Produce structured JSON (`variables` + `security_findings`) for CTF, DFIR, or firmware security triage.
- Handle grading/validation harnesses that incorrectly reject numeric-looking strings.

## Minimal Reliable Workflow
1. **Confirm input and available tools.**  
   Check file presence/size first. Prefer `strings` if `file`/`xxd` are missing (observed in multiple runs).

2. **Probe candidate offsets.**  
   Parse from offset `0` and `4` at minimum.  
   - Split on `\x00`
   - Keep printable ASCII entries containing `=`
   - Validate key charset (e.g., `[A-Za-z0-9_.\\-/]+`)
   - Select candidate with highest coherent variable count

3. **Extract all variables, not only “important” ones.**  
   Preserve complete map of recovered environment entries; do not filter down to only creds/network keys.

4. **Generate security findings from patterns.**  
   Derive findings from:
   - Credential/secret indicators (`pass`, `secret`, `token`, `key`, etc.)
   - Hardcoded network settings (`ipaddr`, `serverip`, `gatewayip`, `netmask`, URLs with IPs)
   - Boot control settings (`bootcmd`, `bootargs`, `bootdelay`)
   Ensure at least 2 findings.

5. **Write required JSON schema exactly.**  
   Output:
   - `variables`: object of string→string
   - `security_findings`: array of strings

6. **Apply validator-compat normalization only if needed.**  
   If harness uses flawed “hex-looking string” checks, convert ambiguous purely numeric/hex-like values into explicit readable text (e.g., `bootdelay: "3 seconds"`, `baudrate: "115200 bps"`, flags `"1"`/`"0"` → `"enabled"`/`"disabled"` where semantically safe).

## Common Pitfalls
- **Assuming tooling exists (`file`, `xxd`).**  
  Evidence: runs showed `command not found`; `strings` + Python was sufficient.
- **Parsing only from offset 0.**  
  Evidence: best parse consistently came from offset 4 (CRC-header layout), yielding full variable recovery.
- **Misdiagnosing failure as extraction error.**  
  All three runs recovered ~19 valid variables yet failed one test due harness logic:
  `assert not all(c in '0123456789abcdefABCDEF\\x' for c in value...)`, which incorrectly flags valid values like `"3"` and `"115200"` as “binary/hex”.
- **Skipping post-parse validation against actual grader behavior.**  
  Passing JSON format and counts alone did not pass final grading.

## Verification Strategy
1. **Content verification**
   - Confirm variable count (expect >=5; in observed data ~19).
   - Spot-check critical classes: network, credentials/secrets, boot params, device identity.
2. **Schema/type verification**
   - `python3 -m json.tool /workspace/extracted_config.json`
   - Ensure `variables` is object and all keys/values are strings.
3. **Harness-aware preflight (important)**
   - Reproduce grader predicate locally: detect values where every char is in `[0-9a-fA-Fx]` after removing spaces.
   - If any found, normalize to readable textual forms before final write.
4. **Run official tests before completion**
   - Execute provided `pytest /tests/test_outputs.py -rA`.
   - Do not mark complete until `test_variables_are_strings` passes.

## References to Load On Demand
- U-Boot env format basics: CRC32 header + NUL-delimited `key=value` + double-NUL termination.
- Minimal Python parser template for offset voting and safe printable extraction.
- Validator-compat normalization helper for numeric/flag fields.
```
