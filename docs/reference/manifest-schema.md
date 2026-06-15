# Manifest Schema Reference

The manifest file defines which Terraform modules to update and where to find them. This document describes the fields, their validation and their behavior.

## Top-Level Structure

The manifest must be a YAML mapping (object) with a single required key:

```yaml
modules:
  - name: example
    type: github
    # ... module fields
  - name: another
    type: registry
    # ... module fields
```

### `modules` (required, list)

A list of module definitions. Must contain at least one module. Each item must be a mapping (object) following the schema below. The `modules` key must be present, non-empty and contain only objects.

## Common Module Fields (All Types)

All modules require `name` and `type` fields.

### `name` (required, string)

A unique identifier for the module. Used in log messages and PR comments. Any non-empty string is valid.

```yaml
name: vpc
```

### `type` (required, enum)

Module type. Determines how the tool finds and updates the module. There are two allowed values: `"github"` or `"registry"`.

```yaml
type: github        # GitHub repository releases/tags
type: registry      # Terraform Registry
```

### Target Selector (required, enum)

Specify exactly one of `glob`, `file` or `files` to select which Terraform files contain this module.

#### `glob` (optional, string)

A glob pattern to match Terraform files. Resolved relative to the repository root. Glob patterns follow standard shell glob syntax; paths are relative to repository root (or `UPDATE_TF_MODULES_REPO_ROOT` environment variable); and multiple globs are not supported - use `files` for multiple patterns.

```yaml
glob: "terraform/**/*.tf"
glob: "production/vpc/*.tf"
glob: "*.tf"
```

#### `file` (optional, string)

A single Terraform file path. Resolved relative to the repository root. Exactly one file path; paths are relative to repository root; error if file does not exist.

```yaml
file: "terraform/main.tf"
```

#### `files` (optional, list of strings)

Multiple Terraform file paths. Resolved relative to the repository root. List must not be empty; each item is a string path; paths are relative to repository root

```yaml
files:
  - "terraform/prod/main.tf"
  - "terraform/staging/main.tf"
```

### Path Resolution

All paths are relative to the repository root. In GitHub Actions, the repository root is automatically set to the workspace root, so no environment variable configuration is needed; if running locally, set the `UPDATE_TF_MODULES_REPO_ROOT` environment variable if needed.

## GitHub Module Type

GitHub modules update source references to GitHub repository releases or tags.

### Required Fields

#### `repo` (required, string)

GitHub repository in `owner/repo` format (e.g., `terraform-aws-modules/terraform-aws-vpc`).

#### `source_prefix` (required, string)

The part of the source block before the version reference. Must include the `?ref=` suffix:

```yaml
source_prefix: "git::https://github.com/terraform-aws-modules/terraform-aws-vpc.git?ref="
```

### Optional Fields

#### `lookup` (optional, string, default: `"release"`)

Where to find the latest version: `"release"` (GitHub releases API, falls back to tags if none found) or `"tag"` (git tags only).

#### `pin` (optional, string, default: `"sha"`)

How to pin the version: `"sha"` pins to commit SHA (recommended); `"tag"` pins to release tag name (e.g., `v1.2.3`).

### Complete GitHub Example

```yaml
- name: vpc
  type: github
  repo: terraform-aws-modules/terraform-aws-vpc
  source_prefix: "git::https://github.com/terraform-aws-modules/terraform-aws-vpc.git?ref="
  glob: "terraform/**/*.tf"
  lookup: release
  pin: sha
```

## Registry Module Type

Registry modules update source references to Terraform Registry modules.

### Required Fields

#### `source` (required, string)

Terraform Registry module source in `namespace/name/provider` format.

```yaml
source: terraform-google-modules/network/google
source: hashicorp/aws/aws
```

### Complete Registry Example

```yaml
- name: network
  type: registry
  source: terraform-google-modules/network/google
  files:
    - terraform/prod/main.tf
    - terraform/staging/main.tf
```

## Validation Rules

All manifests must have:
- A `modules` key containing a non-empty list
- Each module must have `name`, `type` and exactly one target selector (`glob`, `file` or `files`)
- `type` must be `github` or `registry`
- GitHub modules must have `repo` and `source_prefix`
- Registry modules must have `source`
- The `files` list (if used) must not be empty

The tool will report errors for missing required fields or invalid values.

## Fallback & Special Behaviors

### GitHub Release → Tag Fallback

If `lookup: release` is set but the repository has no releases (GitHub API returns 404), the tool automatically falls back to querying git tags. This allows older repositories or those using tags-only versioning to work without configuration changes.

### Registry Version Resolution

For registry modules, the tool:
1. Queries Terraform Registry API for available versions
2. Selects the latest version
3. If no versions available, skips the module with a warning

Version comparison uses semantic versioning semantics (e.g., `v2.0.0 > v1.9.9`).

### Unmanaged Modules

The tool warns when Terraform modules are found in scanned `.tf` files but are not represented in the manifest. This warning is informational and non-blocking.

## Examples

### Minimal GitHub Module

```yaml
modules:
  - name: vpc
    type: github
    repo: terraform-aws-modules/terraform-aws-vpc
    source_prefix: "git::https://github.com/terraform-aws-modules/terraform-aws-vpc.git?ref="
    glob: "terraform/**/*.tf"
```

### Minimal Registry Module

```yaml
modules:
  - name: network
    type: registry
    source: terraform-google-modules/network/google
    file: terraform/main.tf
```

### Mixed Manifest

```yaml
modules:
  - name: aws-vpc
    type: github
    repo: terraform-aws-modules/terraform-aws-vpc
    source_prefix: "git::https://github.com/terraform-aws-modules/terraform-aws-vpc.git?ref="
    glob: "terraform/aws/**/*.tf"
    lookup: release
    pin: sha

  - name: gcp-network
    type: registry
    source: terraform-google-modules/network/google
    files:
      - terraform/gcp/main.tf
      - terraform/gcp/network.tf

  - name: hashicorp-aws
    type: registry
    source: hashicorp/aws/aws
    file: terraform/providers.tf
```

## Validating Your Manifest

To validate locally:

```bash
update-tf-modules --manifest-path .github/update-modules-manifest.yml
```

Exit code `2` indicates a validation error. Check the log output for details.

**Common issues:**
- **YAML syntax errors** — Ensure consistent indentation (spaces, not tabs)
- **Missing required fields** — Each module needs `name`, `type`, and one selector
- **Multiple selectors** — Each module must have exactly one of `glob`, `file`, or `files`
- **Empty files list** — If using `files`, it must contain at least one path
- **Invalid type** — Must be `"github"` or `"registry"` (lowercase)

## See Also

- [Consumer Setup Guide](../how-to/consumer-setup.md) — Step-by-step integration
- [Architecture & Design](../explanation/architecture.md) — Design decisions and version discovery
- [Permissions & Troubleshooting](../how-to/permissions-troubleshooting.md) — Debugging help
