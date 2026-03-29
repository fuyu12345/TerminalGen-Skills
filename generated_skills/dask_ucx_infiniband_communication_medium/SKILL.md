---
name: deriving-dask-ucx-config-from-cluster-spec
description: Extract UCX-related settings from a cluster specification and generate a strict Dask UCX JSON config with exact keys and values. Use when a task requires producing validated environment-variable config files from infra spec JSON in terminal workflows.
---

# Deriving Dask UCX Config from Cluster Spec

## When to Use
- Generate `/tmp/solution/...json` style deliverables from a provided cluster spec.
- Map network/UCX spec fields into exact required output keys.
- Pass strict tests that enforce:
  - file existence,
  - valid JSON,
  - exact key set (no extras),
  - expected value consistency.

## Minimal Reliable Workflow
1. **Resolve the real spec path before parsing.**  
   Treat the advertised path as potentially a file *or* directory.
   ```bash
   ls -ld /tmp/cluster_spec.json
   find /tmp/cluster_spec.json -maxdepth 3 -type f -name '*.json' -print
   ```
2. **Load spec via Python and build only required fields.**  
   Use deterministic extraction instead of manual typing.
   ```bash
   python3 - <<'PY'
   import json, os

   spec_input = '/tmp/cluster_spec.json'
   if os.path.isdir(spec_input):
       candidates = []
       for root, _, files in os.walk(spec_input):
           for fn in files:
               if fn.endswith('.json'):
                   candidates.append(os.path.join(root, fn))
       if not candidates:
           raise SystemExit("No JSON spec found")
       spec_path = sorted(candidates)[0]
   else:
       spec_path = spec_input

   with open(spec_path) as f:
       spec = json.load(f)

   out = {
       "UCX_TLS": spec["ucx"]["tls_priority"],
       "UCX_NET_DEVICES": spec["network"]["ib_device"],
       "DASK_DISTRIBUTED__COMM__UCX__ENABLED": "true"
   }

   os.makedirs('/tmp/solution', exist_ok=True)
   with open('/tmp/solution/dask_ucx_config.json', 'w') as f:
       json.dump(out, f, indent=2)
   print("spec_path:", spec_path)
   print(json.dumps(out, indent=2))
   PY
   ```
3. **Perform strict structural validation.**
   ```bash
   python3 - <<'PY'
   import json
   p='/tmp/solution/dask_ucx_config.json'
   req={"UCX_TLS","UCX_NET_DEVICES","DASK_DISTRIBUTED__COMM__UCX__ENABLED"}
   with open(p) as f:
       d=json.load(f)
   assert set(d)==req, f"Unexpected keys: {set(d)}"
   assert d["DASK_DISTRIBUTED__COMM__UCX__ENABLED"] in {"true","false"}
   print("OK", d)
   PY
   ```

## Common Pitfalls
- **Assuming `/tmp/cluster_spec.json` is always a file.**  
  In all three runs, that path was a **directory** containing `cluster_spec.json`; direct `open('/tmp/cluster_spec.json')` caused `IsADirectoryError`.
- **Using unavailable tooling for validation (`jq`).**  
  One run showed `jq: command not found`. Prefer Python (`json.load`, `python3 -m json.tool`) for portable validation.
- **Submitting after writing values without source verification.**  
  Even if guessed values pass in one instance, always confirm spec content to avoid hidden mismatches in variant tasks.
- **Adding extra fields.**  
  Tests explicitly check “no extra fields”; emit exactly the required three keys.

## Verification Strategy
Tie checks to observed test categories (`test_outputs.py`):
1. **Existence**: confirm `/tmp/solution/dask_ucx_config.json` exists.
2. **Valid JSON**: parse with `json.load` (or `python3 -m json.tool`).
3. **Required fields only**: assert exact key set equality.
4. **Value correctness**:
   - `UCX_TLS == spec["ucx"]["tls_priority"]`
   - `UCX_NET_DEVICES == spec["network"]["ib_device"]`
   - `DASK_DISTRIBUTED__COMM__UCX__ENABLED == "true"` for UCX-enabled requirement.
5. **Consistency check**: ensure values are derived from the same resolved spec file path and print that path during generation for traceability.

## References to Load On Demand
- Dask UCX env var conventions (`DASK_DISTRIBUTED__COMM__UCX__ENABLED`)
- UCX transport string semantics (`UCX_TLS`)
- Interface/device mapping for InfiniBand (`UCX_NET_DEVICES`)
