# Versioning

Automatic semantic version tags are managed by a GitHub Actions workflow.

- Trigger: push to `main` (tag pushes are not a trigger); `pull_request` runs in dry-run mode.
- Full tag format: `v<major>.<minor>.<patch>` (only tags matching `^v[0-9]+\.[0-9]+\.[0-9]+$` are considered).
- Increment strategy: choose the highest existing full tag and increment **patch** only.
- Initial version: `v0.1.0` if no matching tags exist.
- Monotonicity: versions are globally monotonically increasing across all major versions (gaps allowed).
- Moving major tag: update `v<major>` to point to the same commit as the newly created full tag.
- Recursion protection: the workflow triggers on branch pushes only (not on tag pushes).

## Operational examples

### 1) First run (no existing semantic version tags)

Repository has no tags matching `v<major>.<minor>.<patch>`.

- Push to `main` triggers workflow.
- Computed next tag: `v0.1.0`
- Moving major tag: `v0`
- Result:
  - create `v0.1.0`
  - move/create `v0` to same commit

### 2) Normal run (existing semantic version tags)

Existing tags include e.g. `v0.1.0`, `v0.1.1`, `v0.1.2`.

- Push to `main` triggers workflow.
- Highest semantic version tag is `v0.1.2`.
- Computed next tag: `v0.1.3`
- Moving major tag: `v0`
- Result:
  - create `v0.1.3`
  - force-move `v0` to the commit of `v0.1.3`

### 3) Pull request dry-run

- `pull_request` event triggers workflow.
- Workflow computes next full tag and major tag.
- Result:
  - values are shown in job summary
  - **no tags are created**
  - **no tags are pushed**

### 4) Serialization + idempotent rerun safety

Case: multiple `main` pushes happen close together, or a rerun sees an already-created full tag.

- Workflow-level `concurrency` groups runs per event/ref. For `push` to `main` runs queue (`cancel-in-progress: false`) so every push gets a tag. For `pull_request` stale runs are cancelled (`cancel-in-progress: true`) since dry-runs have no side effects.
- Workflow checks remote tags before creating the new full tag.
- If the full tag already exists:
  - run exits successfully
  - no additional full tag is created
  - moving major tag is still force-updated to point to that full tag

### 5) Non-semver tags present

Repository contains tags that do not match strict semver format with `v` prefix (e.g. `release-1`, `1.2.3`, `v1.2`).

- These tags are ignored for version calculation.
- Only tags matching `^v[0-9]+\.[0-9]+\.[0-9]+$` are considered.

### 6) Moving major tag behavior

When creating a new full tag in a major line, the corresponding major tag is updated.

Example:

- new full tag: `v2.4.9`
- moving major tag updated to: `v2`
- `v2` points to the same commit as `v2.4.9`
