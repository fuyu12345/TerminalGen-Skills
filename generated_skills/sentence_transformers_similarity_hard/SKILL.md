---
name: recovering-central-document-from-embeddings
description: Recover central-document similarity outputs from precomputed embeddings, including mislabeled or corrupted-looking embedding files, and produce validated JSON results. Use when a task asks for the most central document by average cosine similarity.
---

# Recovering Central Document from Embeddings

## When to Use

Use this skill when:

- A task provides precomputed embedding vectors and document IDs.
- The goal is to find the single document with highest **average cosine similarity** to all others.
- The expected output is a JSON file with fields like `central_doc_id` and `average_similarity`.
- The embedding file appears unreadable despite a `.npz` extension (e.g., mislabeled text/script content).

---

## Minimal Reliable Workflow

1. **Inspect the input file before assuming format.**
   - Run quick checks:
     - `ls -lah <path>`
     - `python -c "print(open('<path>','rb').read(64))"`
   - If first bytes look like text/code (e.g., `import numpy as np`), treat it as mislabeled content, not a real NPZ.

2. **If file is a generator script, execute it to materialize the real archive.**
   - If the mislabeled file is valid Python that writes the NPZ, run it once:
     - `python3 /workspace/embeddings/document_embeddings.npz`
   - Re-open afterward as NPZ.

3. **Load arrays with pickle enabled when `doc_ids` may be object dtype.**
   - Use:
     - `np.load(path, allow_pickle=True)`
   - This avoids `ValueError: Object arrays cannot be loaded when allow_pickle=False`.

4. **Compute cosine similarities efficiently with matrix multiplication.**
   - Normalize rows: `X = E / ||E||`.
   - Similarity matrix: `S = X @ X.T`.
   - Exclude self-similarity:
     - `avg = (S.sum(axis=1) - np.diag(S)) / (n - 1)`.
   - Select `argmax(avg)`.

5. **Write exact output schema.**
   - Create output directory.
   - Write JSON with exactly:
     - `central_doc_id` (string)
     - `average_similarity` (float rounded to 4 decimals)

---

## Common Pitfalls

- **Trusting file extension alone (`.npz`)**
  - In all runs, initial `np.load` failed with unpickling errors because the `.npz` file actually contained Python source text.
  - Guardrail: always inspect file header bytes first.

- **Using `allow_pickle=False` on object arrays**
  - After regenerating data, loading `doc_ids` failed when pickle was disabled.
  - Guardrail: if `doc_ids` stored as `dtype=object`, use `allow_pickle=True` for trusted local task artifacts.

- **Overcomplicating multi-format loaders too early**
  - Robust fallback loaders are fine, but first-byte inspection + reading file contents found root cause faster and more reliably than blind loading attempts.

- **Marking complete before re-checking output file**
  - Early attempts attempted completion with missing `/workspace/results/central_document.json`.
  - Guardrail: always `cat` (or parse) final JSON before completion.

---

## Verification Strategy

Run checks aligned with observed test assertions:

1. **File existence**
   - `test -f /workspace/results/central_document.json`

2. **Valid JSON and required fields only**
   - Parse JSON and assert keys are exactly:
     - `{"central_doc_id", "average_similarity"}`

3. **Type/range checks**
   - `central_doc_id` is string.
   - `average_similarity` is numeric and in `[0, 1]` (as expected for this embedding set).

4. **Membership check**
   - Confirm `central_doc_id` is present in input `doc_ids`.

5. **Correctness check (most important)**
   - Recompute averages from embeddings and verify output doc equals `argmax(avg)`.
   - This directly matches the grader’s “actually most central” assertion.

---

## References to Load On Demand

- NumPy cosine workflow snippet:
  - `E -> normalize -> S = X @ X.T -> avg excluding diagonal -> argmax`
- Quick forensic check for mislabeled binaries:
  - `python - <<'PY'\nprint(open(path,'rb').read(64))\nPY`
