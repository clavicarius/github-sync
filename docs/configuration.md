# Configuration Guide

## Overview

`gh_sync_labels.py` uses a CSV file as the **single source of truth** for GitHub repository labels.

The configuration defines:

- label names
- label colors
- label descriptions
- logical grouping

The default configuration file is:

```
labels.csv
```

A custom configuration file can be provided:

```bash
python gh_sync_labels.py \
  --csv path/to/labels.csv
```

---

# Configuration Philosophy

The label configuration follows these principles:

- consistent naming
- predictable colors
- meaningful descriptions
- automation-friendly structure
- reusable across repositories

The CSV file should be maintained in version control.

Recommended location:

```
config/
└── labels.csv
```

or:

```
.github/
└── labels.csv
```

---

# CSV Format

The CSV file uses:

| Setting | Value |
|-|-|
| Encoding | UTF-8 |
| Separator | `;` |
| Header | required |
| Line ending | LF recommended |

Example:

```csv
Category;Label;Color;Description
Type;bug;D73A4A;"🐞 A bug that needs to be fixed."
```

---

# CSV Columns

## Category

Logical grouping of labels.

The category is informational only.

It is not synchronized with GitHub.

Example values:

```
Type
Priority
Status
Area
Other
```

---

## Label

The actual GitHub label name.

Rules:

- must be unique
- must not be empty
- should be descriptive
- avoid unnecessary abbreviations

Examples:

Good:

```
bug
priority: high
status: blocked
area: backend
```

Avoid:

```
fix
p1
misc
```

---

## Color

GitHub label color.

Format:

```
RRGGBB
```

Example:

```
D73A4A
```

The following format is also accepted:

```
#D73A4A
```

The tool normalizes colors internally.

---

## Description

Short explanation shown in GitHub.

Recommendations:

- describe the purpose of the label
- keep descriptions concise
- use emojis consistently
- avoid implementation details

Example:

```
🐞 A bug that needs to be fixed.
```

---

# Label Naming Convention

The recommended naming pattern is:

```
category: value
```

for grouped labels.

Examples:

```
priority: high
status: blocked
area: backend
```

Benefits:

- easier filtering
- better readability
- predictable automation
- consistent UI

---

# Label Categories

The default label system contains five categories.

---

# Type Labels

Used to classify the nature of a change.

| Label | Purpose |
|-|-|
| bug | Defect or incorrect behavior |
| feature | New functionality |
| enhancement | Improvement of existing functionality |
| refactor | Code restructuring without behavior changes |
| documentation | Documentation changes |
| test | Test additions or improvements |
| dependencies | Dependency changes |
| security | Security-related changes |
| performance | Performance improvements |

Example:

```csv
Type;bug;D73A4A;"🐞 A bug that needs to be fixed."
```

---

# Priority Labels

Used to communicate urgency.

| Label | Meaning |
|-|-|
| priority: high | Important and should be addressed soon |
| priority: medium | Important but not urgent |
| priority: low | Can be addressed later |

Example:

```csv
Priority;priority: high;D73A4A;"🔴 High priority – should be addressed soon."
```

---

# Status Labels

Used to track workflow state.

| Label | Meaning |
|-|-|
| status: in progress | Work has started |
| status: blocked | Work cannot continue |
| status: needs review | Review required |
| status: needs discussion | Decision required |

Example:

```csv
Status;status: blocked;B60205;"🚫 Cannot proceed due to a dependency."
```

---

# Area Labels

Used for technical ownership or affected components.

| Label | Meaning |
|-|-|
| area: frontend | User interface |
| area: backend | Backend logic/services |
| area: api | Interfaces |
| area: database | Database changes |
| area: ci/cd | Build and deployment pipelines |

Example:

```csv
Area;area: backend;0052CC;"Affects backend logic or services."
```

---

# Other Labels

Additional workflow labels.

| Label | Purpose |
|-|-|
| good first issue | Suitable for newcomers |
| help wanted | Additional help requested |
| technical debt | Long-term cleanup required |

Example:

```csv
Other;technical debt;6A737D;"📋 Technical debt that should be addressed over time."
```

---

# Color Guidelines

Colors should provide visual grouping.

Recommended semantic mapping:

| Meaning | Color |
|-|-|
| Error / Critical | Red |
| Feature / Information | Blue |
| Improvement | Light Blue |
| Security | Dark Red |
| Performance | Orange |
| Success | Green |
| Discussion | Purple |
| Neutral | Gray |

Avoid:

- random colors
- too many similar colors
- colors without meaning

---

# Validation Rules

The tool validates:

## Required Columns

Must exist:

```
Category
Label
Color
Description
```

---

## Duplicate Labels

Not allowed.

Invalid:

```csv
Type;bug;D73A4A;"Bug"
Type;bug;B60205;"Another bug"
```

---

## Invalid Colors

Invalid:

```
red
123
GGHH22
```

Valid:

```
D73A4A
#D73A4A
```

---

## Empty Values

Not allowed:

```
Label;;
```

Required:

- label name
- color
- description

---

# Version Control

The CSV file should be committed together with application changes.

Recommended workflow:

```
feature branch

    |
    v

modify labels.csv

    |
    v

run dry-run

    |
    v

create pull request

    |
    v

merge

    |
    v

GitHub Action synchronizes labels
```

---

# Migration Between Repositories

To copy labels:

## Export source repository

```bash
python gh_sync_labels.py \
  --repo source/repository \
  --export labels.csv
```

## Apply to target repository

```bash
python gh_sync_labels.py \
  --repo target/repository \
  --overwrite \
  --prune
```

---

# Best Practices

Recommended:

✅ Keep labels simple  
✅ Use consistent prefixes  
✅ Store configuration in Git  
✅ Review changes before applying  
✅ Automate synchronization  

Avoid:

❌ Manual label drift  
❌ Duplicate meanings  
❌ Excessive label count  
❌ Unclear descriptions  

---

# Future Extensions

Possible configuration enhancements:

- YAML support
- JSON support
- label ownership
- default labels per repository type
- protected labels
- label templates
- organization-wide configuration
