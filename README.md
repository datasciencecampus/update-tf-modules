# update-tf-modules

A reusable GitHub Actions workflow that automatically opens pull requests to keep Terraform module versions up to date, for both GitHub-hosted and Terraform Registry modules.

## Versioning

This project follows SemVer and publishes two tag types with different semantics:

- `vX.Y.Z` (for example `v0.1.1`) is an immutable release point.
- `vX` (for example `v0`) is a mutable channel tag that moves to the latest stable `vX.Y.Z` release.

Use `@v0` to track the latest non-breaking updates in the current major line, or pin to a full commit SHA for maximum reproducibility. See [Consumer Setup](docs/how-to/consumer-setup.md) for pinning strategies.

## Quick Start

1. **Create a manifest** at `.github/update-modules-manifest.yml` listing the modules to manage.
2. **Declare permissions** — your workflow job needs `contents: write` and `pull-requests: write`.
3. **Call the workflow** using the `@v0` tag or a pinned commit SHA.

```yaml
jobs:
  update:
    permissions:
      contents: write
      pull-requests: write
    uses: datasciencecampus/update-tf-modules/.github/workflows/update-tf-modules.yml@v0
    with:
      manifest_path: .github/update-modules-manifest.yml
      terraform_root: terraform
      create_pr: true
```

New here? The [Getting Started Tutorial](docs/tutorials/getting-started.md) walks you through this step by step.

## Documentation

| | |
|---|---|
| [Getting Started Tutorial](docs/tutorials/getting-started.md) | Step-by-step: from zero to your first automated update PR |
| [Consumer Setup](docs/how-to/consumer-setup.md) | Full integration guide, all inputs, outputs and pinning options |
| [Manifest Schema](docs/reference/manifest-schema.md) | Complete reference for the manifest file format |
| [Architecture & Design](docs/explanation/architecture.md) | How the tool works internally and why |
| [Permissions & Troubleshooting](docs/how-to/permissions-troubleshooting.md) | Error diagnosis, token configuration and debugging |

## Troubleshooting

**PR creation failed?** Check your job `permissions` (need `contents: write` and `pull-requests: write`) and token scope. See [Permissions & Troubleshooting](docs/how-to/permissions-troubleshooting.md).

**Module updates not detected?** Verify manifest syntax and file paths. See [Manifest Schema](docs/reference/manifest-schema.md) for validation rules.

**Something else?** See [Architecture & Design](docs/explanation/architecture.md) for how module types, version discovery and file scanning work.

<!--
Maintainer Notes

✓ Unit tests automated in .github/workflows/test-suite.yml
✓ Dependabot configured in .github/dependabot.yml
✓ Documentation (docs/):
  - tutorials/getting-started.md: step-by-step getting started guide
  - how-to/consumer-setup.md: how-to guide for installing/integrating
  - reference/manifest-schema.md: precise schema reference
  - explanation/architecture.md: design decisions and module types
  - how-to/permissions-troubleshooting.md: permissions, tokens, exit codes

Future enhancements:
- Consider auto-generating Python API docs from docstrings
- Consider adding Terraform provider update support (beyond modules)
-->
