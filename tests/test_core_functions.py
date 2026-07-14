"""
Test cases for core label functions.
"""

from unittest import mock

import pytest

from gh_sync_labels import (
    GitHubClient,
    Label,
    labels_equal,
    normalize_color,
    prune_labels,
    sync_labels,
    validate_label,
)


class TestColorNormalization:
    def test_normalize_color_without_hash(self):
        assert normalize_color("D73A4A") == "D73A4A"

    def test_normalize_color_with_hash(self):
        assert normalize_color("#D73A4A") == "D73A4A"

    def test_normalize_color_lowercase(self):
        assert normalize_color("d73a4a") == "D73A4A"

    def test_normalize_color_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid color format"):
            normalize_color("ZZZ")


class TestLabelValidation:
    def test_validate_label_valid(self):
        validate_label(Label(name="bug", color="D73A4A", description="A bug"))

    def test_validate_label_empty_name(self):
        with pytest.raises(ValueError, match="Label name must not be empty"):
            validate_label(Label(name="", color="D73A4A", description="x"))

    def test_validate_label_empty_color(self):
        with pytest.raises(ValueError, match="Missing color"):
            validate_label(Label(name="bug", color="", description="x"))

    def test_validate_label_empty_description(self):
        with pytest.raises(ValueError, match="Missing description"):
            validate_label(Label(name="bug", color="D73A4A", description=""))


class TestLabelComparison:
    def test_labels_equal_identical(self):
        a = Label(name="bug", color="D73A4A", description="A bug")
        b = Label(name="bug", color="D73A4A", description="A bug")
        assert labels_equal(a, b)

    def test_labels_equal_case_insensitive_color(self):
        a = Label(name="bug", color="D73A4A", description="A bug")
        b = Label(name="bug", color="d73a4a", description="A bug")
        assert labels_equal(a, b)

    def test_labels_different_color(self):
        a = Label(name="bug", color="D73A4A", description="A bug")
        b = Label(name="bug", color="1D76DB", description="A bug")
        assert not labels_equal(a, b)


class TestSyncAndPrune:
    @mock.patch("subprocess.run")
    def test_sync_create_new_label(self, mock_run):
        mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
        client = GitHubClient(repository="owner/repo")

        desired = {"bug": Label(name="bug", color="D73A4A", description="A bug")}
        result = sync_labels(client, desired, {}, overwrite=False)

        assert result.created == 1
        assert result.updated == 0
        assert result.skipped == 0

    @mock.patch("subprocess.run")
    def test_sync_update_with_overwrite(self, mock_run):
        mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
        client = GitHubClient(repository="owner/repo")

        desired = {"bug": Label(name="bug", color="FF0000", description="New")}
        existing = {"bug": Label(name="bug", color="D73A4A", description="Old")}
        result = sync_labels(client, desired, existing, overwrite=True)

        assert result.updated == 1

    @mock.patch("subprocess.run")
    def test_prune_delete_obsolete_labels(self, mock_run):
        mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
        client = GitHubClient(repository="owner/repo")

        desired = {"bug": Label(name="bug", color="D73A4A", description="Bug")}
        existing = {
            "bug": Label(name="bug", color="D73A4A", description="Bug"),
            "old": Label(name="old", color="CCCCCC", description="Old"),
        }

        deleted = prune_labels(client, desired, existing)
        assert deleted == 1
