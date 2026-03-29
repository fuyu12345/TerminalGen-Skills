```markdown
---
name: repairing-autotools-configure-permission-denied
description: Restore a broken Autotools build by fixing script executability and regenerating configure artifacts when needed. Use when ./configure fails with permission errors or shell syntax errors on legacy C projects.
---

# Repairing Autotools Configure Permission/Corruption Issues

## When to Use

Use this skill when a legacy Autotools project fails early in setup, especially with signals like:

- `./configure: Permission denied`
- `./configure: ... syntax error: unexpected end of file`
- `make: *** No targets specified and no makefile found. Stop.`

This pattern appeared consistently across all three runs:
1. `configure` was non-executable initially.
2. After `chmod +x`, `configure` still failed due to truncation/corruption.
3. `autoreconf -fi` regenerated valid artifacts; then `./configure && make` succeeded.

## Minimal Reliable Workflow

1. **Enter project root and inspect build files.**
   ```bash
   cd /path/to/project
   ls -la
   ls -l configure configure.ac Makefile.am Makefile.in
   ```

2. **Fix execute permissions on Autotools scripts (non-destructive).**
   ```bash
   find . -maxdepth 3 -type f \
     \( -name configure -o -name config.guess -o -name config.sub -o -name install-sh -o -name missing -o -name depcomp -o -name ltmain.sh \) \
     -exec chmod +x {} +
   ```

3. **Run `./configure` once; branch on result.**
   - If it succeeds, continue.
   - If it fails with shell parse errors (e.g., unexpected EOF), treat `configure` as invalid and regenerate:
   ```bash
   autoreconf -fi
   ./configure
   ```

4. **Build with make.**
   ```bash
   make -j"$(nproc)"
   ```

5. **Resolve and validate the produced binary (real file, executable, non-symlink).**
   ```bash
   exe="$(readlink -f ./calculator)"
   test -f "$exe" && test -x "$exe" && test ! -L ./calculator
   ```

6. **Write deliverable only after validation passes.**
   ```bash
   printf 'EXECUTABLE=%s\nSTATUS=SUCCESS\n' "$exe" > /tmp/build_result.txt
   ```

## Common Pitfalls

- **Assuming chmod is sufficient.**  
  In all runs, `chmod +x configure` removed one blocker but exposed another: broken/truncated `configure` (`syntax error: unexpected end of file`).

- **Running `make` after failed `./configure`.**  
  This predictably fails with missing Makefile (`No targets specified and no makefile found`).

- **Writing success output before build verification.**  
  One trajectory briefly wrote:
  `EXECUTABLE=` (empty) with `STATUS=SUCCESS`, which is invalid.

- **Hardcoding output location assumptions (`src/calculator` only).**  
  This project produced `./calculator` in root. Check actual build output rather than assuming subdir layout.

## Verification Strategy

Run these checks explicitly before marking success:

1. **Configure path is executable**
   ```bash
   test -x ./configure
   ```

2. **Configure completed and generated Makefile**
   ```bash
   test -f ./Makefile
   ```

3. **Binary exists at build-produced location and is executable regular file**
   ```bash
   test -f ./calculator && test -x ./calculator && test ! -L ./calculator
   ```

4. **Binary is a real compiled executable (ELF on Linux)**
   ```bash
   file ./calculator | grep -q 'ELF'
   ```

5. **Result file format is exact**
   ```bash
   cat /tmp/build_result.txt
   # Must be exactly:
   # EXECUTABLE=/absolute/path/to/calculator
   # STATUS=SUCCESS
   ```

These checks align with observed verifier expectations across all runs (`configure executable`, `Makefile generated`, binary exists/executable/regular/ELF, and strict result-file format).
```
