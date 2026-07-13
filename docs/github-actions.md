# GitHub Actions Integration

## Overview

`gh_sync_labels.py` can be executed automatically through GitHub Actions.

The recommended approach is to manage repository labels as code:

```
labels.csv
    |
    v
Pull Request
    |
    v
Review
    |
    v
Merge
    |
    v
GitHub Actions
    |
    v
Repository Labels
```

This ensures that labels remain consistent across repositories and changes are reviewed like source code.

---

# Requirements

The workflow requires:

- repository checkout
- Python runtime
- GitHub CLI
- GitHub token permissions

The default GitHub Actions environment already provides:

- `gh` CLI
- authentication via `github.token`

No additional secrets are required.

---

# Recommended Workflow

Create:

```
.github/workflows/sync-labels.yml
```

Example:

```yaml
name: Sync GitHub Labels

on:

  workflow_dispatch:

  push:
    branches:
      - main


jobs:

  labels:

    name: Synchronize Labels

    runs-on: ubuntu-latest


    permissions:

      issues: write


    steps:

      - name: Checkout repository
        uses: actions/checkout@v4


      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"


      - name: Synchronize labels
        env:
          GH_TOKEN: ${{ github.token }}

        run: |
          python gh_sync_labels.py \
            --overwrite \
            --prune
```

---

# Workflow Triggers

## Manual Execution

Recommended during initial setup:

```yaml
on:
  workflow_dispatch:
```

Allows running the workflow manually from:

```
Actions
 |
 v
Sync GitHub Labels
 |
 v
Run workflow
```

---

## Automatic Execution

Example:

```yaml
on:

  push:
    branches:
      - main
```

Every merge to `main` updates labels automatically.

---

## Scheduled Synchronization

Optional:

```yaml
on:

  schedule:

    - cron: "0 6 * * 1"
```

Runs weekly.

Useful when:

- multiple teams modify labels
- drift detection is required

---

# Permissions

The workflow needs permission to modify issue metadata.

Required:

```yaml
permissions:
  issues: write
```

Without this permission:

```
gh label create
gh label delete
```

will fail.

---

# Security Model

The workflow uses:

```yaml
GH_TOKEN: ${{ github.token }}
```

Advantages:

- no personal access token required
- automatically managed by GitHub
- limited to repository scope
- works with branch protection

---

# Recommended Permission Scope

Use the minimum required permissions:

```yaml
permissions:

  contents: read

  issues: write
```

Explanation:

| Permission | Purpose |
|-|-|
| contents: read | Checkout repository |
| issues: write | Manage labels |

---

# Pull Request Validation Workflow

For controlled environments, separate validation and deployment.

Recommended:

```
Pull Request

    |
    v

Dry Run

    |
    v

Review Output

    |
    v

Merge

    |
    v

Apply Changes
```

---

Example:

```yaml
name: Validate Labels

on:

  pull_request:


jobs:

  validate:

    runs-on: ubuntu-latest


    permissions:

      issues: read


    steps:

      - uses: actions/checkout@v4


      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"


      - name: Validate label changes
        run:

          python gh_sync_labels.py \
            --dry-run
```

---

# Production Deployment Workflow

Recommended production command:

```bash
python gh_sync_labels.py \
  --overwrite \
  --prune
```

This guarantees:

- missing labels are created
- changed labels are updated
- obsolete labels are removed

---

# Using a Custom CSV Location

Example:

Repository:

```
.github/
└── labels/
    └── github-labels.csv
```

Workflow:

```yaml
- name: Synchronize labels

  run: |

    python gh_sync_labels.py \
      --csv .github/labels/github-labels.csv \
      --overwrite \
      --prune
```

---

# Multi-Repository Synchronization

For organizations with multiple repositories:

```
organization-labels

        |
        v

labels.csv

        |
        +------ repository-a
        |
        +------ repository-b
        |
        +------ repository-c
```

Possible implementations:

- reusable workflows
- organization-level automation
- scheduled synchronization

---

# Reusable Workflow Example

Create:

```
.github/workflows/reusable-label-sync.yml
```

Example:

```yaml
name: Reusable Label Sync

on:

  workflow_call:


jobs:

  sync:

    runs-on: ubuntu-latest


    permissions:

      issues: write


    steps:

      - uses: actions/checkout@v4


      - uses: actions/setup-python@v5
        with:

          python-version: "3.12"


      - name: Sync labels

        env:

          GH_TOKEN: ${{ github.token }}

        run:

          python gh_sync_labels.py \
            --overwrite \
            --prune
```

---

# Failure Handling

A workflow fails when:

- CSV validation fails
- GitHub authentication fails
- repository permissions are missing
- GitHub CLI returns an error

Example:

```
Process completed with exit code 1
```

The failure prevents unnoticed configuration drift.

---

# Recommended Repository Setup

Final structure:

```
.
├── gh_sync_labels.py
├── labels.csv
│
├── docs
│   ├── usage.md
│   ├── configuration.md
│   ├── architecture.md
│   └── github-actions.md
│
└── .github
    └── workflows
        └── sync-labels.yml
```

---

# Best Practices

Recommended:

✅ Store label configuration in Git  
✅ Review label changes through Pull Requests  
✅ Use `--dry-run` before enabling pruning  
✅ Use repository-scoped permissions  
✅ Automate synchronization after merge  

Avoid:

❌ Personal access tokens in workflows  
❌ Manual label maintenance  
❌ Broad workflow permissions  
❌ Unreviewed pruning

---

# Future Improvements

Possible enhancements:

- automatic dry-run comments on Pull Requests
- label drift detection reports
- organization-wide label synchronization
- scheduled compliance checks
- GitHub App authentication
- reusable marketplace action
