---
name: extracting-qemu-launch-config-to-json
description: Extract memory, CPU count, network mode, and display type from a QEMU launch command and write normalized JSON output. Use when a script-based QEMU configuration must be summarized for validation or documentation.
---

# Extracting QEMU Launch Config to JSON

## When to Use
- Summarizing a `qemu-system-*` launch script into a machine-checkable JSON file.
- Validating deployment documentation against actual QEMU CLI arguments.
- Producing outputs that must satisfy strict schema/type/lowercase test assertions.

(Observed across 3/3 successful runs with identical pass set: file exists, valid JSON, required fields, correct types, lowercase strings, values matching script.)

## Minimal Reliable Workflow
1. **Read the launch script, not prose summaries.**  
   Inspect the command block directly (e.g., `sed -n '1,200p' /path/to/qemu-launch.sh`).

2. **Extract memory in MB.**  
   - Parse `-m <value>`.
   - Normalize to integer MB (`memory_mb`).
   - If absent, use `0`.

3. **Extract total CPU count.**  
   Parse `-smp`:
   - If form is `-smp N`, use `N`.
   - If form includes topology (`cores=`, `threads=`, `sockets=`), compute total as product of present topology dimensions (default missing dimensions to `1`).
   - If absent, use `0`.

4. **Extract network mode classification.**  
   Prefer actual network backend option:
   - `-netdev tap,...` → `"tap"`
   - `-netdev user,...` or `-nic user` → `"user"`
   - No network option → `"none"`
   - Unmapped backend → `"other"`

5. **Extract display type classification.**  
   - `-display vnc...` or `-vnc ...` → `"vnc"`
   - `-display gtk` → `"gtk"`
   - `-display sdl` → `"sdl"`
   - `-nographic` or explicit none → `"none"`
   - Unmapped display backend → `"other"`

6. **Write exact JSON schema (only 4 keys):**
   ```json
   {
     "memory_mb": 0,
     "cpu_count": 0,
     "network_mode": "none",
     "display_type": "none"
   }
   ```
   Use integers for numeric fields and lowercase strings for string fields.

7. **Save to required path and print for quick sanity-check.**

## Common Pitfalls
- **Using comments instead of CLI flags as source of truth.**  
  Runs succeeded by reading actual options (`-m`, `-smp`, `-netdev`, `-display`) directly.
- **Miscomputing CPU count from `-smp` topology.**  
  Treat topology as total vCPUs, not just one dimension unless only one is provided.
- **Wrong schema shape.**  
  Tests require exactly four specific keys; extra/missing keys risk failure.
- **Type mistakes.**  
  `memory_mb`/`cpu_count` must be numbers, not quoted strings.
- **Case mistakes in string fields.**  
  Tests explicitly check lowercase string values.
- **Missing default behavior when option absent.**  
  Use `0` for integers and `"none"` for strings when not specified.

## Verification Strategy
Run checks equivalent to observed passing assertions:

1. **Existence:** confirm output file exists at required path.
2. **JSON validity:** parse with `jq .` or Python `json.load`.
3. **Schema exactness:** ensure key set is exactly:
   `memory_mb`, `cpu_count`, `network_mode`, `display_type`.
4. **Type checks:** integers for numeric fields; strings for modes/types.
5. **Lowercase checks:** verify `network_mode` and `display_type` are lowercase.
6. **Value-to-script consistency:** re-open launch script and confirm each JSON value maps to the corresponding QEMU argument.

## References to Load On Demand
- QEMU `-smp` option semantics (topology and total vCPU interpretation).
- QEMU networking options (`-netdev`, `-nic`, legacy `-net`) mapping.
- QEMU display options (`-display`, `-vnc`, `-nographic`) normalization rules.
