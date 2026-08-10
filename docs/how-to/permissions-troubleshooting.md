# Permissions, Tokens & Troubleshooting

This guide helps you diagnose and fix common issues with PR creation, token authentication and workflow execution.

## Permissions Matrix

Your GitHub Actions job must declare the required permissions for the workflow to create PRs. Here's what's required for each feature:

### PR Creation Requires

```yaml
permissions:
  contents: write      # Required: create branches and commits
  pull-requests: write # Required: create and update pull requests
```

### Without Permissions

| Action | Result | Error |
|--------|--------|-------|
| Create branch | Fails | `Resource not accessible by integration` |
| Create/update PR | Fails | `Resource not accessible by integration` |
| Read repo contents | Works | No special permission needed |

### Disabling PR Creation

If `create_pr=false`, PR permissions are **not required**:

```yaml
permissions:
  contents: write      # Still needed for commits
  # pull-requests: write  # Not needed if create_pr=false
```

## Token Configuration

The workflow uses a token for authenticated GitHub API calls and PR operations. Token behavior varies:

### Default: `GITHUB_TOKEN`

If no secret is passed to the workflow, it uses the built-in `GITHUB_TOKEN`:

```yaml
secrets:
  # token omitted → uses GITHUB_TOKEN automatically
```

**Characteristics:**
- Automatically available in all GitHub Actions
- Scoped to current repository only
- Expires at end of workflow run
- Scoped to job permissions
- Good for most use cases

### Explicit: Personal Access Token (PAT)

Pass a Personal Access Token for higher rate limits or cross-repository access:

```yaml
secrets:
  token: ${{ secrets.GH_PAT }}
```

**Setup:**
1. Generate token at https://github.com/settings/tokens
2. Select scopes:
   - `repo` — Full control of private/public repositories
   - `workflow` — Update workflows (optional)
3. Store as repository secret: https://github.com/OWNER/REPO/settings/secrets
4. Reference in workflow: `${{ secrets.GH_PAT }}`

**Characteristics:**
- Persists across workflow runs
- Can access multiple repositories
- Manual expiration and renewal required
- Less secure if leaked (not job-scoped)

### Explicit: GitHub App Token

For production automation, use a GitHub App token:

```yaml
secrets:
  token: ${{ steps.gh_app_token.outputs.token }}
```

**Setup:**
1. Create GitHub App with appropriate permissions
2. Generate token in workflow using `actions/create-github-app-token@v1`
3. Pass to reusable workflow

**Characteristics:**
- Fine-grained permission control
- Automatic expiration (1 hour)
- Audit trail for actions
- Enterprise-friendly
- More complex setup

## Troubleshooting PR Creation

### Error: "Resource not accessible by integration"

**Cause:** Missing job permissions.

**Fix:** Add permissions block to your job:

```yaml
jobs:
  update:
    permissions:
      contents: write
      pull-requests: write
    uses: datasciencecampus/update-tf-modules/.github/workflows/update-tf-modules.yml@v0
```

**Verify:** Check that `permissions` is at the job level (not workflow level).

### Error: "Failed to create PR: 403 Forbidden"

**Cause:** Token lacks required scopes or is invalid.

**Fix:**
1. If using `GITHUB_TOKEN`: verify job permissions are declared
2. If using custom token: verify token has `repo` scope and is not expired
3. Try using `GITHUB_TOKEN` first (simpler, usually works)

### Error: "Branch already exists"

**Cause:** Previous PR branch wasn't deleted or wasn't merged.

**Fix:**
1. Delete the old branch manually: `git push origin --delete automation/update-terraform-modules`
2. Retry the workflow once the branch is deleted

### Error: "Protected branch requires status checks"

**Cause:** Repository has branch protection rules that prevent automated commits.

**Fix:**
1. Go to https://github.com/OWNER/REPO/settings/branches
2. Find branch protection rule for your PR base branch
3. Options:
   - Add `github-actions` bot to dismissal list (allows automation to dismiss)
   - Disable "Require status checks to pass before merging" (less secure)
   - Use GitHub App token (may satisfy branch rules)

### Error: "Network error: Failed to reach GitHub API"

**Cause:** GitHub API is unavailable or network connectivity issue.

**Fix:**
1. Check GitHub Status at https://www.githubstatus.com/
2. Verify runner network access (if using self-hosted runner)
3. Retry the workflow after a few minutes

## Troubleshooting Module Updates

### No modules updated; PR not created

**Possible causes:**
1. No newer versions available (normal)
2. Manifest is invalid (validation error)
3. Module sources are unreachable
4. Terraform files don't match glob patterns

**Diagnose:**
1. Check workflow logs for error messages
2. Run tool locally to validate manifest:
   ```bash
   update-tf-modules --manifest-path .github/update-modules-manifest.yml
   ```
3. Verify manifest syntax and paths (see [Manifest Schema](../reference/manifest-schema.md))
4. Check that glob patterns match your Terraform files

### "Module XYZ not found"

**Cause:** Glob pattern doesn't match any files or file path is incorrect.

**Fix:**
1. Verify file paths in manifest are relative to repo root
2. Test glob pattern locally:
   ```bash
   find terraform -name "*.tf" -path "your-glob-pattern"
   ```
3. Check that files actually contain the module source block

### "Failed to fetch versions for module XYZ"

**Cause:** API error (GitHub API, Terraform Registry API, or network).

**Fix:**
1. Verify API is reachable (check GitHub Status, Registry status)
2. Verify token is valid and has correct scopes
3. Check that repository/module names are spelled correctly

### Many "unmanaged module" warnings

This warning is informational and non-blocking. It usually means Terraform modules were discovered in scanned files but are not yet represented in your manifest.

Add modules to the manifest incrementally as needed. For details on why this happens and how discovery works, see [Architecture & Design](../explanation/architecture.md).

## Exit Codes & Debugging

### Exit Code 0: Success

Workflow completed successfully. Terraform files may or may not have changed.

**Possible outcomes:**
- No modules need updates (expected)
- Updates applied and PR created
- Updates applied but `create_pr=false` (no PR created)

### Exit Code 2: Expected Error

Manifest validation failed or expected error occurred.

**Common causes:**
- Manifest file not found
- Manifest YAML syntax error
- Manifest validation error (missing required field, invalid type, etc.)
- Terraform files not found

**Debug:**
1. Check workflow logs for error message
2. Verify manifest file path is correct
3. Validate manifest syntax:
   ```bash
   cat .github/update-modules-manifest.yml | python3 -c "import sys, yaml; yaml.safe_load(sys.stdin)" && echo "Valid YAML"
   ```

### Exit Code 1: Unexpected Error

Unrecoverable error (network, permission, bug).

**Common causes:**
- GitHub API error (5xx)
- Network connectivity issue
- File system error (permission denied, disk full)
- Bug in update tool (rare)

**Debug:**
1. Check full workflow run log in Actions tab
2. Check GitHub API status (https://www.githubstatus.com/)
3. If self-hosted runner: check runner logs
4. Report issue with logs at https://github.com/datasciencecampus/update-tf-modules/issues

## Token Security Best Practices

1. **Never commit tokens:** Use GitHub Secrets, not hardcoded values
2. **Use least privilege:** Create tokens with minimum required scopes
3. **Rotate regularly:** Personal tokens don't auto-expire; manually rotate quarterly
4. **Audit access:** Review token usage in GitHub API logs
5. **Use GitHub App tokens in production:** More secure and automatically expire

## Workflow Run Inspection

To debug a specific workflow run:

1. Go to your repository → Actions tab
2. Click on the workflow run
3. Click on the `update` job
4. Scroll to see detailed logs including:
   - Module discovery output
   - API query responses
   - File updates
   - PR creation details

**Useful log sections:**
- `[WARN] Terraform modules were found...` — Unmanaged modules discovered during scanning
- `Updated GitHub module in <path> to <ref>` — A GitHub module source was rewritten
- `Updated registry module '<source>' in <path> to <version>` — A registry module version was inserted or updated
- `[SKIP] ...` — A module was skipped (for example no resolvable tag/version)
- `[ERROR] ...` — API or unexpected runtime error details
- `Completed module update run. Replacements made: <n>` — Final run summary

## See Also

- [Consumer Setup Guide](consumer-setup.md) — How to integrate the workflow
- [Manifest Schema Reference](../reference/manifest-schema.md) — Field documentation
- [Architecture & Design](../explanation/architecture.md) — How the tool works internally
