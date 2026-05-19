# update-tf-modules
A workflow to automate module updates in terraform projects

## Reusable Workflow Versioning Policy

Consumers should reference a stable major tag, not main.

- Recommended caller reference: `@v1`
- Do not reference: `@main`

### Compatibility Contract

- v1.x.y: no breaking changes to existing inputs, secrets, or outputs
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
