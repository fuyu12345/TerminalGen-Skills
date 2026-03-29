---
name: configuring-kvm-nested-virtualization
description: Detect CPU vendor and write a valid modprobe.d KVM options file with nested virtualization enabled. Use when a task requires producing a CPU-matched `kvm.conf` (Intel vs AMD) for persistent nested virtualization.
---

# Configuring KVM Nested Virtualization

## When to Use
Use this skill when required to create or fix a KVM module config file (often `/root/kvm.conf` or `/etc/modprobe.d/kvm.conf`) so nested virtualization is enabled and module choice matches host CPU vendor.

Evidence from all 3 successful runs:
- CPU vendor was detected from `/proc/cpuinfo`.
- Correct output file content was exactly one options line.
- Tests passed only when module name matched vendor and `nested=1`.

## Minimal Reliable Workflow
1. Detect vendor from `/proc/cpuinfo` (do not assume Intel/AMD).
   ```bash
   grep -m1 '^vendor_id' /proc/cpuinfo
   ```
2. Map vendor to module name:
   - `GenuineIntel` → `kvm_intel`
   - `AuthenticAMD` → `kvm_amd`
3. Write exactly one valid modprobe options line to the required target file.
   ```bash
   if grep -q 'vendor_id[[:space:]]*:[[:space:]]*GenuineIntel' /proc/cpuinfo; then
     echo 'options kvm_intel nested=1' > /root/kvm.conf
   elif grep -q 'vendor_id[[:space:]]*:[[:space:]]*AuthenticAMD' /proc/cpuinfo; then
     echo 'options kvm_amd nested=1' > /root/kvm.conf
   else
     echo 'Unsupported CPU vendor' >&2
     exit 1
   fi
   ```
4. Confirm file exists, is readable, and content is correct.
   ```bash
   ls -l /root/kvm.conf
   cat /root/kvm.conf
   ```

## Common Pitfalls
- Writing Intel config on AMD (or vice versa).  
  - Seen in initial environment state: `/etc/modprobe.d/kvm.conf` had `options kvm_intel nested=0` while CPU vendor was `AuthenticAMD`.
- Leaving `nested=0` (disabled) instead of `nested=1`.
- Writing to the wrong file path (task may require `/root/kvm.conf`, not editing existing `/etc/modprobe.d/kvm.conf`).
- Using invalid syntax (must be `options <module> nested=1`; avoid extra tokens/invalid formatting).

## Verification Strategy
Tie checks to the observed test expectations (all 6 passed in each run):

1. **File exists/readable**
   ```bash
   test -r /root/kvm.conf
   ```
2. **Module matches processor type**
   - Compare `vendor_id` from `/proc/cpuinfo` against line in config.
3. **Nested enabled**
   - Ensure line contains `nested=1`.
4. **Syntax validity**
   - Ensure line format is:
     ```text
     options kvm_intel nested=1
     ```
     or
     ```text
     options kvm_amd nested=1
     ```
5. **Completeness**
   - Ensure required options line is present and unambiguous.

A compact self-check:
```bash
vendor="$(awk -F: '/^vendor_id/{gsub(/^[ \t]+/,"",$2); print $2; exit}' /proc/cpuinfo)"
line="$(cat /root/kvm.conf)"
case "$vendor" in
  GenuineIntel) [[ "$line" == "options kvm_intel nested=1" ]] ;;
  AuthenticAMD) [[ "$line" == "options kvm_amd nested=1" ]] ;;
  *) false ;;
esac
```
