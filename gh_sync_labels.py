#!/usr/bin/env python3
"""
gh_sync_labels.py

Synchronize GitHub repository labels with a CSV configuration.

The CSV file is treated as the single source of truth.

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
import re
import subprocess
import sys

from dataclasses import dataclass
from pathlib import Path
from typing import Any


###############################################################################
# Constants
###############################################################################

DEFAULT_CSV_FILE = "labels.csv"

REQUIRED_COLUMNS = {
    "Category",
    "Label",
    "Color",
    "Description",
}

HEX_COLOR_PATTERN = re.compile(r"^#?[0-9A-Fa-f]{6}$")


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
class Label:
    """
    Represents a GitHub label.
    """

    name: str
    color: str
    description: str


###############################################################################
# GitHub CLI Wrapper
###############################################################################

class GitHubClient:
    """
    Small wrapper around the GitHub CLI.

    All communication with GitHub should happen through this class.
    """

    def __init__(
        self,
        repository: str | None = None,
        dry_run: bool = False,
    ) -> None:
        self.repository = repository or self.get_current_repository()
        self.dry_run = dry_run

    def run(self, args: list[str]) -> str:
        """
        Execute a GitHub CLI command.

        Raises
        ------
        RuntimeError
            If the command exits with a non-zero exit code.
        """

        if self.dry_run:
            # Keep read operations functional in dry-run mode so
            # comparison/export logic can still operate on real data.
            if args[:2] == ["label", "list"]:
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

    @classmethod
    def get_current_repository(cls) -> str:
        """
        Determine the current GitHub repository.

        Returns
        -------
        str
            Repository in the form owner/repository.
        """

        logger.debug("Determining current repository...")

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

    def list_labels(self) -> dict[str, Label]:
        """
        Load all labels from the repository.

        Returns
        -------
        dict[str, Label]
            Dictionary indexed by label name.
        """

        logger.debug("Loading existing GitHub labels...")

        output = self.run(
            [
                "label",
                "list",
                "--repo",
                self.repository,
                "--limit",
                "1000",
                "--json",
                "name,color,description",
            ]
        )

        labels: dict[str, Label] = {}

        for item in json.loads(output):
            label = Label(
                name=item["name"],
                color=item["color"].upper(),
                description=item.get("description", ""),
            )

            labels[label.name] = label

        return labels
        

###############################################################################
# CSV Handling
###############################################################################

def normalize_color(color: str) -> str:
    """
    Normalize and validate a GitHub label color.

    Accepts:
        D73A4A
        #D73A4A

    Returns:
        Uppercase hex color without '#'.

    Raises:
        ValueError:
            If the color format is invalid.
    """

    normalized = color.strip()

    if not HEX_COLOR_PATTERN.match(normalized):
        raise ValueError(
            f"Invalid color format: {color}"
        )

    return normalized.replace("#", "").upper()


def validate_label(label: Label) -> None:
    """
    Validate a label definition.

    Raises:
        ValueError:
            If required label data is missing.
    """

    if not label.name:
        raise ValueError(
            "Label name must not be empty."
        )

    if not label.color:
        raise ValueError(
            f"Missing color for label: {label.name}"
        )

    if not label.description:
        raise ValueError(
            f"Missing description for label: {label.name}"
        )


def load_labels(csv_file: Path) -> dict[str, Label]:
    """
    Load labels from CSV.

    The CSV file is the single source of truth.

    Parameters
    ----------
    csv_file:
        Path to CSV configuration.

    Returns
    -------
    dict[str, Label]
        Labels indexed by label name.

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist.

    ValueError
        If the CSV format is invalid.
    """

    if not csv_file.exists():
        raise FileNotFoundError(
            f"CSV file not found: {csv_file}"
        )

    logger.info(
        "Loading labels from %s",
        csv_file,
    )

    labels: dict[str, Label] = {}

    with csv_file.open(
        mode="r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file,
            delimiter=";",
        )

        if not reader.fieldnames:
            raise ValueError(
                "CSV file has no header."
            )

        missing_columns = (
            REQUIRED_COLUMNS
            - set(reader.fieldnames)
        )

        if missing_columns:
            raise ValueError(
                "Missing CSV columns: "
                + ", ".join(sorted(missing_columns))
            )

        for row_number, row in enumerate(
            reader,
            start=2,
        ):

            try:

                label = Label(
                    name=row["Label"].strip(),
                    color=normalize_color(
                        row["Color"]
                    ),
                    description=row["Description"].strip(),
                )

                validate_label(label)

                if label.name in labels:
                    raise ValueError(
                        f"Duplicate label name: "
                        f"{label.name}"
                    )

                labels[label.name] = label

            except Exception as exc:

                raise ValueError(
                    f"Invalid CSV row {row_number}: {exc}"
                ) from exc

    logger.info(
        "Loaded %s labels from CSV",
        len(labels),
    )

    return labels
    

def export_labels(
    labels: dict[str, Label],
    output_file: Path,
) -> None:
    """
    Export labels into CSV format.

    Parameters
    ----------
    labels:
        Dictionary of labels to export.
    output_file:
        Path to the output CSV file.
    """

    logger.info(
        "Exporting labels to %s",
        output_file,
    )

    with output_file.open(
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
                "Category",
                "Label",
                "Color",
                "Description",
            ]
        )

        for label in labels.values():

            writer.writerow(
                [
                    "",
                    label.name,
                    label.color,
                    label.description,
                ]
            )

    logger.info(
        "Exported %s labels",
        len(labels),
    )


###############################################################################
# Label Synchronization
###############################################################################

@dataclass(slots=True)
class SyncResult:
    """
    Stores the result of a synchronization run.
    """

    created: int = 0
    updated: int = 0
    deleted: int = 0
    skipped: int = 0


def create_label(
    client: GitHubClient,
    label: Label,
) -> None:
    """
    Create a new GitHub label.
    """

    logger.info(
        "Creating label: %s",
        label.name,
    )

    client.run(
        [
            "label",
            "create",
            label.name,
            "--repo",
            client.repository,
            "--color",
            label.color,
            "--description",
            label.description,
        ]
    )


def update_label(
    client: GitHubClient,
    label: Label,
) -> None:
    """
    Update an existing GitHub label.

    Uses --force because GitHub CLI does not provide
    a dedicated update command.
    """

    logger.info(
        "Updating label: %s",
        label.name,
    )

    client.run(
        [
            "label",
            "create",
            label.name,
            "--repo",
            client.repository,
            "--color",
            label.color,
            "--description",
            label.description,
            "--force",
        ]
    )


def delete_label(
    client: GitHubClient,
    label_name: str,
) -> None:
    """
    Delete a GitHub label.
    """

    logger.info(
        "Deleting label: %s",
        label_name,
    )

    client.run(
        [
            "label",
            "delete",
            label_name,
            "--repo",
            client.repository,
            "--yes",
        ]
    )


def labels_equal(
    current: Label,
    desired: Label,
) -> bool:
    """
    Compare two labels.

    Color comparison is case insensitive.
    """

    return (
        current.color.upper()
        == desired.color.upper()
        and current.description
        == desired.description
    )


def sync_labels(
    client: GitHubClient,
    desired_labels: dict[str, Label],
    existing_labels: dict[str, Label],
    overwrite: bool,
) -> SyncResult:
    """
    Synchronize desired labels with GitHub.

    Creates missing labels.

    Updates existing labels only when overwrite
    is enabled and changes are detected.

    """

    result = SyncResult()

    for name, desired in desired_labels.items():

        current = existing_labels.get(name)

        if current is None:

            create_label(
                client,
                desired,
            )

            result.created += 1
            continue

        if labels_equal(
            current,
            desired,
        ):

            logger.info(
                "Skipping unchanged label: %s",
                name,
            )

            result.skipped += 1
            continue

        if overwrite:

            update_label(
                client,
                desired,
            )

            result.updated += 1

        else:

            logger.info(
                "Skipping existing label (overwrite disabled): %s",
                name,
            )

            result.skipped += 1

    return result


def prune_labels(
    client: GitHubClient,
    desired_labels: dict[str, Label],
    existing_labels: dict[str, Label],
) -> int:
    """
    Delete labels which are not defined in CSV.

    Only labels missing from the CSV are removed.
    """

    deleted = 0

    obsolete_labels = (
        set(existing_labels.keys())
        - set(desired_labels.keys())
    )

    for label_name in sorted(obsolete_labels):

        delete_label(
            client,
            label_name,
        )

        deleted += 1

    return deleted
    
    
    
###############################################################################
# Command Line Interface
###############################################################################

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Synchronize GitHub labels from a CSV configuration."
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
        default=DEFAULT_CSV_FILE,
        help=(
            "Path to the labels CSV file. "
            f"Default: {DEFAULT_CSV_FILE}"
        ),
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=(
            "Update existing labels when "
            "color or description changed."
        ),
    )

    parser.add_argument(
        "--prune",
        action="store_true",
        help=(
            "Delete labels that are not defined "
            "in the CSV file."
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
            "Export existing GitHub labels "
            "to CSV and exit."
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

        csv_file = Path(
            args.csv
        )

        client = GitHubClient(
            repository=args.repo,
            dry_run=args.dry_run,
        )

        logger.info(
            "Repository: %s",
            client.repository,
        )

        existing_labels = client.list_labels()

        logger.info(
            "Existing GitHub labels: %s",
            len(existing_labels),
        )

        if args.export:

            export_labels(
                existing_labels,
                Path(args.export),
            )

            return 0

        desired_labels = load_labels(
            csv_file
        )

        result = sync_labels(
            client=client,
            desired_labels=desired_labels,
            existing_labels=existing_labels,
            overwrite=args.overwrite,
        )

        if args.prune:

            result.deleted = prune_labels(
                client=client,
                desired_labels=desired_labels,
                existing_labels=existing_labels,
            )

        logger.info(
            ""
        )

        logger.info(
            "Synchronization summary:"
        )

        logger.info(
            "Created: %s",
            result.created,
        )

        logger.info(
            "Updated: %s",
            result.updated,
        )

        logger.info(
            "Deleted: %s",
            result.deleted,
        )

        logger.info(
            "Skipped: %s",
            result.skipped,
        )

        logger.info(
            "Done."
        )

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
