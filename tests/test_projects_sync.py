"""Test cases for project field and option synchronization."""

from gh_sync_projects import (
    FieldOption,
    Project,
    ProjectField,
    RemoteFieldOption,
    RemoteProjectField,
    option_equal,
    projects_equal,
    sync_field_options,
    sync_fields,
)


class FakeClient:
    """Small fake client used for sync tests."""

    def __init__(self):
        self.created_fields: list[str] = []
        self.deleted_fields: list[str] = []
        self.created_options: list[tuple[str, str]] = []
        self.updated_options: list[tuple[str, str]] = []
        self.deleted_options: list[tuple[str, str]] = []

    def create_field(self, project_id: str, field: ProjectField) -> str:
        self.created_fields.append(field.name)
        return f"field-{field.name}"

    def delete_field(self, field_id: str) -> None:
        self.deleted_fields.append(field_id)

    def create_single_select_option(self, field_id: str, option: FieldOption) -> None:
        self.created_options.append((field_id, option.name))

    def update_single_select_option(
        self,
        project_id: str,
        field_id: str,
        option_id: str,
        option: FieldOption,
    ) -> None:
        self.updated_options.append((field_id, option.name))

    def delete_single_select_option(
        self,
        project_id: str,
        field_id: str,
        option_id: str,
    ) -> None:
        self.deleted_options.append((field_id, option_id))


class TestProjectComparison:
    def test_projects_equal(self):
        current = Project(name="Development", description="Board", visibility="private")
        desired = Project(name="Development", description="Board", visibility="private")
        assert projects_equal(current, desired)

    def test_option_equal(self):
        current = RemoteFieldOption(id="1", name="Todo", color="gray", description="Ready")
        desired = FieldOption(name="Todo", color="GRAY", description="Ready")
        assert option_equal(current, desired)


class TestFieldOptionSync:
    def test_sync_field_options_create_update_delete(self):
        client = FakeClient()
        desired_field = ProjectField(
            name="Status",
            field_type="single_select",
            options=(
                FieldOption(name="Todo", color="GRAY", description="Ready"),
                FieldOption(name="Done", color="GREEN", description="Completed"),
            ),
        )
        current_field = RemoteProjectField(
            id="field-status",
            name="Status",
            field_type="single_select",
            options={
                "Todo": RemoteFieldOption(
                    id="opt-1",
                    name="Todo",
                    color="GRAY",
                    description="Old",
                ),
                "Blocked": RemoteFieldOption(
                    id="opt-2",
                    name="Blocked",
                    color="RED",
                    description="Blocked",
                ),
            },
        )

        result = sync_field_options(
            client=client,
            project_id="project-1",
            desired_field=desired_field,
            current_field=current_field,
            overwrite=True,
            prune=True,
        )

        assert result.created == 1
        assert result.updated == 1
        assert result.deleted == 1
        assert result.skipped == 0


class TestFieldSync:
    def test_sync_fields_creates_new_field_and_options(self):
        client = FakeClient()
        desired_fields = {
            "Status": ProjectField(
                name="Status",
                field_type="single_select",
                options=(
                    FieldOption(name="Todo", color="GRAY", description="Ready"),
                ),
            )
        }

        result = sync_fields(
            client=client,
            project_id="project-1",
            desired_fields=desired_fields,
            existing_fields={},
            overwrite=False,
            prune=False,
        )

        assert result.created == 2
        assert result.updated == 0
        assert result.deleted == 0
        assert "Status" in client.created_fields
        assert ("field-Status", "Todo") in client.created_options
