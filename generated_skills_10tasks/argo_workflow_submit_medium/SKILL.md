---
name: submitting-argo-workflow-manifests
description: Create a valid Argo Workflow manifest and matching submission metadata artifact from a starter template. Use when terminal tasks require producing `completed-workflow.yaml` plus a consistency-checked JSON report for workflow submission.
---

# Submitting Argo Workflow Manifests

## When to Use

Use this skill when a task asks to:
- Complete an incomplete Argo Workflow YAML template
- Produce a second JSON report file that must match workflow values
- Satisfy validation checks like YAML/JSON syntax, Kubernetes naming, namespace, container image, and no placeholders

This pattern was consistently successful across all 3 runs, each passing all 14 verifier tests.

## Minimal Reliable Workflow

1. **Inspect the starter template first.**  
   Read the provided YAML and identify unresolved TODO/placeholder fields (for example: `my_workflow_name`, `default`, `IMAGE_HERE`, empty command, placeholder args).

2. **Write a complete workflow file at the required path.**  
   Create `/workspace/completed-workflow.yaml` with:
   - `apiVersion: argoproj.io/v1alpha1`
   - `kind: Workflow`
   - `metadata.name` in Kubernetes-compatible format (lowercase, digits, hyphens only)
   - `metadata.namespace: argo`
   - `spec.entrypoint`
   - `spec.templates` containing at least one template with `container.image`, `container.command`, and runnable `args`

3. **Use a public container image.**  
   Use a known public image tag (e.g., `alpine:3.19` or `alpine:3.20`), as done in all successful runs.

4. **Create the submission report JSON.**  
   Write `/workspace/submission-report.json` with exactly:
   - `workflow_name`
   - `namespace`
   - `container_image`  
   Set values to exactly match the workflow manifest.

5. **Perform a fast consistency check before finishing.**  
   Print both files (`cat`) and optionally parse-check with Python (`yaml.safe_load` and `json.load`) before marking complete.

## Common Pitfalls

- **Leaving template placeholders unchanged.**  
  Starter template values like `my_workflow_name`, `IMAGE_HERE`, or placeholder args are invalid for final submission and are explicitly caught by checks.

- **Using invalid workflow naming format.**  
  Underscores or uppercase in `metadata.name` will violate Kubernetes naming expectations.

- **Forgetting namespace override.**  
  Leaving `metadata.namespace: default` instead of `argo` fails metadata requirements.

- **Cross-file mismatch between YAML and JSON report.**  
  If `workflow_name` or `container_image` in JSON differs from YAML, consistency tests fail.

- **Providing structure without executable container config.**  
  Empty `command`/non-runnable template may fail container-step requirements.

## Verification Strategy

Run verification in layers, mirroring observed test coverage:

1. **Existence checks**
   - Confirm both files exist at exact required paths.

2. **Syntax checks**
   - Parse YAML and JSON (or at minimum inspect for valid structure).

3. **Workflow schema essentials**
   - Confirm `apiVersion`, `kind`, `metadata`, `spec`, `entrypoint`, `templates`.

4. **Semantic constraints**
   - Validate `metadata.name` is lowercase alphanumeric/hyphen.
   - Validate `metadata.namespace == "argo"`.
   - Validate at least one template includes `container.image` with non-placeholder public image.

5. **Cross-artifact consistency**
   - Confirm JSON `workflow_name`, `namespace`, and `container_image` match YAML values exactly.

6. **Placeholder sweep**
   - Ensure no TODO markers or placeholder tokens remain anywhere in final YAML.
