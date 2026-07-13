# GitHub Label Synchronization Tool (gh-sync-labels)

![logo](./assets/logo.png)

## Overview

`gh_sync_labels.py` is a Python-based command-line tool for managing GitHub repository labels.

The tool synchronizes GitHub labels with a CSV configuration file.

The CSV file is the **single source of truth**.

It can:

- create missing labels
- update existing labels
- remove obsolete labels
- export existing labels
- validate label configuration
- run in dry-run mode
- operate locally or inside GitHub Actions

The tool uses the GitHub CLI (`gh`) and does not require direct API access.

---

# Features

## Label Synchronization

The tool compares:

```
CSV configuration
        |
        v
GitHub repository labels
```

and applies the required changes.

Supported operations:

| Operation | Description |
|---|---|
| Create | Adds labels missing in GitHub |
| Update | Updates color and description |
| Skip | Keeps unchanged labels |
| Prune | Removes labels not defined in CSV |
| Export | Saves existing labels to CSV |
| Dry Run | Shows planned changes without modifying GitHub |

---

# Requirements

## Software

Required:

- Python 3.12+
- GitHub CLI (`gh`)
- authenticated GitHub session

Verify GitHub CLI:

```bash
gh --version
```

Authenticate:

```bash
gh auth login
```

Verify access:

```bash
gh repo view
```

---

# Installation

Clone repository:

```bash
git clone <repository>
cd <repository>
```

No Python dependencies are required.

The script uses only Python standard libraries.

---

# Repository Structure

Recommended structure:

```
.
├── gh_sync_labels.py
├── labels.csv
├── tests
│   ├── test_csv_parsing.py
│   └── test_label_comparison.py
└── README.md
```

---

# CSV Configuration

The CSV file defines all managed labels.

Default filename:

```
labels.csv
```

Format:

- UTF-8 encoding
- semicolon separated
- header required

Example:

```csv
Category;Label;Color;Description
Type;bug;D73A4A;"🐞 A bug that needs to be fixed."
Type;feature;1D76DB;"✨ A new feature."
Priority;priority: high;D73A4A;"🔴 High priority item."
Status;status: blocked;B60205;"🚫 Blocked by dependency."
```

---

# CSV Columns

| Column | Description |
|---|---|
| Category | Logical grouping, informational only |
| Label | GitHub label name |
| Color | Hex color (`RRGGBB`) |
| Description | GitHub label description |

---

# Command Line Usage

## Basic synchronization

```bash
python gh_sync_labels.py
```

Uses:

- current Git repository
- `labels.csv`

Creates missing labels only.

---

# Specify CSV File

```bash
python gh_sync_labels.py \
  --csv config/labels.csv
```

---

# Specify Repository

```bash
python gh_sync_labels.py \
  --repo organization/repository
```

Format:

```
owner/repository
```

If omitted:

The current repository is detected automatically.

---

# Update Existing Labels

By default existing labels are preserved.

Enable updates:

```bash
python gh_sync_labels.py \
  --overwrite
```

Updates happen only when:

- color changed
- description changed

---

# Remove Obsolete Labels

Enable pruning:

```bash
python gh_sync_labels.py \
  --prune
```

The tool calculates:

```
Existing GitHub Labels
        -
CSV Labels
        =
Labels to remove
```

Only labels missing from the CSV are deleted.

Labels defined in the CSV are always preserved.

---

# Full Synchronization

Recommended for controlled repositories:

```bash
python gh_sync_labels.py \
  --overwrite \
  --prune
```

Result:

```
CSV
 |
 +-- create missing labels
 |
 +-- update changed labels
 |
 +-- remove obsolete labels
```

---

# Dry Run

Preview changes without modifying GitHub:

```bash
python gh_sync_labels.py \
  --dry-run
```

Example output:

```
INFO Repository: my-org/my-repo

INFO Creating label:
bug

INFO Updating label:
feature

INFO Deleting label:
legacy-label

INFO Dry run enabled.
No changes applied.
```

---

# Export Existing Labels

Export current repository labels:

```bash
python gh_sync_labels.py \
  --export backup.csv
```

Example output:

```csv
Category;Label;Color;Description
;bug;D73A4A;"🐞 A bug"
;feature;1D76DB;"✨ Feature"
```

This can be used as a starting point for a new configuration.

---

# GitHub Actions Integration

Example workflow:

`.github/workflows/sync-labels.yml`

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

      - name: Sync labels
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          python gh_sync_labels.py \
            --overwrite \
            --prune
```

---

# Architecture

The application is divided into logical components.

```
gh_sync_labels.py

|
├── Data Model
│   └── Label
│
├── GitHub Client
│   ├── execute gh commands
│   ├── list labels
│   ├── create labels
│   ├── update labels
│   └── delete labels
│
├── CSV Handling
│   ├── load configuration
│   ├── validate structure
│   └── normalize colors
│
├── Synchronization
│   ├── compare labels
│   ├── create missing
│   ├── update changed
│   └── prune obsolete
│
└── CLI
    ├── argument parsing
    └── application startup
```

---

# Design Principles

The implementation follows these principles:

## Single Source of Truth

The CSV defines the desired state.

GitHub is only the target system.

---

## Idempotency

Running the tool multiple times produces the same result.

Example:

First run:

```
Create 24 labels
```

Second run:

```
Skip 24 labels
```

---

## Minimal GitHub Calls

The repository labels are loaded once.

Comparison happens locally.

This avoids unnecessary API calls.

---

## UTF-8 Support

The tool supports:

- emoji
- German umlauts
- multilingual descriptions

Example:

```
🐞 Fehlerbehebung
✨ Neue Funktion
```

---

# Testing

Tests are implemented using `pytest`.

Install:

```bash
pip install pytest
```

Run:

```bash
pytest -v
```

Tests cover:

## CSV Parsing

- valid CSV
- missing columns
- duplicate labels
- invalid colors
- UTF-8 handling

## Comparison Logic

- unchanged labels
- changed colors
- changed descriptions

---

# Error Handling

The tool exits with:

| Code | Meaning |
|-|-|
| 0 | Successful execution |
| 1 | Error |

Examples:

- missing CSV
- invalid repository
- GitHub CLI failure
- invalid configuration

---

# Security Considerations

The tool requires:

```
GH_TOKEN
```

or an authenticated local GitHub CLI session.

No credentials are stored.

The CSV file should not contain secrets.

---

# Recommended Workflow

For production repositories:

## 1. Export current state

```bash
python gh_sync_labels.py \
  --export labels.csv
```

---

## 2. Review CSV

Adjust:

- labels
- colors
- descriptions

---

## 3. Test changes

```bash
python gh_sync_labels.py \
  --dry-run
```

---

## 4. Apply changes

```bash
python gh_sync_labels.py \
  --overwrite \
  --prune
```

---

# Future Improvements

Potential extensions:

- JSON/YAML configuration
- organization-wide synchronization
- protected labels
- label groups
- automatic backups
- GitHub App authentication
- REST API backend
- web dashboard
- GitHub Action Marketplace release

---

# License

MIT License

Copyright (c) 2026
