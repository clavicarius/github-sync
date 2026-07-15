# Versioning

This repository uses automated semantic version tagging via GitHub Actions.

## Scope

Version tags are created automatically on **every push to `main`**.

## Tag format

- Full version tag: `v<major>.<minor>.<patch>` (example: `v0.3.17`)
- Moving major tag: `v<major>` (example: `v0`)

The `v` prefix is mandatory for all version tags.

## Increment strategy

- Only the **patch** component is incremented automatically.
- `major` and `minor` are not auto-incremented by the workflow.
- If no semantic version tag exists yet, the initial version is:

`v0.1.0`

## Monotonicity rule

Version numbers must be monotonically increasing across the whole repository history (globally, not only within a single major line).

- Gaps in version numbers are allowed.
- Major lines/tags may be skipped.

## Moving major tags

For each created version tag `v<major>.<minor>.<patch>`, the corresponding major tag `v<major>` is moved to the same commit.

Example:

- newest full tag: `v0.5.12`
- major tag `v0` points to the commit of `v0.5.12`

## Recursion / endless-loop protection

The workflow must be configured to avoid self-trigger loops caused by its own tag operations.

Typical safeguards:

- Trigger only on branch pushes to `main` (not tag pushes), and/or
- Skip execution for commits created by automation/bot if applicable.

## Notes

- Non-semver tags are ignored when determining the next version.
- This document defines the intended behavior; the workflow implementation must follow this contract.
