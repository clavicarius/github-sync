# Testing Guidelines for gh-sync-labels

## Overview

`gh-sync-labels` uses `pytest` for all automated tests. The current suite focuses on the Python CLI implementation in `gh_sync_labels.py` and covers the core label logic, CSV handling, export behavior, dry-run mode, and the GitHub CLI wrapper.

## Test Layout

The repository currently keeps its pytest modules directly in `tests/`:

```text
tests/
├── test_core_functions.py
├── test_csv_operations.py
├── test_dry_run.py
├── test_export.py
└── test_github_client.py
```

## Running Tests

Run the full suite with the same command used in CI:

```bash
python -m pytest
```

Run a single test module:

```bash
python -m pytest tests/test_export.py
```

Run tests filtered by name:

```bash
python -m pytest -k export
```

Run tests with coverage:

```bash
python -m pytest --cov=gh_sync_labels --cov-report=term-missing
```

## Makefile Shortcuts

The repository Makefile wraps the pytest commands:

```bash
make test
make test-verbose
make test-coverage
make coverage-report
```

## What the Current Tests Cover

- `test_core_functions.py` validates label normalization, validation, comparison, sync, and prune behavior.
- `test_csv_operations.py` covers CSV parsing, missing columns, duplicate labels, and invalid colors.
- `test_dry_run.py` verifies dry-run behavior for individual operations and sync/prune flows.
- `test_export.py` checks CSV export output and export/load round-trips.
- `test_github_client.py` exercises the `GitHubClient` wrapper with mocked `subprocess.run` calls.

## Test Patterns in This Repository

- Use `pytest` assertions and `pytest.raises(...)` for expectations.
- Mock external commands with `unittest.mock.patch`.
- Create temporary files and directories with `tempfile.TemporaryDirectory`.
- Keep tests self-contained; current tests create their input data inline instead of relying on a shared fixtures directory.

## Continuous Integration

GitHub Actions runs the test suite from `.github/workflows/tests.yml` with Python 3.12:

```bash
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
python -m pytest
```

## Contributing Tests

When adding or updating functionality:

1. Add or update pytest coverage in `tests/`.
2. Prefer targeted runs while iterating, for example:
   ```bash
   python -m pytest tests/test_core_functions.py
   ```
3. Run `python -m pytest` before opening or updating a pull request.
4. Update this document if the test layout or commands change.
