# update-tf-modules
A workflow to automate module updates in terraform projects

## Reusable Workflow Versioning Policy

Consumers should reference a stable major tag, not main.

- Recommended caller reference: `@v1`
- Do not reference: `@main`

### Compatibility Contract

- v1.x.y: no breaking changes to existing inputs, secrets or outputs
- v1 minor releases (x): additive only (new optional inputs/outputs, internal hardening)
- v1 patch releases (y): bug fixes and security fixes only
- v2.0.0+: allowed to introduce breaking contract changes

### What `@v1` Means For Callers

- `@v1` tracks the latest compatible v1 release
- You will receive additive improvements and fixes without contract-breaking changes
- Breaking contract changes will only be introduced in `@v2`

### Upgrade Guidance For Callers

- Default track: `@v1` for automatic non-breaking updates
- Strict pinning: use an exact version tag such as `@v1.1.1` when change control is required

## Call This Workflow

Use this repository workflow as a reusable contract from another workflow.

```yaml
uses: ONS/cloud_enablement/update-tf-modules/.github/workflows/update-tf-modules.yml@v1
```

### Manifest Example For Callers

- Consumer template: `examples/update-modules-manifest.example.yml`
- Repository runtime manifest: `.github/update-modules-manifest.yml`

Use the example file as the starting point in your own repository, then set:

- `manifest_path` to your manifest location
- `terraform_root` to your Terraform root folder

Quick start for new consumers:

1. Copy `examples/update-modules-manifest.example.yml` into your repository (for example `.github/update-modules-manifest.yml`).
2. Replace placeholder module values (`repo`, `source_prefix`, `source`) with your real module sources.
3. Call this reusable workflow and set `manifest_path` to that copied file.

### Required Inputs

This workflow currently has no required inputs.

### Optional Inputs

- `manifest_path` (string, default: `.github/update-modules-manifest.yml`): path to the updater manifest in the target repository.
- `terraform_root` (string, default: `terraform`): root folder to diff, format-check and include in PR paths.
- `python_version` (string, default: `3.12`): Python runtime used for the update tool.
- `base_branch` (string, default: `main`): PR base branch.
- `pr_branch_name` (string, default: `automation/update-terraform-modules`): branch name used for update commits.
- `create_pr` (boolean, default: `true`): whether to open a PR when changes are detected.

### Secrets

- `token` (optional): token used for GitHub API and PR creation.

Token behavior:

- If `token` is passed, it is used.
- If `token` is not passed, the workflow falls back to `GITHUB_TOKEN`.

### Outputs

- `changed` (`"true"` or `"false"`): whether Terraform files changed under `terraform_root`.
- `pr_number` (string, empty when not created): PR number when PR creation runs successfully.
- `pr_url` (string, empty when not created): PR URL when PR creation runs successfully.

### Manifest Schema Reference

Top-level requirements:

- The manifest must be a YAML mapping.
- It must contain a non-empty `modules` list.
- Each item in `modules` must be a mapping.

Per-module requirements:

- Common required fields:
	- `name` (string)
	- `type` (`github` or `registry`)
- Exactly one target selector must be provided:
	- `glob` (string)
	- `file` (string)
	- `files` (non-empty list of strings)

GitHub module (`type: github`) required fields:

- `repo` (string, format like `owner/repo`)
- `source_prefix` (string, should include `?ref=` suffix)

GitHub module optional fields:

- `lookup` (`release` or `tag`, default: `release`)
- `pin` (`sha` or `tag`, default: `sha`)

Registry module (`type: registry`) required fields:

- `source` (string, for example `terraform-google-modules/network/google`)

Path behavior:

- `glob`, `file` and `files` paths are resolved relative to repository root.

### Minimal Caller Example (Cross Repository)

```yaml
name: Run shared module updater

on:
  workflow_dispatch:

jobs:
  update:
    uses: ONS/cloud_enablement/update-tf-modules/.github/workflows/update-tf-modules.yml@v1
    with:
      manifest_path: .github/update-modules-manifest.yml
      terraform_root: terraform
      base_branch: main
      create_pr: true
    secrets:
      token: ${{ secrets.UPDATE_MODULES_TOKEN }}

  on-change:
    if: ${{ needs.update.outputs.changed == 'true' }}
    runs-on: ubuntu-latest
    needs: update
    steps:
      - name: Print PR details
        run: |
          echo "PR number: ${{ needs.update.outputs.pr_number }}"
          echo "PR URL: ${{ needs.update.outputs.pr_url }}"
```

### Failure Modes And Exit Behavior

- If no files change under `terraform_root`, the workflow succeeds with `changed=false` and PR creation is skipped.
- If `create_pr=false`, the workflow still runs updates and checks, but does not create a PR.
- If Terraform formatting check fails when changes exist, the workflow fails.
- If PR creation fails (permissions, token scope, branch protection or API errors), the workflow fails.
