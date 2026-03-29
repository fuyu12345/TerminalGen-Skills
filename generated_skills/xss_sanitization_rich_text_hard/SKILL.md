---
name: hardening-rich-text-xss-sanitization
description: Implement defense-in-depth HTML sanitization for rich text while preserving safe formatting. Use when a CMS/editor must block XSS vectors (script tags, event handlers, dangerous URLs, obfuscation) and pass security/performance tests.
---

# Hardening Rich-Text XSS Sanitization

## When to Use

- Build or repair server-side HTML sanitization for user-submitted rich text.
- Replace brittle regex-only sanitizers that miss obfuscation or protocol tricks.
- Satisfy tests that require both:
  - **blocking XSS** (`<script>`, `on*`, `javascript:`/`data:`/`vbscript:`, SVG/embed vectors), and
  - **preserving formatting** (`p`, `b`, `i`, links, lists, headings, blockquote, code/pre).
- Meet a throughput target (e.g., 1000 docs in <5s).

## Minimal Reliable Workflow

1. **Read full test expectations before coding.**  
   Fetch tests in small chunks if terminal output truncates (observed repeatedly across runs).  
   Example: `nl -ba test_xss.py | sed -n '100,160p'`.

2. **Extract explicit security and preservation contracts.**  
   Build a checklist from assertions:
   - Must remove dangerous tags/vectors and often dangerous payload text (`alert` in tests).
   - Must keep legitimate formatting and safe links.
   - Must meet performance threshold.

3. **Implement defense-in-depth sanitizer (not regex-only).**
   - Normalize input (remove null bytes/control chars; decode entities; remove HTML comments).
   - Remove dangerous container tags and contents (`script`, `svg`, `iframe`, `object`, `embed`, etc.).
   - Parse and rebuild with strict allowlist of tags/attributes.
   - Drop all `on*` attributes and `style`.
   - Validate URL attributes with normalized scheme checks; block `javascript:`, `data:`, `vbscript:` (including obfuscated whitespace/control-char forms).

4. **Preserve only required formatting surface.**  
   Allow minimal tags and attributes needed by tests/product requirements (e.g., `a[href,title]`, headings, lists, blockquote, code/pre).

5. **Run full suite and iterate fast.**
   - Local/unit suite (in runs: `python3 test_xss.py` or `python3 -m unittest -q test_xss.py`).
   - Harness suite (in bench: `pytest /tests/test_outputs.py -rA`).

## Common Pitfalls

- **Coding against truncated test output.**  
  All successful runs had to re-read tests in narrower ranges to capture missing assertions.
- **Using simplistic regex replacements.**  
  Legacy pattern (`<script>` lowercase only, single `onclick` rule) is bypass-prone and fails obfuscation cases.
- **Removing tags but leaving payload text.**  
  Tests assert absence of strings like `alert`; strip dangerous blocks/content, not only tag wrappers.
- **Checking URL schemes without normalization.**  
  Failing to collapse whitespace/control chars allows `java\nscript:`-style bypasses.
- **Over-sanitizing and breaking legitimate content.**  
  Escaping all HTML or dropping allowed tags fails formatting-preservation tests.

## Verification Strategy

1. **Import and interface sanity**
   - Confirm file exists/imports and exports `sanitize_html`.

2. **Security regression checks (from observed assertions)**
   - Script tags (case variants, malformed spacing, entity-encoded, comment-obfuscated, null-byte obfuscated).
   - Event handlers (`onclick`, `onerror`, `onload`, `onmouseover`, multiple handlers).
   - Dangerous URLs (`javascript:`, `data:`, `vbscript:` in `href/src/action`).
   - Dangerous tags (`svg`, `iframe`, `object`, `embed`, `meta`, form-related injection).
   - CSS expression vectors via inline style removal.

3. **Formatting preservation checks**
   - Confirm expected snippets remain for `b/i`, links with safe `https`, lists, headings, blockquote, code/pre.

4. **Performance check**
   - Run the 1000-document benchmark test; ensure comfortably below threshold (all three runs passed).

## References to Load On Demand

- OWASP XSS Prevention Cheat Sheet (allowlist and context rules)
- Bleach docs (`Cleaner`, tags/attributes/protocols) if using library-based sanitization
- Python `html.parser` docs if implementing custom parser-based sanitizer
