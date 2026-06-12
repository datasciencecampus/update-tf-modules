# update-tf-modules

A reusable GitHub Actions workflow that automatically opens pull requests to keep Terraform module versions up to date, for both GitHub-hosted and Terraform Registry modules.

## Versioning

This project follows SemVer. Use the `@v1` tag to track the latest non-breaking updates; see [Consumer Setup](docs/CONSUMER_SETUP.md) for pinning strategies (tag vs. commit SHA).

## Quick Start

1. **Create a manifest** at `.github/update-modules-manifest.yml` listing the modules to manage.
2. **Declare permissions** — your workflow job needs `contents: write` and `pull-requests: write`.
3. **Call the workflow** using the `@v1` tag or a pinned commit SHA.

```yaml
jobs:
  update:
    permissions:
      contents: write
      pull-requests: write
    uses: datasciencecampus/update-tf-modules/.github/workflows/update-tf-modules.yml@v1
    with:
      manifest_path: .github/update-modules-manifest.yml
      terraform_root: terraform
      create_pr: true
```

New here? The [Getting Started Tutorial](docs/TUTORIAL.md) walks you through this step by step.

## Documentation

| | |
|---|---|
| [Getting Started Tutorial](docs/TUTORIAL.md) | Step-by-step: from zero to your first automated update PR |
| [Consumer Setup](docs/CONSUMER_SETUP.md) | Full integration guide, all inputs, outputs and pinning options |
| [Manifest Schema](docs/MANIFEST_SCHEMA.md) | Complete reference for the manifest file format |
| [Architecture & Design](docs/ARCHITECTURE.md) | How the tool works internally and why |
| [Permissions & Troubleshooting](docs/PERMISSIONS_TROUBLESHOOTING.md) | Error diagnosis, token configuration and debugging |

## Troubleshooting

**PR creation failed?** Check your job `permissions` (need `contents: write` and `pull-requests: write`) and token scope. See [Permissions & Troubleshooting](docs/PERMISSIONS_TROUBLESHOOTING.md).

**Module updates not detected?** Verify manifest syntax and file paths. See [Manifest Schema](docs/MANIFEST_SCHEMA.md) for validation rules.

**Something else?** See [Architecture & Design](docs/ARCHITECTURE.md) for how module types, version discovery and file scanning work.

<!--
Maintainer Notes

✓ Unit tests automated in .github/workflows/test-suite.yml
✓ Dependabot configured in .github/dependabot.yml
✓ Documentation (docs/):
  - TUTORIAL.md: step-by-step getting started guide
  - CONSUMER_SETUP.md: how-to guide for installing/integrating
  - MANIFEST_SCHEMA.md: precise schema reference
  - ARCHITECTURE.md: design decisions and module types
  - PERMISSIONS_TROUBLESHOOTING.md: permissions, tokens, exit codes

Future enhancements:
- Consider auto-generating Python API docs from docstrings
- Consider adding Terraform provider update support (beyond modules)
-->
