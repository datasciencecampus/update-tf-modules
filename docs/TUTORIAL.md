# Getting Started: Automating Your First Module Update

This tutorial walks you through setting up `update-tf-modules` from scratch. By the end you will have a scheduled workflow that automatically opens a pull request whenever a new version of your Terraform modules is released — with no manual version-tracking required.

**Time:** approximately 15 minutes.

---

## What you'll need

- A GitHub repository containing Terraform files
- At least one Terraform module sourced from GitHub or the Terraform Registry
- Permission to create files and commit to the repository's default branch

---

## Step 1: Find your module source strings

Open a Terraform file that contains a `module` block and look at the `source` line. The format will tell you which module type to use in the manifest.

**GitHub-hosted module** — the source contains a Git URL and a `?ref=` parameter:

```hcl
module "remote_state" {
  source = "git::https://github.com/your-org/terraform-gcs-remote-state.git?ref=abc1234"
}
```

Note down:
- Everything before (and not including) the version/SHA — this is your `source_prefix`. In the example above that's `git::https://github.com/your-org/terraform-gcs-remote-state.git?ref=`
- The repository slug — `your-org/terraform-gcs-remote-state`

**Terraform Registry module** — the source is in `namespace/name/provider` format, with a separate `version` line:

```hcl
module "network" {
  source  = "terraform-google-modules/network/google"
  version = "= 9.0.0"
}
```

Note down the `source` value — `terraform-google-modules/network/google`. That's all you need.

---

## Step 2: Create the manifest

The manifest is a YAML file that tells the tool which modules to manage and where to find them in your repository. Create `.github/update-modules-manifest.yml`:

```yaml
modules:
  - name: remote-state           # A label used in logs and PR comments
    type: github
    repo: your-org/terraform-gcs-remote-state
    source_prefix: "git::https://github.com/your-org/terraform-gcs-remote-state.git?ref="
    glob: "terraform/**/*.tf"    # Which files to scan for this module
```

If you also have a Registry module, add it to the same list:

```yaml
modules:
  - name: remote-state
    type: github
    repo: your-org/terraform-gcs-remote-state
    source_prefix: "git::https://github.com/your-org/terraform-gcs-remote-state.git?ref="
    glob: "terraform/**/*.tf"

  - name: network
    type: registry
    source: terraform-google-modules/network/google
    glob: "terraform/**/*.tf"
```

> **`source_prefix` explained:** The tool finds your module in the `.tf` file by looking for a line that starts with this exact string, then replaces what follows it with the new version. Copy it carefully from your source file — any mismatch means the module won't be found. The string should end just before the version or commit SHA.

---

## Step 3: Create the workflow file

Create `.github/workflows/update-terraform-modules.yml`:

```yaml
name: Update Terraform Modules

on:
  schedule:
    - cron: '0 9 * * 1'   # Every Monday at 09:00 UTC
  workflow_dispatch:        # Allows manual runs from the Actions tab

jobs:
  update:
    permissions:
      contents: write        # Required to create branches and commits
      pull-requests: write   # Required to open pull requests
    uses: datasciencecampus/update-tf-modules/.github/workflows/update-tf-modules.yml@v1
    with:
      manifest_path: .github/update-modules-manifest.yml
      terraform_root: terraform
```

The `permissions` block is required. Without `contents: write` and `pull-requests: write` declared at the job level, the workflow will fail even if a token is supplied.

---

## Step 4: Commit and do a manual test run

Commit both new files and push:

```bash
git add .github/update-modules-manifest.yml .github/workflows/update-terraform-modules.yml
git commit -m "chore: add automated Terraform module update workflow"
git push
```

Then trigger the workflow manually to see it in action before waiting for Monday:

1. In your repository, go to the **Actions** tab
2. Select **Update Terraform Modules** from the left sidebar
3. Click **Run workflow** → **Run workflow**

---

## Step 5: Check the result

Once the run completes, check the workflow log in the Actions tab. For a successful update run you'll see output like:

```
Updated GitHub module in terraform/main.tf to def5678abc123
Completed module update run. Replacements made: 1
```

**If a newer version was found:** A pull request is opened on your repository with a title like `chore: update Terraform modules`. The diff will show the updated `?ref=` or `version` values in your `.tf` files. Review it and merge when ready.

**If you're already up to date:** The output will read `Replacements made: 0` and no PR is created. This is expected — it means all your modules are already at the latest version.

**If the run shows `Replacements made: 0` but you expected an update:** The most likely cause is a `source_prefix` that doesn't exactly match the source line in your `.tf` file. The tool does a literal string match, so even a small difference (a trailing space, a missing `?ref=`) means it won't find the module. Compare your manifest's `source_prefix` character-by-character against the file. A `[SKIP]` line in the logs means the API couldn't resolve a version; an `[ERROR]` line means an API call failed. See [Permissions & Troubleshooting](PERMISSIONS_TROUBLESHOOTING.md) for a full list of errors and fixes.

---

## What happens on subsequent runs

The workflow runs automatically each Monday. If a new release of any managed module is published during the week, it opens a new PR. If nothing has changed, it does nothing. You don't need to think about it again until a PR appears.

---

## Next steps

- **Add more modules:** Expand the `modules` list in your manifest. See [Manifest Schema Reference](MANIFEST_SCHEMA.md) for all available fields, including how to target specific files and how to control whether versions are pinned to a tag or a commit SHA.
- **Change the schedule:** Update the `cron` value — for example `'0 9 * * *'` for daily runs.
- **Pin to a commit SHA:** Replace `@v1` with a full commit SHA for stricter supply-chain control. See [Consumer Setup](CONSUMER_SETUP.md) for guidance.
- **Understand the internals:** See [Architecture & Design](ARCHITECTURE.md) for how version discovery, file patching, and the GitHub/Registry split work.
