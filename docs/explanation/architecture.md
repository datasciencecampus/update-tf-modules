# Architecture and Design

This document explains the design decisions behind `update-tf-modules` and how the tool works internally.

## Design Goals

1. **Single Manifest, Multiple Modules:** One configuration file can manage module updates across different sources (GitHub, Terraform Registry).
2. **Type Safety:** Modules are strictly typed (GitHub vs Registry) to catch configuration errors early.
3. **Flexible File Selection:** Support glob patterns, single files and file lists for flexible scope management.
4. **Gradual Adoption:** Tool scans all modules in the repository and warns about unmanaged ones, enabling incremental adoption.

## Module Types: GitHub vs Registry

The tool supports two types of module sources: GitHub and Terraform Registry.

### GitHub Modules

**Use case:** Terraform modules in GitHub repositories using releases or tags for versioning.

**How it works:**
1. Tool queries GitHub API (Releases or Tags endpoint)
2. Extracts version/commit from latest release or tag
3. Updates `source` block in Terraform files with new version reference
4. Creates PR with changes

**Example workflow:**
```
GitHub Release: v2.5.0
            ↓
    GitHub API query
            ↓
  Resolve to SHA: abc123def456
            ↓
  Update source: ?ref=abc123def456
            ↓
  Commit & PR
```

**Why separate?** GitHub has releases/tags (with semantic versioning) while Terraform Registry uses semantic versioning directly. The tool treats them differently to match each ecosystem's conventions.

### Registry Modules

**Use case:** Terraform modules published to the public Terraform Registry (registry.terraform.io).

**How it works:**
1. Tool queries Terraform Registry API
2. Fetches list of available versions
3. Selects latest version using semantic version comparison
4. Updates or inserts `version` constraint in Terraform files
5. Creates PR with changes

**Example workflow:**
```
Terraform Registry: Available versions [1.0.0, 1.5.0, 2.0.0]
            ↓
 Semantic version comparison
            ↓
     Latest: 2.0.0
            ↓
  Update version: = "2.0.0"
            ↓
  Commit & PR
```

## Version Discovery & Pinning Strategies

### GitHub Modules: SHA vs Tag Pinning

**Default: `pin: sha` (most stable)**

Resolve the release/tag to its commit SHA:
- Immutable: SHA always points to the same commit
- Safe: Can't be re-tagged or force-pushed
- Explicit: Exactly which commit is in use
- Less readable: SHA is not human-meaningful

```hcl
source = "git::https://...?ref=abc123def456789"
```

**Alternative: `pin: tag` (readable but mutable)**

Use the release/tag name directly:
- Readable: Tag names like `v2.5.0` are meaningful
- Flexible: Allows re-tagging or fast-moving tags
- Mutable: Tag can be re-created or force-pushed
- Less safe: May not be the commit you tested

```hcl
source = "git::https://...?ref=v2.5.0"
```

**Recommendation:** Use `pin: sha` (default) for production to avoid unexpected behavior from tag mutations.

### GitHub Lookup: Release vs Tag Fallback

**Default: `lookup: release`**

Query GitHub Releases API first:
```
GET /repos/owner/repo/releases/latest
```

**If no releases found (404):** Automatically fall back to git tags:
```
GET /repos/owner/repo/git/refs/tags
```

This fallback allows older repositories or those using tags-only versioning to work seamlessly without configuration changes.

**Alternative: `lookup: tag`**

Query git tags directly (no releases API):
```
GET /repos/owner/repo/git/refs/tags
```

Use this if your repository doesn't use GitHub Releases (for example, older projects using annotated tags directly).

## File Discovery & Scanning

### How Module Discovery Works

1. **Scan Phase:** Tool scans all `.tf` files in `terraform_root` (default: `terraform/`)
2. **Parse Phase:** Regex extracts module blocks and their source attributes
3. **Match Phase:** Compares source attributes against modules in manifest
4. **Update Phase:** For matching modules, fetches new versions and updates files

**Example:**

```hcl
# terraform/main.tf
module "vpc" {
  source = "git::https://github.com/terraform-aws-modules/terraform-aws-vpc.git?ref=v3.14.0"
}
```

Tool detects:
- Module name: `vpc`
- Current source/version: `v3.14.0`
- Repo: `terraform-aws-modules/terraform-aws-vpc`

Then:
- Checks manifest for matching module
- Queries GitHub API for latest version
- Updates to new version (if different)

### Unmanaged Module Warnings

The tool warns when Terraform modules are found in scanned `.tf` files but are not represented in the manifest.

This is informational and non-blocking. On first run in a large repository, many warnings are expected; add modules to the manifest incrementally over time.

## Configuration via Environment Variables

The tool reads environment variables for advanced configuration (beyond what the manifest specifies).

### `UPDATE_TF_MODULES_REPO_ROOT`

Repository root for file discovery and path resolution.

- **Default:** `GITHUB_WORKSPACE` (GitHub Actions) or current directory
- **Use case:** Override repository root if running outside GitHub Actions or in a monorepo

### `UPDATE_TF_MODULES_TARGET_TERRAFORM_ROOT`

Root directory for Terraform file scanning (relative to repo root).

- **Default:** `terraform/`
- **Example values:**
  - `terraform/` — Standard layout
  - `infrastructure/` — Alternative layout
  - `.` — Scan entire repo root

**Example:**
```bash
export UPDATE_TF_MODULES_TARGET_TERRAFORM_ROOT="infrastructure/terraform"
update-tf-modules --manifest-path .github/manifest.yml
```

### `GITHUB_TOKEN` and `GH_TOKEN`

GitHub API authentication (optional). Enables authenticated API calls and allows private repository access.

- **Priority:** `GITHUB_TOKEN` checked first, then `GH_TOKEN`
- **Default:** Unauthenticated requests
- **With token:** Authenticated requests (required for private repositories)

**Example:**
```bash
export GITHUB_TOKEN="ghp_..."
update-tf-modules --manifest-path .github/manifest.yml
```

## Exit Codes

The tool uses exit codes to indicate success/failure to CI/CD pipelines.

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| `0` | Success | Terraform files may or may not have changed; PR created if changes detected and `create_pr=true` |
| `2` | Expected Error | Manifest validation failed, manifest not found or manifest file validation error. Check logs for details. |
| `1` | Unexpected Error | Unrecoverable error (network failure, permission denied, bug). Check logs and contact maintainers if needed. |

## Data Flow

Simplified overview of how the tool processes a manifest:

```
┌─────────────────────┐
│ Read Manifest YAML  │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│ Validate Structure  │
│ - Required fields   │
│ - Type checking     │
│ - Path selectors    │
└──────────┬──────────┘
           │
        (2) ← Exit code 2 if validation fails
           │ (validation OK)
           v
┌─────────────────────┐
│ Scan .tf Files      │
│ - Regex parse       │
│ - Extract modules   │
│ - Warn unmanaged    │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│ Match & Resolve     │
│ - Query APIs        │
│ - Fetch versions    │
│ - Compare to pinned │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│ Update Files        │
│ - Rewrite sources   │
│ - Preserve format   │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│ Create PR (optional)│
│ - Commit changes    │
│ - Push branch       │
│ - Open PR           │
└──────────┬──────────┘
           │
        (0) ← Exit code 0 on success
```

### Fallback Behavior

If API requests fail:
- Tool logs a warning and skips the module
- Returns exit code `0` (success) — non-blocking
- PR is created with updates for modules that succeeded

Example:
```
[ERROR] Failed to fetch versions for terraform-google-modules/network/google: 503 Service Unavailable
[SKIP] Skipping module "network" because no GitHub tag or release could be resolved.
```

## Limitations

1. **Source format assumptions:** Tool assumes module sources follow GitHub git SSH or Terraform Registry conventions. Custom source types (e.g., S3, HTTP) are not supported.

2. **Terraform file parsing:** Uses regex parsing, not full HCL parsing. Complex or unusual formatting may not be detected.

3. **Single version per module:** Each module is updated to a single version; parallel or staged version updates are not supported.

## See Also

- [Consumer Setup Guide](../how-to/consumer-setup.md) — How to use the tool
- [Manifest Schema Reference](../reference/manifest-schema.md) — Detailed field documentation
- [Permissions & Troubleshooting](../how-to/permissions-troubleshooting.md) — Debugging and error codes
