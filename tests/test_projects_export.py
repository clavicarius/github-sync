"""Test cases for project configuration export."""

from pathlib import Path
from tempfile import TemporaryDirectory

from gh_sync_projects import (
    FieldOption,
    Project,
    ProjectField,
    export_project_configuration,
    load_project_configuration,
)


class TestProjectExport:
    def test_export_and_reload_configuration(self):
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            project = Project(
                name="Development",
                description="Planning board",
                visibility="private",
            )
            fields = {
                "Status": ProjectField(
                    name="Status",
                    field_type="single_select",
                    options=(
                        FieldOption(name="Todo", color="GRAY", description="Ready"),
                        FieldOption(name="Done", color="GREEN", description="Completed"),
                    ),
                ),
                "Effort": ProjectField(
                    name="Effort",
                    field_type="number",
                ),
            }

            export_project_configuration(project, fields, output_dir)

            assert (output_dir / "project.csv").exists()
            assert (output_dir / "fields.csv").exists()
            assert (output_dir / "status.csv").exists()

            reloaded = load_project_configuration(output_dir)

            assert reloaded.project == project
            assert set(reloaded.fields.keys()) == set(fields.keys())
            assert len(reloaded.fields["Status"].options) == 2
