# Contributing Guide

Thank you for your interest in contributing to `gh_sync_labels`.

This document explains how to set up the development environment, make changes, run tests, and submit contributions.

---

# Contribution Philosophy

`gh_sync_labels` is designed as a small, reliable DevOps utility.

Contributions should focus on:

- simplicity
- maintainability
- automation
- reliability
- backward compatibility

The goal is to keep the tool easy to understand and easy to operate.

---

# Getting Started

## Requirements

Before contributing, install:

| Tool | Version |
|-|-|
| Python | 3.12+ |
| Git | latest |
| GitHub CLI | latest |
| pytest | latest |

Verify installations:

```bash
python --version
```

```bash
git --version
```

```bash
gh --version
```

---

# Fork and Clone

Fork the repository on GitHub.

Clone your fork:

```bash
git clone https://github.com/<your-user>/gh_sync_labels.git

cd gh_sync_labels
```

Add the upstream repository:

```bash
git remote add upstream https://github.com/<organization>/gh_sync_labels.git
```

Verify:

```bash
git remote -v
```

---

# Development Setup

The project intentionally has minimal dependencies.

Install development tools:

```bash
pip install pytest
```

Verify:

```bash
pytest --version
```

---

# Project Structure

```
.
├── gh_sync_labels.py
├── labels.csv
│
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
│
├── docs/
│   ├── usage.md
│   ├── configuration.md
│   ├── architecture.md
│   ├── github-actions.md
│   └── development.md
│
├── tests/
│   ├── test_csv_parsing.py
│   └── test_label_comparison.py
│
└── .github/
    └── workflows/
        └── sync-labels.yml
```

---

# Branch Strategy

Create a dedicated branch for every change.

Recommended naming:

| Type | Example |
|-|-|
| Feature | `feature/add-yaml-support` |
| Bugfix | `fix/csv-parser-error` |
| Documentation | `docs/improve-usage-guide` |
| Refactor | `refactor/github-client` |
| Tests | `test/add-sync-tests` |

Create branch:

```bash
git checkout -b feature/my-change
```

---

# Making Changes

Before implementing changes:

1. Check existing issues
2. Review current architecture
3. Keep changes focused
4. Add tests where applicable
5. Update documentation if behavior changes

Avoid:

- unrelated refactoring
- unnecessary dependencies
- breaking CLI changes without discussion

---

# Coding Guidelines

## Python Style

Follow:

- PEP 8
- clear naming
- type hints
- small functions

Example:

```python
def load_labels(
    csv_path: Path
) -> dict[str, Label]:
    ...
```

Avoid:

```python
def load(x):
    ...
```

---

# Functions

Functions should:

- have one responsibility
- be easy to test
- avoid hidden side effects

Prefer:

```python
compare_labels()
```

over:

```python
sync_everything()
```

with multiple responsibilities.

---

# Logging

Use the existing logging system.

Example:

```python
logger.info(
    "Creating label: %s",
    label.name,
)
```

Avoid:

```python
print(
    "Creating label"
)
```

---

# Adding Dependencies

Before adding a dependency:

Ask:

- Is it required?
- Can the standard library solve the problem?
- Does it improve maintainability?

Keep the project lightweight.

---

# Testing

All changes should pass the test suite.

Run:

```bash
pytest -v
```

Expected:

```
====================

All tests passed

====================
```

---

# Test Requirements

New functionality should include tests.

Examples:

## CSV Changes

Add tests for:

- parsing
- validation
- invalid input

## Synchronization Changes

Add tests for:

- create behavior
- update behavior
- prune behavior

---

# Manual Validation

Before submitting changes:

Run:

```bash
python gh_sync_labels.py \
  --dry-run
```

Verify:

- no unexpected changes
- output is understandable
- errors are handled correctly

---

# Pull Request Process

## Before Opening a PR

Ensure:

- tests pass
- documentation is updated
- changelog is updated if required
- code is formatted consistently

---

## Pull Request Description

A Pull Request should contain:

### Summary

What changed?

Example:

```
Added support for exporting existing labels.
```

---

### Motivation

Why was this change needed?

Example:

```
Allows repositories to bootstrap label configuration.
```

---

### Testing

Explain how it was tested.

Example:

```
pytest -v

python gh_sync_labels.py --dry-run
```

---

# Commit Messages

Use clear commit messages.

Recommended format:

```
<type>: <short description>
```

Examples:

```
feat: add label export support

fix: handle UTF-8 CSV parsing

docs: improve workflow documentation

test: add comparison tests
```

---

# Pull Request Review

Reviewers will check:

- correctness
- maintainability
- tests
- documentation
- compatibility

Requested changes should be addressed before merging.

---

# Documentation Changes

Update documentation when changing:

| Change | Update |
|-|-|
| CLI option | docs/usage.md |
| CSV format | docs/configuration.md |
| Architecture | docs/architecture.md |
| Workflow | docs/github-actions.md |
| Development process | docs/development.md |

---

# Reporting Issues

When creating an issue, include:

## Description

Explain:

- what happened
- what was expected

---

## Environment

Include:

```
Python version:
Operating system:
GitHub CLI version:
Repository type:
```

---

## Reproduction

Provide:

- commands used
- CSV example
- error output

---

# Security Issues

Do not create public issues for security vulnerabilities.

Instead:

- contact the repository maintainers privately
- provide reproduction details
- allow time for investigation

---

# Release Process

Releases should include:

- updated `CHANGELOG.md`
- version tag
- tested code
- updated documentation

Example:

```bash
git tag v1.0.0

git push --tags
```

---

# Contributor Checklist

Before submitting:

- [ ] Branch created
- [ ] Code follows project style
- [ ] Tests added or updated
- [ ] `pytest -v` passes
- [ ] Documentation updated
- [ ] `--dry-run` verified
- [ ] Pull Request description completed

---

# Thank You

Every contribution helps improve `gh_sync_labels`.

Thank you for helping make GitHub label management more reliable, consistent, and automated.
