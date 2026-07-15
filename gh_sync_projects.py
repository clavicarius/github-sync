#!/usr/bin/env python3
"""
gh_sync_projects.py

Synchronize GitHub Projects v2 from CSV configuration files.

The CSV directory is treated as the single source of truth.

Author:
    jürgen Schlosser- Clavicarius

License:
    MIT
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import subprocess
import sys

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any


###############################################################################
# Constants
###############################################################################

DEFAULT_CONFIG_DIR = "config/projects"

PROJECT_FILE = "project.csv"
FIELDS_FILE = "fields.csv"

PROJECT_REQUIRED_COLUMNS = {
    "Name",
    "Description",
    "Visibility",
}

FIELD_REQUIRED_COLUMNS = {
    "Name",
    "Type",
}

OPTION_REQUIRED_COLUMNS = {
    "Field",
    "Option",
    "Color",
    "Description",
}

SUPPORTED_FIELD_TYPES = {
    "single_select",
    "text",
    "number",
    "date",
    "iteration",
}

SUPPORTED_OPTION_COLORS = {
    "BLUE",
    "GRAY",
    "GREEN",
    "ORANGE",
    "PINK",
    "PURPLE",
    "RED",
    "YELLOW",
}

FIELD_TYPE_TO_GRAPHQL = {
    "single_select": "SINGLE_SELECT",
    "text": "TEXT",
    "number": "NUMBER",
    "date": "DATE",
    "iteration": "ITERATION",
}


###############################################################################
# Logging
###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)


###############################################################################
# Data Model
###############################################################################


@dataclass(slots=True, frozen=True)
class Project:
    """Represents a GitHub Project v2."""

    name: str
    description: str
    visibility: str


@dataclass(slots=True, frozen=True)
class FieldOption:
    """Represents a single-select field option."""

    name: str
    color: str
    description: str


@dataclass(slots=True, frozen=True)
class ProjectField:
    """Represents a GitHub Project field."""

    name: str
    field_type: str
    options: tuple[FieldOption, ...] = ()


@dataclass(slots=True, frozen=True)
class ProjectConfiguration:
    """Represents all project configuration loaded from CSV."""

    project: Project
    fields: dict[str, ProjectField]


@dataclass(slots=True, frozen=True)
class RemoteFieldOption:
    """Represents a remote single-select option with its GitHub ID."""

    id: str
    name: str
    color: str
    description: str


@dataclass(slots=True, frozen=True)
class RemoteProjectField:
    """Represents a remote field with its GitHub ID."""

    id: str
    name: str
    field_type: str
    options: dict[str, RemoteFieldOption]


@dataclass(slots=True)
class SyncResult:
    """Stores synchronization counters."""

    created: int = 0
    updated: int = 0
    deleted: int = 0
    skipped: int = 0


###############################################################################
# GitHub CLI Wrapper
###############################################################################


class GitHubClient:
    """Wrapper around GitHub CLI commands and GraphQL interactions."""

    def __init__(
        self,
        repository: str | None = None,
        dry_run: bool = False,
    ) -> None:
        self.repository = repository or self.get_current_repository()
        self.owner, self.name = self.repository.split("/", 1)
        self.dry_run = dry_run

    def run(self, args: list[str]) -> str:
        """
        Execute a GitHub CLI command.

        Parameters
        ----------
        args:
            GitHub CLI arguments without the leading ``gh``.

        Returns
        -------
        str
            Command output.

        Raises
        ------
        RuntimeError
            If the command exits with a non-zero status code.
        """

        if self.dry_run:
            if self._is_read_operation(args):
                logger.info(
                    "[DRY-RUN:READ] gh %s",
                    " ".join(args),
                )
            else:
                logger.info(
                    "[DRY-RUN] gh %s",
                    " ".join(args),
                )
                return ""

        result = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())

        return result.stdout.strip()

    @staticmethod
    def _is_read_operation(args: list[str]) -> bool:
        """Determine whether a command is read-only."""

        if args[:2] != ["api", "graphql"]:
            return False

        query_value = ""
        for index, item in enumerate(args):
            if item == "-f" and index + 1 < len(args):
                candidate = args[index + 1]
                if candidate.startswith("query="):
                    query_value = candidate.split("=", 1)[1]
                    break

        return not query_value.lstrip().startswith("mutation")

    @classmethod
    def get_current_repository(cls) -> str:
        """Determine current repository from GitHub CLI context."""

        result = subprocess.run(
            [
                "gh",
                "repo",
                "view",
                "--json",
                "nameWithOwner",
                "-q",
                ".nameWithOwner",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())

        return result.stdout.strip()

    def graphql(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a GraphQL query using ``gh api graphql``."""

        args = [
            "api",
            "graphql",
            "-f",
            f"query={query}",
        ]

        if variables:
            for key, value in variables.items():
                args.extend(
                    [
                        "-f",
                        f"{key}={json.dumps(value, ensure_ascii=False)}",
                    ]
                )

        output = self.run(args)

        if not output:
            return {}

        payload = json.loads(output)

        if "errors" in payload:
            message = "; ".join(
                error.get("message", "GraphQL error")
                for error in payload["errors"]
            )
            raise RuntimeError(message)

        return payload.get("data", {})

    def get_repository_node_id(self) -> str:
        """Load repository node ID required for project creation."""

        query = """
        query($owner: String!, $name: String!) {
          repository(owner: $owner, name: $name) {
            id
          }
        }
        """

        data = self.graphql(
            query,
            {
                "owner": self.owner,
                "name": self.name,
            },
        )

        repository = data.get("repository")
        if not repository:
            raise RuntimeError(
                f"Repository not found: {self.repository}"
            )

        return str(repository["id"])

    def list_projects(self) -> dict[str, tuple[str, Project]]:
        """Load existing repository projects indexed by project name."""

        query = """
        query($owner: String!, $name: String!) {
          repository(owner: $owner, name: $name) {
            projectsV2(first: 100) {
              nodes {
                id
                title
                shortDescription
                public
              }
            }
          }
        }
        """

        data = self.graphql(
            query,
            {
                "owner": self.owner,
                "name": self.name,
            },
        )

        repository = data.get("repository", {})
        projects = repository.get("projectsV2", {}).get("nodes", [])

        result: dict[str, tuple[str, Project]] = {}

        for item in projects:
            project = Project(
                name=item.get("title", ""),
                description=item.get("shortDescription") or "",
                visibility=(
                    "public"
                    if bool(item.get("public"))
                    else "private"
                ),
            )
            result[project.name] = (str(item["id"]), project)

        return result

    def list_project_fields(
        self,
        project_id: str,
    ) -> dict[str, RemoteProjectField]:
        """Load project fields and single-select options for a project."""

        query = """
        query($projectId: ID!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              fields(first: 100) {
                nodes {
                  ... on ProjectV2Field {
                    id
                    name
                    dataType
                  }
                  ... on ProjectV2SingleSelectField {
                    id
                    name
                    dataType
                    options {
                      id
                      name
                      color
                      description
                    }
                  }
                }
              }
            }
          }
        }
        """

        data = self.graphql(
            query,
            {
                "projectId": project_id,
            },
        )

        node = data.get("node", {})
        fields = node.get("fields", {}).get("nodes", [])
        result: dict[str, RemoteProjectField] = {}

        for field in fields:
            field_name = field.get("name", "")
            data_type = str(field.get("dataType", "")).lower()

            options: dict[str, RemoteFieldOption] = {}
            for option in field.get("options", []) or []:
                remote_option = RemoteFieldOption(
                    id=str(option["id"]),
                    name=option["name"],
                    color=str(option.get("color", "")).upper(),
                    description=option.get("description") or "",
                )
                options[remote_option.name] = remote_option

            result[field_name] = RemoteProjectField(
                id=str(field["id"]),
                name=field_name,
                field_type=data_type,
                options=options,
            )

        return result

    def create_project(self, project: Project) -> str:
        """Create a new project and return its node ID."""

        if self.dry_run:
            return f"dry-run-project-{project.name}"

        repository_id = self.get_repository_node_id()
        query = """
        mutation($ownerId: ID!, $title: String!, $description: String, $public: Boolean!) {
          createProjectV2(input: {
            ownerId: $ownerId
            title: $title
            shortDescription: $description
            public: $public
          }) {
            projectV2 {
              id
            }
          }
        }
        """

        data = self.graphql(
            query,
            {
                "ownerId": repository_id,
                "title": project.name,
                "description": project.description,
                "public": project.visibility == "public",
            },
        )

        return str(
            data["createProjectV2"]["projectV2"]["id"]
        )

    def update_project(
        self,
        project_id: str,
        project: Project,
    ) -> None:
        """Update project metadata."""

        query = """
        mutation($projectId: ID!, $title: String!, $description: String, $public: Boolean!) {
          updateProjectV2(input: {
            projectId: $projectId
            title: $title
            shortDescription: $description
            public: $public
          }) {
            projectV2 {
              id
            }
          }
        }
        """

        self.graphql(
            query,
            {
                "projectId": project_id,
                "title": project.name,
                "description": project.description,
                "public": project.visibility == "public",
            },
        )

    def create_field(
        self,
        project_id: str,
        field: ProjectField,
    ) -> str:
        """Create a project field and return its node ID."""

        graphql_type = FIELD_TYPE_TO_GRAPHQL[field.field_type]

        query = """
        mutation($projectId: ID!, $name: String!, $dataType: ProjectV2CustomFieldType!) {
          createProjectV2Field(input: {
            projectId: $projectId
            name: $name
            dataType: $dataType
          }) {
            projectV2Field {
              ... on ProjectV2FieldCommon {
                id
              }
            }
          }
        }
        """

        data = self.graphql(
            query,
            {
                "projectId": project_id,
                "name": field.name,
                "dataType": graphql_type,
            },
        )

        return str(
            data["createProjectV2Field"]["projectV2Field"]["id"]
        )

    def delete_field(
        self,
        field_id: str,
    ) -> None:
        """Delete a custom project field."""

        query = """
        mutation($fieldId: ID!) {
          deleteProjectV2Field(input: {
            fieldId: $fieldId
          }) {
            clientMutationId
          }
        }
        """

        self.graphql(
            query,
            {
                "fieldId": field_id,
            },
        )

    def create_single_select_option(
        self,
        field_id: str,
        option: FieldOption,
    ) -> None:
        """Create a single-select field option."""

        query = """
        mutation($fieldId: ID!, $name: String!, $color: ProjectV2SingleSelectFieldOptionColor!, $description: String) {
          createProjectV2SingleSelectFieldOption(input: {
            fieldId: $fieldId
            name: $name
            color: $color
            description: $description
          }) {
            projectV2SingleSelectFieldOption {
              id
            }
          }
        }
        """

        self.graphql(
            query,
            {
                "fieldId": field_id,
                "name": option.name,
                "color": option.color,
                "description": option.description,
            },
        )

    def update_single_select_option(
        self,
        project_id: str,
        field_id: str,
        option_id: str,
        option: FieldOption,
    ) -> None:
        """Update a single-select field option."""

        query = """
        mutation($projectId: ID!, $fieldId: ID!, $optionId: String!, $name: String!, $color: ProjectV2SingleSelectFieldOptionColor!, $description: String) {
          updateProjectV2SingleSelectField(input: {
            projectId: $projectId
            fieldId: $fieldId
            optionId: $optionId
            name: $name
            color: $color
            description: $description
          }) {
            projectV2Item {
              id
            }
          }
        }
        """

        self.graphql(
            query,
            {
                "projectId": project_id,
                "fieldId": field_id,
                "optionId": option_id,
                "name": option.name,
                "color": option.color,
                "description": option.description,
            },
        )

    def delete_single_select_option(
        self,
        project_id: str,
        field_id: str,
        option_id: str,
    ) -> None:
        """Delete a single-select field option."""

        query = """
        mutation($projectId: ID!, $fieldId: ID!, $optionId: String!) {
          deleteProjectV2SingleSelectFieldOption(input: {
            projectId: $projectId
            fieldId: $fieldId
            optionId: $optionId
          }) {
            clientMutationId
          }
        }
        """

        self.graphql(
            query,
            {
                "projectId": project_id,
                "fieldId": field_id,
                "optionId": option_id,
            },
        )


###############################################################################
# CSV Handling
###############################################################################


def require_columns(
    file_name: str,
    fieldnames: list[str] | None,
    required_columns: set[str],
) -> None:
    """Validate required CSV columns."""

    if not fieldnames:
        raise ValueError(
            f"CSV file has no header: {file_name}"
        )

    missing_columns = required_columns - set(fieldnames)

    if missing_columns:
        raise ValueError(
            f"Missing CSV columns in {file_name}: "
            + ", ".join(sorted(missing_columns))
        )


def normalize_visibility(visibility: str) -> str:
    """Normalize and validate project visibility values."""

    normalized = visibility.strip().lower()

    if normalized not in {"private", "public"}:
        raise ValueError(
            f"Invalid project visibility: {visibility}"
        )

    return normalized


def normalize_field_type(field_type: str) -> str:
    """Normalize and validate project field type values."""

    normalized = field_type.strip().lower()

    if normalized not in SUPPORTED_FIELD_TYPES:
        raise ValueError(
            f"Invalid field type: {field_type}"
        )

    return normalized


def normalize_option_color(color: str) -> str:
    """Normalize and validate single-select option colors."""

    normalized = color.strip().upper()

    if normalized not in SUPPORTED_OPTION_COLORS:
        raise ValueError(
            f"Invalid option color: {color}"
        )

    return normalized


def load_project_definition(
    csv_file: Path,
) -> Project:
    """Load ``project.csv`` definition."""

    if not csv_file.exists():
        raise FileNotFoundError(
            f"CSV file not found: {csv_file}"
        )

    logger.info(
        "Loading project definition from %s",
        csv_file,
    )

    with csv_file.open(
        mode="r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.DictReader(
            file,
            delimiter=";",
        )

        require_columns(
            csv_file.name,
            reader.fieldnames,
            PROJECT_REQUIRED_COLUMNS,
        )

        rows = list(reader)

    if not rows:
        raise ValueError(
            "project.csv must contain exactly one row."
        )

    if len(rows) > 1:
        raise ValueError(
            "project.csv currently supports exactly one project."
        )

    row = rows[0]

    project = Project(
        name=row["Name"].strip(),
        description=row["Description"].strip(),
        visibility=normalize_visibility(row["Visibility"]),
    )

    if not project.name:
        raise ValueError(
            "Project name must not be empty."
        )

    return project


def load_fields_definition(
    csv_file: Path,
) -> dict[str, ProjectField]:
    """Load ``fields.csv`` definitions."""

    if not csv_file.exists():
        raise FileNotFoundError(
            f"CSV file not found: {csv_file}"
        )

    logger.info(
        "Loading field definitions from %s",
        csv_file,
    )

    fields: dict[str, ProjectField] = {}

    with csv_file.open(
        mode="r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.DictReader(
            file,
            delimiter=";",
        )

        require_columns(
            csv_file.name,
            reader.fieldnames,
            FIELD_REQUIRED_COLUMNS,
        )

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            try:
                name = row["Name"].strip()
                field_type = normalize_field_type(row["Type"])

                if not name:
                    raise ValueError(
                        "Field name must not be empty."
                    )

                if name in fields:
                    raise ValueError(
                        f"Duplicate field name: {name}"
                    )

                fields[name] = ProjectField(
                    name=name,
                    field_type=field_type,
                )
            except Exception as exc:
                raise ValueError(
                    f"Invalid CSV row {row_number} in {csv_file.name}: {exc}"
                ) from exc

    return fields


def load_field_options(
    csv_file: Path,
) -> dict[str, list[FieldOption]]:
    """Load a single option CSV file and return options by field name."""

    options: dict[str, list[FieldOption]] = {}

    with csv_file.open(
        mode="r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.DictReader(
            file,
            delimiter=";",
        )

        require_columns(
            csv_file.name,
            reader.fieldnames,
            OPTION_REQUIRED_COLUMNS,
        )

        seen_pairs: set[tuple[str, str]] = set()

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            try:
                field_name = row["Field"].strip()
                option_name = row["Option"].strip()

                if not field_name:
                    raise ValueError(
                        "Field name must not be empty."
                    )

                if not option_name:
                    raise ValueError(
                        "Option name must not be empty."
                    )

                pair = (field_name, option_name)
                if pair in seen_pairs:
                    raise ValueError(
                        f"Duplicate option '{option_name}' for field '{field_name}'"
                    )
                seen_pairs.add(pair)

                option = FieldOption(
                    name=option_name,
                    color=normalize_option_color(row["Color"]),
                    description=row["Description"].strip(),
                )

                options.setdefault(field_name, []).append(option)
            except Exception as exc:
                raise ValueError(
                    f"Invalid CSV row {row_number} in {csv_file.name}: {exc}"
                ) from exc

    return options


def load_project_configuration(
    config_dir: Path,
) -> ProjectConfiguration:
    """Load project configuration from a directory of CSV files."""

    if not config_dir.exists() or not config_dir.is_dir():
        raise FileNotFoundError(
            f"Configuration directory not found: {config_dir}"
        )

    project = load_project_definition(
        config_dir / PROJECT_FILE
    )

    fields = load_fields_definition(
        config_dir / FIELDS_FILE
    )

    option_files = sorted(
        file
        for file in config_dir.glob("*.csv")
        if file.name not in {PROJECT_FILE, FIELDS_FILE}
    )

    options_by_field: dict[str, list[FieldOption]] = {}

    for option_file in option_files:
        logger.info(
            "Loading option definitions from %s",
            option_file,
        )

        file_options = load_field_options(option_file)

        for field_name, options in file_options.items():
            options_by_field.setdefault(field_name, []).extend(options)

    for field_name, options in options_by_field.items():
        if field_name not in fields:
            raise ValueError(
                f"Options reference unknown field: {field_name}"
            )

        field = fields[field_name]

        if field.field_type != "single_select":
            raise ValueError(
                f"Options are only allowed for single_select fields: {field_name}"
            )

        fields[field_name] = replace(
            field,
            options=tuple(options),
        )

    for field in fields.values():
        if field.field_type == "single_select":
            option_names = [
                option.name
                for option in field.options
            ]
            if len(option_names) != len(set(option_names)):
                raise ValueError(
                    f"Duplicate options found for field: {field.name}"
                )

    logger.info(
        "Loaded project '%s' with %s fields",
        project.name,
        len(fields),
    )

    return ProjectConfiguration(
        project=project,
        fields=fields,
    )


def export_project_configuration(
    project: Project,
    fields: dict[str, ProjectField],
    output_dir: Path,
) -> None:
    """Export project configuration into CSV files."""

    logger.info(
        "Exporting project configuration to %s",
        output_dir,
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    project_file = output_dir / PROJECT_FILE
    with project_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(
            file,
            delimiter=";",
        )
        writer.writerow(
            [
                "Name",
                "Description",
                "Visibility",
            ]
        )
        writer.writerow(
            [
                project.name,
                project.description,
                project.visibility,
            ]
        )

    fields_file = output_dir / FIELDS_FILE
    with fields_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(
            file,
            delimiter=";",
        )
        writer.writerow(
            [
                "Name",
                "Type",
            ]
        )

        for field in fields.values():
            writer.writerow(
                [
                    field.name,
                    field.field_type,
                ]
            )

    for field in fields.values():
        if field.field_type != "single_select":
            continue

        options_file_name = (
            field.name.strip().lower().replace(" ", "_")
            + ".csv"
        )

        options_file = output_dir / options_file_name

        with options_file.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as file:
            writer = csv.writer(
                file,
                delimiter=";",
            )
            writer.writerow(
                [
                    "Field",
                    "Option",
                    "Color",
                    "Description",
                ]
            )

            for option in field.options:
                writer.writerow(
                    [
                        field.name,
                        option.name,
                        option.color,
                        option.description,
                    ]
                )

    logger.info(
        "Export complete."
    )


###############################################################################
# Synchronization
###############################################################################


def projects_equal(
    current: Project,
    desired: Project,
) -> bool:
    """Compare two project definitions."""

    return (
        current.description == desired.description
        and current.visibility == desired.visibility
    )


def option_equal(
    current: RemoteFieldOption,
    desired: FieldOption,
) -> bool:
    """Compare existing and desired single-select options."""

    return (
        current.color.upper() == desired.color.upper()
        and current.description == desired.description
    )


def create_project(
    client: GitHubClient,
    project: Project,
) -> str:
    """Create a new project and return its ID."""

    logger.info(
        "Creating project: %s",
        project.name,
    )

    return client.create_project(project)


def update_project(
    client: GitHubClient,
    project_id: str,
    project: Project,
) -> None:
    """Update an existing project."""

    logger.info(
        "Updating project: %s",
        project.name,
    )

    client.update_project(project_id, project)


def create_field(
    client: GitHubClient,
    project_id: str,
    field: ProjectField,
) -> str:
    """Create a project field and return its ID."""

    logger.info(
        "Creating field: %s",
        field.name,
    )

    return client.create_field(project_id, field)


def delete_field(
    client: GitHubClient,
    field_name: str,
    field_id: str,
) -> None:
    """Delete a project field."""

    logger.info(
        "Deleting field: %s",
        field_name,
    )

    client.delete_field(field_id)


def create_option(
    client: GitHubClient,
    field_name: str,
    field_id: str,
    option: FieldOption,
) -> None:
    """Create a single-select option."""

    logger.info(
        "Creating option: %s -> %s",
        field_name,
        option.name,
    )

    client.create_single_select_option(
        field_id,
        option,
    )


def update_option(
    client: GitHubClient,
    project_id: str,
    field_name: str,
    field_id: str,
    option_id: str,
    option: FieldOption,
) -> None:
    """Update a single-select option."""

    logger.info(
        "Updating option: %s -> %s",
        field_name,
        option.name,
    )

    client.update_single_select_option(
        project_id,
        field_id,
        option_id,
        option,
    )


def delete_option(
    client: GitHubClient,
    project_id: str,
    field_name: str,
    field_id: str,
    option_name: str,
    option_id: str,
) -> None:
    """Delete a single-select option."""

    logger.info(
        "Deleting option: %s -> %s",
        field_name,
        option_name,
    )

    client.delete_single_select_option(
        project_id,
        field_id,
        option_id,
    )


def sync_field_options(
    client: GitHubClient,
    project_id: str,
    desired_field: ProjectField,
    current_field: RemoteProjectField,
    overwrite: bool,
    prune: bool,
) -> SyncResult:
    """Synchronize single-select field options."""

    result = SyncResult()

    desired_options = {
        option.name: option
        for option in desired_field.options
    }

    for option_name, desired_option in desired_options.items():
        current_option = current_field.options.get(option_name)

        if current_option is None:
            create_option(
                client,
                desired_field.name,
                current_field.id,
                desired_option,
            )
            result.created += 1
            continue

        if option_equal(
            current_option,
            desired_option,
        ):
            logger.info(
                "Skipping unchanged option: %s -> %s",
                desired_field.name,
                option_name,
            )
            result.skipped += 1
            continue

        if overwrite:
            update_option(
                client,
                project_id,
                desired_field.name,
                current_field.id,
                current_option.id,
                desired_option,
            )
            result.updated += 1
        else:
            logger.info(
                "Skipping existing option (overwrite disabled): %s -> %s",
                desired_field.name,
                option_name,
            )
            result.skipped += 1

    if prune:
        obsolete_options = (
            set(current_field.options.keys())
            - set(desired_options.keys())
        )

        for option_name in sorted(obsolete_options):
            current_option = current_field.options[option_name]
            delete_option(
                client,
                project_id,
                desired_field.name,
                current_field.id,
                option_name,
                current_option.id,
            )
            result.deleted += 1

    return result


def sync_fields(
    client: GitHubClient,
    project_id: str,
    desired_fields: dict[str, ProjectField],
    existing_fields: dict[str, RemoteProjectField],
    overwrite: bool,
    prune: bool,
) -> SyncResult:
    """Synchronize project fields and single-select options."""

    result = SyncResult()

    for field_name, desired_field in desired_fields.items():
        current_field = existing_fields.get(field_name)

        if current_field is None:
            field_id = create_field(
                client,
                project_id,
                desired_field,
            )
            result.created += 1

            if desired_field.field_type == "single_select":
                temp_current = RemoteProjectField(
                    id=field_id,
                    name=desired_field.name,
                    field_type=desired_field.field_type,
                    options={},
                )
                option_result = sync_field_options(
                    client,
                    project_id,
                    desired_field,
                    temp_current,
                    overwrite=overwrite,
                    prune=False,
                )
                result.created += option_result.created
                result.updated += option_result.updated
                result.deleted += option_result.deleted
                result.skipped += option_result.skipped

            continue

        if current_field.field_type != desired_field.field_type:
            logger.info(
                "Skipping field with type mismatch: %s",
                field_name,
            )
            result.skipped += 1
            continue

        logger.info(
            "Skipping unchanged field: %s",
            field_name,
        )
        result.skipped += 1

        if desired_field.field_type == "single_select":
            option_result = sync_field_options(
                client,
                project_id,
                desired_field,
                current_field,
                overwrite=overwrite,
                prune=prune,
            )
            result.created += option_result.created
            result.updated += option_result.updated
            result.deleted += option_result.deleted
            result.skipped += option_result.skipped

    if prune:
        obsolete_fields = (
            set(existing_fields.keys())
            - set(desired_fields.keys())
        )

        for field_name in sorted(obsolete_fields):
            logger.info(
                "Skipping deletion of unmanaged field for safety: %s",
                field_name,
            )
            result.skipped += 1

    return result


def sync_project(
    client: GitHubClient,
    desired_project: Project,
    existing_projects: dict[str, tuple[str, Project]],
    overwrite: bool,
) -> tuple[str, SyncResult]:
    """Synchronize project metadata and return project ID with result."""

    result = SyncResult()

    existing = existing_projects.get(desired_project.name)

    if existing is None:
        project_id = create_project(
            client,
            desired_project,
        )
        result.created += 1
        return project_id, result

    project_id, current_project = existing

    if projects_equal(
        current_project,
        desired_project,
    ):
        logger.info(
            "Skipping unchanged project: %s",
            desired_project.name,
        )
        result.skipped += 1
        return project_id, result

    if overwrite:
        update_project(
            client,
            project_id,
            desired_project,
        )
        result.updated += 1
    else:
        logger.info(
            "Skipping existing project (overwrite disabled): %s",
            desired_project.name,
        )
        result.skipped += 1

    return project_id, result


def merge_sync_results(*results: SyncResult) -> SyncResult:
    """Merge multiple ``SyncResult`` instances into one."""

    merged = SyncResult()

    for result in results:
        merged.created += result.created
        merged.updated += result.updated
        merged.deleted += result.deleted
        merged.skipped += result.skipped

    return merged


###############################################################################
# Command Line Interface
###############################################################################


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Synchronize GitHub Projects v2 from CSV configuration."
        )
    )

    parser.add_argument(
        "--repo",
        required=False,
        help=(
            "GitHub repository in owner/name format. "
            "If omitted, the current repository is used."
        ),
    )

    parser.add_argument(
        "--csv",
        default=DEFAULT_CONFIG_DIR,
        help=(
            "Path to the projects CSV directory. "
            f"Default: {DEFAULT_CONFIG_DIR}"
        ),
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=(
            "Update existing resources when differences are detected."
        ),
    )

    parser.add_argument(
        "--prune",
        action="store_true",
        help=(
            "Delete single-select options that are missing in CSV (fields are not deleted for safety)."
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Show changes without applying them."
        ),
    )

    parser.add_argument(
        "--export",
        metavar="FILE",
        help=(
            "Export existing GitHub project configuration "
            "to CSV directory and exit."
        ),
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging.",
    )

    return parser.parse_args()


###############################################################################
# Application Entry Point
###############################################################################


def main() -> int:
    """
    Application entry point.

    Returns
    -------
    int
        Process exit code.
    """

    args = parse_arguments()

    if args.debug:
        logger.setLevel(
            logging.DEBUG
        )

    try:
        config_dir = Path(args.csv)

        client = GitHubClient(
            repository=args.repo,
            dry_run=args.dry_run,
        )

        logger.info(
            "Repository: %s",
            client.repository,
        )

        existing_projects = client.list_projects()

        logger.info(
            "Existing GitHub projects: %s",
            len(existing_projects),
        )

        if args.export:
            if not existing_projects:
                raise ValueError(
                    "No project found to export."
                )

            first_project_name = sorted(
                existing_projects.keys()
            )[0]
            project_id, project = existing_projects[first_project_name]
            existing_fields = client.list_project_fields(project_id)

            export_fields: dict[str, ProjectField] = {}
            for remote_field in existing_fields.values():
                options = tuple(
                    FieldOption(
                        name=option.name,
                        color=option.color,
                        description=option.description,
                    )
                    for option in remote_field.options.values()
                )
                export_fields[remote_field.name] = ProjectField(
                    name=remote_field.name,
                    field_type=remote_field.field_type,
                    options=options,
                )

            export_project_configuration(
                project,
                export_fields,
                Path(args.export),
            )
            return 0

        configuration = load_project_configuration(config_dir)

        project_id, project_result = sync_project(
            client=client,
            desired_project=configuration.project,
            existing_projects=existing_projects,
            overwrite=args.overwrite,
        )

        existing_fields = client.list_project_fields(project_id)

        field_result = sync_fields(
            client=client,
            project_id=project_id,
            desired_fields=configuration.fields,
            existing_fields=existing_fields,
            overwrite=args.overwrite,
            prune=args.prune,
        )

        result = merge_sync_results(
            project_result,
            field_result,
        )

        logger.info("")
        logger.info("Synchronization summary:")
        logger.info("Created: %s", result.created)
        logger.info("Updated: %s", result.updated)
        logger.info("Deleted: %s", result.deleted)
        logger.info("Skipped: %s", result.skipped)
        logger.info("Done.")

        return 0

    except Exception as exc:
        logger.error(
            "%s",
            exc,
        )
        return 1


if __name__ == "__main__":
    sys.exit(
        main()
    )
