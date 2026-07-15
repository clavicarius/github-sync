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

### 4) Idempotent rerun / race-condition safety

Case: computed tag already exists on `origin` (e.g. rerun or concurrent run already pushed it).

- Workflow checks remote tags before creating the new tag.
- If tag exists:
  - run exits successfully
  - no additional tag is created
  - no push is performed

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
