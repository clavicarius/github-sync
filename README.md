# GitHub Synchronization Tools

Synchronize GitHub labels and Projects v2 definitions from CSV configuration.

![logo](./assets/logo.png)

The repository currently provides:

- `gh_sync_labels.py` to manage repository labels as code
- `gh_sync_projects.py` to manage GitHub Projects v2 (project metadata, fields, and single-select options) as code

## Features

- Create missing labels
- Update existing labels
- Remove obsolete labels
- Export existing labels
- Create and update GitHub Projects v2 from CSV definitions
- Synchronize project fields and single-select options
- Export GitHub Projects v2 definitions back to CSV
- Dry-run support
- CSV validation
- GitHub Actions support
- UTF-8 and emoji support

## Requirements

- Python 3.12+
- GitHub CLI (`gh`)
- Authenticated GitHub session

## Quick Start

Clone repository:

```bash
git clone <repository>
cd <repository>
```

Run label synchronization:

```bash
python gh_sync_labels.py
```

Full synchronization:

```bash
python gh_sync_labels.py \
  --overwrite \
  --prune
```

Run projects synchronization:

```bash
python gh_sync_projects.py
```

Projects full synchronization:

```bash
python gh_sync_projects.py \
  --overwrite \
  --prune
```

## Documentation

Detailed documentation:

* [Usage](docs/usage.md)
* [Usage (Labels)](docs/usage_sync_labels.md)
* [Usage (Projects)](docs/usage_sync_projects.md)
* [Configuration](docs/configuration.md)
* [Architecture](docs/architecture.md)
* [GitHub Actions](docs/github-actions.md)
* [Development](docs/development.md)

## License

MIT
