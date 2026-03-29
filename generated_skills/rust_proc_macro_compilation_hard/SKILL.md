---
name: repairing-rust-proc-macro-compilation
description: Repair Rust procedural macro crates by fixing proc-macro manifest settings, macro entry signatures, and missing syn/quote types. Use when `cargo build` fails in a proc-macro crate after refactors.
---

# Repairing Rust Proc-Macro Compilation

## When to Use

Use this skill when a Rust crate with `#[proc_macro]` / `#[proc_macro_derive]` stops compiling and errors mention things like:

- wrong token stream types (`TokenStream2` vs `proc_macro::TokenStream`)
- missing `syn` types (for example `DeriveInput`)
- proc-macro crate export restrictions
- warnings treated as failures (deprecated manifest keys, unused variables)

This pattern was stable across all three successful runs.

## Minimal Reliable Workflow

1. **Inspect manifest and macro source first.**
   - Open `Cargo.toml` and `src/lib.rs`.
   - Confirm crate is intended to be a proc-macro crate.

2. **Run one clean build and wait for completion before issuing more commands.**
   - Run `cargo build`.
   - Do not queue file-inspection commands while build is still running; wait for full diagnostics.

3. **Fix proc-macro manifest warnings immediately.**
   - In `[lib]`, use:
     - `proc-macro = true`  
     - not deprecated `proc_macro = true`.

4. **Correct procedural macro entrypoint signatures.**
   - Use `proc_macro::TokenStream` for public macro entry functions:
     - `#[proc_macro_derive(...)] pub fn ... (input: TokenStream) -> TokenStream`
     - `#[proc_macro] pub fn ... (input: TokenStream) -> TokenStream`

5. **Import required `syn` types explicitly.**
   - Add missing imports such as `DeriveInput` when using:
     - `parse_macro_input!(input as DeriveInput)`

6. **Remove or refactor invalid exports in proc-macro crates.**
   - Avoid exporting arbitrary `pub fn` items from a proc-macro crate unless they are macro entrypoints.
   - Keep helper functions private if needed.

7. **Eliminate warnings from leftover refactor code.**
   - Rename intentionally unused macro inputs to `_input`.
   - Remove dead/unused helper code that creates warnings.

8. **Rebuild and (if required by task) write result artifact.**
   - Re-run `cargo build` until clean.
   - If benchmark requires a summary file, write exact requested format and verify with `cat`.

## Common Pitfalls

- **Queuing commands while `cargo build` is still running**
  - Causes interleaved/mangled terminal output and missed diagnostics.
  - Prevent by waiting for prompt return before next command batch.

- **Using deprecated manifest key**
  - `proc_macro = true` triggers warning; strict checks may fail.
  - Replace with `proc-macro = true`.

- **Using `TokenStream2` in macro entrypoints**
  - Entrypoints require `proc_macro::TokenStream`.
  - Keep `TokenStream2` usage internal only (if needed), with explicit imports.

- **Missing `syn::DeriveInput` import**
  - `parse_macro_input!` with `DeriveInput` fails without import.

- **Exporting non-macro public items from proc-macro crate**
  - Proc-macro crates cannot export arbitrary public items; this causes hard compile errors.

- **Ignoring warnings**
  - Unused parameter warnings (e.g., in `custom_macro`) can fail “no warnings” gates.
  - Prefix with `_` or use variable.

## Verification Strategy

Run verification in this order:

1. **Compile check**
   - `cargo build`
   - Expect success and no warnings in output.

2. **Warning gate**
   - `cargo check`
   - Expect no warnings (important because tests often enforce warning-free output).

3. **Macro crate sanity**
   - Confirm `Cargo.toml` uses `[lib] proc-macro = true`.
   - Confirm macro entrypoints use `proc_macro::TokenStream`.

4. **Task artifact validation (if requested)**
   - Ensure output file exists and matches exact line format/order.
   - Example checks: `cat /tmp/build_result.txt`, line count, key/value exactness.

## References to Load On Demand

- Rust Reference: Procedural macros (`proc_macro`, `proc_macro_derive`, export restrictions)
- `syn` docs: `DeriveInput`, `parse_macro_input!`
- `quote` docs: token generation patterns
