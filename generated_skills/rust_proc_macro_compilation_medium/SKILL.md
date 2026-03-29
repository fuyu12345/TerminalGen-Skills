---
name: fixing-rust-derive-macro-trait-signature-and-clean-build
description: Diagnose and repair Rust workspace compilation failures caused by custom derive macros, then verify warning-free build and runnable binary. Use when a proc-macro crate and consumer crate disagree on generated trait impls.
---

# Fixing Rust Derive Macro Trait Signature and Clean Build

## When to Use

Use this skill when:

- A Rust workspace has a `proc-macro` crate plus an app/library crate using `#[derive(...)]`.
- Build errors originate from derive expansion (for example `error[E0186]` about method signature mismatch).
- Task requires **both crates** to compile cleanly, with no warnings, and a working binary.
- You must produce structured status output (e.g., solution file with crate status + binary path).

---

## Minimal Reliable Workflow

1. **Inspect both crates before editing.**  
   Open:
   - workspace `Cargo.toml`
   - proc-macro `Cargo.toml` and `src/lib.rs`
   - consumer crate `Cargo.toml` and source using `#[derive]`

2. **Run a full workspace build and wait for completion.**  
   Use `cargo build`, then poll until compiler finishes.  
   In all three runs, the key error appeared only after full compile:
   - `E0186`: trait requires `fn describe(&self)`, macro generated `fn describe()`.

3. **Fix the derive macro at the source of expansion.**
   - Generate impl method signature that exactly matches trait contract.
   - Keep implementation in macro crate, not ad-hoc fixes in consumer structs.
   - Prefer robust impl generation:
     - handle struct-only derive with clear compile error for unsupported items
     - preserve generics with `split_for_impl` when applicable

4. **Prevent warning regressions in consumer crate.**
   - If the generated method ignores fields, ensure generated code references fields (`let _ = &self.field;`) to avoid dead-code/never-read warnings in strict tasks.
   - Rebuild and confirm no warnings printed.

5. **Verify runtime behavior.**
   - Run binary (`cargo run -p <app>` or absolute path) and confirm non-empty stdout.

6. **Write required status artifact exactly as specified.**
   - Include success/failure flags, absolute binary path, and issue count.
   - Keep key names and formatting exact.

---

## Common Pitfalls

- **Stopping at file inspection without full compiler output.**  
  In all runs, initial suspicion was correct, but confirmation required waiting for `cargo build` to finish.

- **Fixing consumer code instead of macro output.**  
  The repeated `E0186` errors (one per `#[derive]`) came from one macro bug; patch macro generation once.

- **Method signature drift in generated impls.**  
  `fn describe()` vs `fn describe(&self)` caused every derive site to fail.

- **Ignoring warning-free requirement.**  
  Even after error fixes, strict tasks may fail if warnings remain; generated field reads are a practical guardrail.

- **Incorrect solution file schema.**  
  Tests validated exact keys and executable binary path; malformed status file can fail otherwise-correct code.

---

## Verification Strategy

Run this sequence after edits:

1. `cargo build` at workspace root  
   - Expect success for both crates.
   - Confirm absence of warnings in output.

2. `cargo run -p app` (or run absolute binary)  
   - Expect successful execution and non-empty output.

3. Validate binary path from build artifacts  
   - Typically `/workspace/target/debug/app` in this layout.

4. Write and re-open solution/status file  
   - Confirm required keys and values exactly:
     - `MACRO_CRATE_STATUS=success`
     - `APP_CRATE_STATUS=success`
     - `BINARY_PATH=<absolute path>`
     - `ISSUES_FIXED=<int>`

This strategy is validated by all three successful runs: same root error, macro-side fix, clean build, successful binary run, and passing tests.
