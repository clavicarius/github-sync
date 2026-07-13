# Architecture Guide

## Overview

`gh_sync_labels.py` is a lightweight Python application for synchronizing GitHub repository labels.

The application follows a modular architecture with clear separation between:

- configuration handling
- GitHub communication
- synchronization logic
- command-line interface

The main design goal is:

> Keep the synchronization logic independent from GitHub operations.

This makes the tool easier to test, maintain, and extend.

---

# High-Level Architecture

The overall data flow:

```
                labels.csv
                    |
                    v
            CSV Configuration
                    |
                    v
              Label Objects
                    |
                    |
                    v
        +-----------------------+
        | Synchronization Engine |
        +-----------------------+
                    |
        +-----------+-----------+
        |                       |
        v                       v
 Create / Update           Delete / Prune
        |
        v
 GitHub Repository Labels
```

---

# Component Overview

The application consists of the following components:

```
gh_sync_labels.py

|
├── Constants
|
├── Data Model
|       └── Label
|
├── GitHub Client
|       ├── execute commands
|       ├── list labels
|       ├── create labels
|       ├── update labels
|       └── delete labels
|
├── CSV Handler
|       ├── load CSV
|       ├── validate data
|       └── normalize colors
|
├── Synchronization Engine
|       ├── compare labels
|       ├── create missing
|       ├── update changed
|       └── remove obsolete
|
└── CLI Application
        ├── argument parsing
        └── execution flow
```

---

# Data Model

## Label

The central domain object.

Example:

```python
Label(
    name="bug",
    color="D73A4A",
    description="🐞 A bug that needs to be fixed."
)
```

Properties:

| Field | Description |
|-|-|
| name | GitHub label name |
| color | Hex color without `#` |
| description | Label description |

The object is immutable after creation.

Purpose:

- avoid inconsistent state
- simplify comparisons
- separate data from GitHub API representation

---

# GitHub Client

## Responsibility

The GitHub client encapsulates all communication with GitHub.

The rest of the application does not directly execute GitHub CLI commands.

Responsibilities:

- detect repository
- retrieve labels
- create labels
- update labels
- delete labels

---

## Command Flow

Example:

```
Synchronization Engine

        |
        v

GitHubClient.create_label()

        |
        v

gh label create

        |
        v

GitHub Repository
```

---

# GitHub CLI Integration

The application uses:

```
gh
```

instead of direct REST API calls.

Advantages:

- no additional Python dependencies
- uses existing GitHub authentication
- works locally and in GitHub Actions
- simple permission model

---

# CSV Processing

## Input

The CSV file is loaded as the desired state.

Example:

```csv
Category;Label;Color;Description
Type;bug;D73A4A;"🐞 A bug"
```

---

## Processing Pipeline

```
CSV File

    |
    v

DictReader

    |
    v

Validation

    |
    v

Color normalization

    |
    v

Label objects

    |
    v

Dictionary:

{
  "bug": Label(...)
}
```

---

# Synchronization Logic

The synchronization engine compares:

```
Desired Labels
       |
       -
       |
Existing Labels
```

The comparison produces three possible actions.

---

# Create

Condition:

```
CSV contains label
AND
GitHub does not contain label
```

Action:

```
gh label create
```

Example:

```
CSV:
bug

GitHub:
(no bug label)

Result:
create bug
```

---

# Update

Condition:

```
Label exists
AND
configuration differs
AND
--overwrite enabled
```

Compared fields:

- color
- description

Example:

Before:

```
bug
color=D73A4A
```

CSV:

```
bug
color=B60205
```

Result:

```
update label
```

---

# Skip

Condition:

```
Existing label == configured label
```

No action is performed.

This makes the process idempotent.

---

# Prune

Condition:

```
GitHub label exists
AND
CSV does not contain label
AND
--prune enabled
```

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
delete legacy
```

---

# Idempotency

The synchronization is designed to be idempotent.

Running:

```bash
python gh_sync_labels.py \
  --overwrite \
  --prune
```

multiple times results in the same final state.

Example:

First run:

```
Created: 24
Updated: 0
Deleted: 3
```

Second run:

```
Created: 0
Updated: 0
Deleted: 0
Skipped: 24
```

---

# Error Handling

Errors are handled at application boundaries.

Examples:

## CSV errors

- missing columns
- invalid colors
- duplicate labels

Result:

```
exit code 1
```

---

## GitHub errors

Examples:

- authentication failure
- missing permissions
- repository unavailable

Result:

```
exit code 1
```

---

# Command Line Layer

The CLI layer is responsible for:

- parsing arguments
- initializing services
- starting synchronization
- reporting results

Supported arguments:

```
--repo
--csv
--overwrite
--prune
--dry-run
--export
--debug
```

---

# Testing Architecture

Tests are separated from implementation.

Structure:

```
tests/

├── test_csv_parsing.py

└── test_label_comparison.py
```

---

## CSV Tests

Verify:

- valid configuration
- missing fields
- invalid colors
- duplicate labels
- UTF-8 support

---

## Comparison Tests

Verify:

- equal labels
- changed colors
- changed descriptions

---

# GitHub Actions Architecture

The recommended automation flow:

```
Pull Request

      |
      v

Review labels.csv

      |
      v

Merge

      |
      v

GitHub Action

      |
      v

gh_sync_labels.py

      |
      v

Repository labels updated
```

---

# Extension Points

The current design allows future enhancements.

---

## Additional Configuration Formats

Possible:

```
labels.yaml
labels.json
```

Implementation:

Replace CSV loader only.

---

## GitHub API Backend

Current:

```
gh CLI
```

Possible:

```
GitHub REST API
```

Only the GitHub client layer changes.

---

## Multiple Repository Support

Possible:

```
repositories:
  - org/project-a
  - org/project-b
```

The synchronization engine remains unchanged.

---

## Protected Labels

Possible extension:

```
protected: true
```

Prevents deletion during pruning.

---

# Design Principles Summary

The architecture follows:

| Principle | Implementation |
|-|-|
| Separation of concerns | Independent components |
| Single source of truth | CSV configuration |
| Idempotency | State comparison |
| Testability | Isolated logic |
| Minimal dependencies | Python standard library |
| Automation ready | CLI and GitHub Actions |

---

# Conclusion

`gh_sync_labels.py` is intentionally designed as a small but extensible DevOps utility.

The architecture allows teams to manage GitHub labels like any other infrastructure configuration:

- version controlled
- reviewed
- automated
- reproducible
