# Setting Up the Reusable Workflow

This guide walks you through integrating `update-tf-modules` into your repository.

## Quick Start

### 1. Create a Manifest File

Copy [examples/update-modules-manifest.example.yml](../examples/update-modules-manifest.example.yml) into your repository:

```bash
mkdir -p .github
curl -o .github/update-modules-manifest.yml \
  https://raw.githubusercontent.com/datasciencecampus/update-tf-modules/main/examples/update-modules-manifest.example.yml
```

Or manually create `.github/update-modules-manifest.yml`. See [Manifest Schema](../reference/manifest-schema.md) for detailed field descriptions and validation rules.

### 2. Call the Workflow

In your GitHub Actions workflow, add a job that calls this reusable workflow. Note that your GitHub Actions job must declare the required permissions:

```yaml
permissions:
  contents: write
  pull-requests: write
```

Without these permissions, PR creation will fail even if a token is supplied. See [Permissions & Troubleshooting](permissions-troubleshooting.md) for full details and token configuration. For production, it is recommended to pin to a full commit SHA.

```yaml
jobs:
  update:
    permissions:
      contents: write
      pull-requests: write
    uses: datasciencecampus/update-tf-modules/.github/workflows/update-tf-modules.yml@<full-commit-sha> # v1.2.3
    with:
      manifest_path: .github/update-modules-manifest.yml
      terraform_root: terraform
      base_branch: main
      create_pr: true
    secrets:
      token: ${{ secrets.GITHUB_TOKEN }}
```

**For convenience:** Track the v1 tag (receives non-breaking updates automatically):

```yaml
uses: datasciencecampus/update-tf-modules/.github/workflows/update-tf-modules.yml@v1
```

## Example: Minimal Workflow File

Save this as `.github/workflows/update-terraform-modules.yml`:

```yaml
name: Update Terraform Modules

on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday
  workflow_dispatch:  # Manually trigger

jobs:
  update:
    permissions:
      contents: write
      pull-requests: write
    uses: datasciencecampus/update-tf-modules/.github/workflows/update-tf-modules.yml@v1
    with:
      manifest_path: .github/update-modules-manifest.yml
      terraform_root: terraform
      base_branch: main
      create_pr: true
    secrets:
      token: ${{ secrets.GITHUB_TOKEN }}

  on-change:
    if: ${{ needs.update.outputs.changed == 'true' }}
    runs-on: ubuntu-latest
    needs: update
    steps:
      - name: PR Created
        run: |
          echo "Module updates detected"
          echo "PR: ${{ needs.update.outputs.pr_url }}"
```

## Workflow Inputs and Outputs

### Optional Inputs

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `manifest_path` | string | `.github/update-modules-manifest.yml` | Path to your manifest file |
| `terraform_root` | string | `terraform` | Root folder containing Terraform files |
| `base_branch` | string | `main` | PR base branch |
| `create_pr` | boolean | `true` | Whether to open a PR (or just commit) |
| `updater_ref` | string | `v1` | Git ref (branch/tag/SHA) for the update-tf-modules repository |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| `changed` | string | `"true"` or `"false"` — whether Terraform files changed |
| `pr_number` | string | PR number (empty if not created) |
| `pr_url` | string | PR URL (empty if not created) |

## Troubleshooting

For detailed troubleshooting including permission errors, token configuration, rate limiting, and manifest validation issues, see [Permissions & Troubleshooting](permissions-troubleshooting.md).

## Next Steps

- [Detailed Manifest Schema Reference](../reference/manifest-schema.md) — Field-by-field guide with examples
- [Architecture & Design](../explanation/architecture.md) — Why certain decisions were made
- [Permissions & Troubleshooting](permissions-troubleshooting.md) — Token, permissions, exit codes, debugging
