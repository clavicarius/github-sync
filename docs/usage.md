# Usage Guide

## Overview

`gh_sync_labels.py` synchronizes GitHub repository labels using a CSV configuration file.

The CSV file represents the desired state.

The tool compares:

```
CSV configuration
        |
        v
GitHub repository labels
```

and applies the required changes.

Supported actions:

- create missing labels
- update changed labels
- remove obsolete labels
- export existing labels
- preview changes without modifying GitHub

---

# Prerequisites

Before using the tool, ensure the following requirements are met.

## Python

Required:

```
Python 3.12+
```

Verify:

```bash
python --version
```

---

## GitHub CLI

The tool uses the GitHub CLI (`gh`) for all repository operations.

Install:

https://cli.github.com/

Verify:

```bash
gh --version
```

---

## Authentication

Authenticate GitHub CLI:

```bash
gh auth login
```

Verify access:

```bash
gh repo view
```

The authenticated user requires permissions to manage repository labels.

---

# Basic Usage

## Synchronize labels

Run:

```bash
python gh_sync_labels.py
```

Default behavior:

- uses the current repository
- reads `labels.csv`
- creates missing labels
- leaves existing labels unchanged

Example output:

```
INFO Repository: my-org/my-repository
INFO Loading labels from labels.csv
INFO Loaded 24 labels from CSV
INFO Creating label: bug
INFO Skipping unchanged label: feature
INFO Done.
```

---

# Command Line Options

## `--repo`

Specify a repository explicitly.

Format:

```
owner/repository
```

Example:

```bash
python gh_sync_labels.py \
  --repo my-org/my-project
```

If omitted, the repository is detected automatically from the current Git repository.

---

## `--csv`

Specify the CSV configuration file.

Default:

```
labels.csv
```

Example:

```bash
python gh_sync_labels.py \
  --csv config/github-labels.csv
```

---

## `--overwrite`

Update existing labels.

Without this option:

- existing labels are preserved

With this option:

- changed colors are updated
- changed descriptions are updated

Example:

```bash
python gh_sync_labels.py \
  --overwrite
```

Update conditions:

A label is updated only if one of these values changed:

- color
- description

Unchanged labels are skipped.

---

## `--prune`

Remove labels that are not defined in the CSV.

Example:

```bash
python gh_sync_labels.py \
  --prune
```

The tool calculates:

```
Existing GitHub labels
        -
CSV labels
        =
Labels to remove
```

Only obsolete labels are deleted.

Example:

GitHub:

```
bug
feature
legacy
```

CSV:

```
bug
feature
```

Result:

```
bug       kept
feature   kept
legacy    deleted
```

---

## `--dry-run`

Preview changes without modifying GitHub.

Example:

```bash
python gh_sync_labels.py \
  --dry-run
```

The tool shows:

- labels to create
- labels to update
- labels to delete

No changes are applied.

Recommended before using:

```bash
--overwrite --prune
```

on production repositories.

Example:

```
INFO Repository: my-org/my-project

INFO [DRY-RUN] Create label:
priority: high

INFO [DRY-RUN] Update label:
feature

INFO [DRY-RUN] Delete label:
deprecated
```

---

## `--export`

Export existing GitHub labels into a CSV file.

Example:

```bash
python gh_sync_labels.py \
  --export labels-backup.csv
```

Output:

```csv
Category;Label;Color;Description
;bug;D73A4A;"🐞 A bug that needs to be fixed."
;feature;1D76DB;"✨ A new feature."
```

Use cases:

- create an initial configuration
- backup current labels
- migrate labels between repositories

---

## `--debug`

Enable debug logging.

Example:

```bash
python gh_sync_labels.py \
  --debug
```

Useful for troubleshooting:

- GitHub CLI calls
- CSV parsing
- synchronization decisions

---

# Common Workflows

## Initial Setup

When introducing label management to an existing repository:

### Step 1

Export current labels:

```bash
python gh_sync_labels.py \
  --export labels.csv
```

### Step 2

Review and adjust:

```
labels.csv
```

### Step 3

Test:

```bash
python gh_sync_labels.py \
  --dry-run
```

### Step 4

Apply:

```bash
python gh_sync_labels.py \
  --overwrite \
  --prune
```

---

# CI/CD Usage

Recommended command for automated environments:

```bash
python gh_sync_labels.py \
  --overwrite \
  --prune
```

This ensures:

- CSV is the source of truth
- repository labels stay consistent
- obsolete labels are removed

---

# GitHub Actions Example

```yaml
name: Sync GitHub Labels

on:

  workflow_dispatch:

  push:
    branches:
      - main


jobs:

  labels:

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

# Exit Codes

The tool uses standard exit codes.

| Code | Meaning |
|---|---|
| `0` | Successful execution |
| `1` | Error occurred |

Errors include:

- missing CSV file
- invalid CSV format
- GitHub CLI failure
- authentication problems
- invalid label definition

---

# Recommended Production Process

For production repositories:

1. Change CSV

```
labels.csv
```

2. Validate changes:

```bash
python gh_sync_labels.py \
  --dry-run
```

3. Apply:

```bash
python gh_sync_labels.py \
  --overwrite \
  --prune
```

4. Commit CSV changes together with repository changes.

---

# Troubleshooting

## GitHub CLI authentication error

Check:

```bash
gh auth status
```

Login again:

```bash
gh auth login
```

---

## Repository cannot be detected

Specify:

```bash
python gh_sync_labels.py \
  --repo owner/repository
```

---

## Labels are not updated

Ensure:

```bash
--overwrite
```

is enabled.

---

## Labels are not deleted

Ensure:

```bash
--prune
```

is enabled.

The tool never deletes labels unless explicitly requested.

---

# Best Practices

Recommended:

✅ Keep `labels.csv` under version control  
✅ Review changes using `--dry-run`  
✅ Use `--overwrite --prune` in controlled environments  
✅ Run synchronization through GitHub Actions  
✅ Keep label descriptions meaningful  

Avoid:

❌ Manual label changes in GitHub UI  
❌ Running `--prune` without reviewing changes  
❌ Maintaining multiple label definitions
