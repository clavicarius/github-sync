"""Test cases for project CSV parsing and validation."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from gh_sync_projects import (
    ProjectConfiguration,
    load_project_configuration,
)


class TestProjectCsvLoading:
    def test_load_valid_project_configuration(self):
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "project.csv").write_text(
                "Name;Description;Visibility\n"
                "Development;Planning board;private\n",
                encoding="utf-8",
            )
            (config_dir / "fields.csv").write_text(
                "Name;Type\n"
                "Status;single_select\n"
                "Effort;number\n",
                encoding="utf-8",
            )
            (config_dir / "status.csv").write_text(
                "Field;Option;Color;Description\n"
                "Status;Todo;GRAY;Ready\n"
                "Status;Done;GREEN;Complete\n",
                encoding="utf-8",
            )

            configuration = load_project_configuration(config_dir)

            assert isinstance(configuration, ProjectConfiguration)
            assert configuration.project.name == "Development"
            assert configuration.project.visibility == "private"
            assert set(configuration.fields.keys()) == {"Status", "Effort"}
            assert len(configuration.fields["Status"].options) == 2

    def test_missing_required_columns_fails(self):
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "project.csv").write_text(
                "Name;Visibility\n"
                "Development;private\n",
                encoding="utf-8",
            )
            (config_dir / "fields.csv").write_text(
                "Name;Type\n"
                "Status;single_select\n",
                encoding="utf-8",
            )

            with pytest.raises(ValueError, match="Missing CSV columns"):
                load_project_configuration(config_dir)

    def test_invalid_field_type_fails(self):
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "project.csv").write_text(
                "Name;Description;Visibility\n"
                "Development;Planning board;private\n",
                encoding="utf-8",
            )
            (config_dir / "fields.csv").write_text(
                "Name;Type\n"
                "Status;invalid\n",
                encoding="utf-8",
            )

            with pytest.raises(ValueError, match="Invalid field type"):
                load_project_configuration(config_dir)

    def test_invalid_option_color_fails(self):
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "project.csv").write_text(
                "Name;Description;Visibility\n"
                "Development;Planning board;private\n",
                encoding="utf-8",
            )
            (config_dir / "fields.csv").write_text(
                "Name;Type\n"
                "Status;single_select\n",
                encoding="utf-8",
            )
            (config_dir / "status.csv").write_text(
                "Field;Option;Color;Description\n"
                "Status;Todo;INVALID;Ready\n",
                encoding="utf-8",
            )

            with pytest.raises(ValueError, match="Invalid option color"):
                load_project_configuration(config_dir)

    def test_duplicate_option_names_fail(self):
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "project.csv").write_text(
                "Name;Description;Visibility\n"
                "Development;Planning board;private\n",
                encoding="utf-8",
            )
            (config_dir / "fields.csv").write_text(
                "Name;Type\n"
                "Status;single_select\n",
                encoding="utf-8",
            )
            (config_dir / "status.csv").write_text(
                "Field;Option;Color;Description\n"
                "Status;Todo;GRAY;Ready\n"
                "Status;Todo;GREEN;Done\n",
                encoding="utf-8",
            )

            with pytest.raises(ValueError, match="Duplicate option"):
                load_project_configuration(config_dir)
