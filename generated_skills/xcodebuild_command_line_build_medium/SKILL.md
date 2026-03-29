---
name: repairing-android-cli-gradle-builds
description: Restore Android command-line debug APK builds by bootstrapping a compatible Gradle runtime, aligning repository configuration, and fixing packaging-time resource gaps. Use when terminal Gradle builds fail (missing wrapper, Gradle-version mismatch, or resource-linking errors).
---

# Repairing Android CLI Gradle Builds

## When to Use
- Build fails immediately with `./gradlew: No such file or directory`.
- System `gradle` is too old to parse modern `settings.gradle` (`dependencyResolutionManagement` not found).
- Build fails with repository policy conflicts (`FAIL_ON_PROJECT_REPOS` vs `allprojects { repositories ... }`).
- Build reaches `processDebugResources` and fails on missing `@mipmap/ic_launcher` / `ic_launcher_round`.
- Need a CI-friendly output file with APK path and exact size.

## Minimal Reliable Workflow
1. **Inspect wrapper and Gradle compatibility first.**
   - Check for `gradlew` and `gradle/wrapper/gradle-wrapper.jar`.
   - Read `gradle/wrapper/gradle-wrapper.properties` and note required distribution version.
   - Check `gradle --version`; if very old, do not rely on it for modern Android projects.

2. **Bootstrap with a compatible Gradle runtime when wrapper is missing/broken.**
   - Download the version matching wrapper properties (or AGP-compatible version).
   - Run build with that binary directly (e.g., `gradle -p <project> assembleDebug`) to unblock.

3. **Resolve repository-mode conflicts before retry loops.**
   - If `settings.gradle` uses `repositoriesMode.set(FAIL_ON_PROJECT_REPOS)`, remove project-level repository blocks from root `build.gradle` (preferred stable fix seen across runs), or consistently change policy/project blocks together.
   - Re-run build and capture first hard failure.

4. **Fix packaging/resource blockers surfaced after Gradle config issues.**
   - If manifest references missing launcher mipmaps, add valid resources matching referenced names.
   - Use valid resource placement; avoid invalid adaptive icon XML in density-specific folders.

5. **Run build in isolation and wait for completion.**
   - Launch a single build command and do not send follow-up commands until prompt returns.
   - Poll/wait instead of queuing more commands into an active Gradle process.

6. **Generate result artifact only after APK exists.**
   - Confirm APK file exists and get exact byte size via `stat`.
   - Write JSON with exactly required fields and real values.

## Common Pitfalls
- **Using outdated system Gradle** (observed: 4.4.1) on modern settings files → `dependencyResolutionManagement()` method missing.
- **Command interleaving during long Gradle runs** → shell commands get consumed by Gradle stdin, causing false progress and broken output files.
- **Repository policy mismatch** (`FAIL_ON_PROJECT_REPOS` + `allprojects.repositories`) → configuration failure before tasks execute.
- **Invalid icon resource placement** (adaptive-icon XML in `mipmap-mdpi`/`hdpi` etc.) → AAPT errors requiring SDK 26 context.
- **Writing output JSON before successful build** → empty/invalid `apk_size_bytes`, nonexistent APK path.

## Verification Strategy
1. **Build verification**
   - Ensure `assembleDebug` exits successfully (`BUILD SUCCESSFUL` and zero exit code).

2. **APK verification**
   - Verify file exists at expected debug path.
   - Verify non-zero size.
   - Record size from `stat` and reuse same value in JSON.

3. **Output JSON verification**
   - Confirm file exists.
   - Confirm valid JSON with exactly:
     - `build_successful: true`
     - `apk_path` (absolute string path to existing `.apk`)
     - `apk_size_bytes` (integer, matches `stat`)

4. **Final test-harness verification**
   - Run project/task tests (e.g., `pytest /tests/test_outputs.py`) after writing JSON.
   - If tests fail, re-check JSON field types and that size/path match actual file.
