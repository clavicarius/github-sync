"""
Test cases for GitHubClient class.
"""

import json
from unittest import mock

import pytest

from gh_sync_labels import GitHubClient


class TestGitHubClientInit:
    @mock.patch.object(GitHubClient, "get_current_repository")
    def test_init_with_repository(self, mock_get_repo):
        client = GitHubClient(repository="owner/repo")
        assert client.repository == "owner/repo"
        mock_get_repo.assert_not_called()

    @mock.patch("subprocess.run")
    def test_init_without_repository(self, mock_run):
        mock_run.return_value = mock.Mock(returncode=0, stdout="current/repo\n", stderr="")

        client = GitHubClient()
        assert client.repository == "current/repo"
        mock_run.assert_called_once()


class TestGitHubClientRun:
    @mock.patch("subprocess.run")
    def test_run_success(self, mock_run):
        mock_run.return_value = mock.Mock(returncode=0, stdout="output", stderr="")
        client = GitHubClient(repository="owner/repo")
        assert client.run(["repo", "view"]) == "output"

    @mock.patch("subprocess.run")
    def test_run_failure_raises_runtime_error(self, mock_run):
        mock_run.return_value = mock.Mock(returncode=1, stdout="", stderr="error message")
        client = GitHubClient(repository="owner/repo")

        with pytest.raises(RuntimeError, match="error message"):
            client.run(["repo", "view"])

    @mock.patch("subprocess.run")
    def test_dry_run_skips_subprocess(self, mock_run):
        client = GitHubClient(repository="owner/repo", dry_run=True)
        result = client.run(["label", "delete", "x"])

        mock_run.assert_not_called()
        assert result == ""

    @mock.patch("subprocess.run")
    def test_dry_run_label_list_executes_subprocess(self, mock_run):
        mock_run.return_value = mock.Mock(returncode=0, stdout="[]", stderr="")
        client = GitHubClient(repository="owner/repo", dry_run=True)

        result = client.run(["label", "list", "--json", "name,color,description"])

        mock_run.assert_called_once()
        assert result == "[]"

    @mock.patch("subprocess.run")
    def test_dry_run_label_list_logs_read_marker(self, mock_run, caplog):
        mock_run.return_value = mock.Mock(returncode=0, stdout="[]", stderr="")
        client = GitHubClient(repository="owner/repo", dry_run=True)

        with caplog.at_level("INFO"):
            client.run(["label", "list", "--json", "name,color,description"])

        assert "[DRY-RUN:READ] gh label list --json name,color,description" in caplog.text

    @mock.patch("subprocess.run")
    def test_dry_run_write_logs_skip_marker(self, mock_run, caplog):
        client = GitHubClient(repository="owner/repo", dry_run=True)

        with caplog.at_level("INFO"):
            client.run(["label", "delete", "x"])

        mock_run.assert_not_called()
        assert "[DRY-RUN] gh label delete x" in caplog.text


class TestGitHubClientListLabels:
    @mock.patch("subprocess.run")
    def test_list_labels_empty(self, mock_run):
        mock_run.return_value = mock.Mock(returncode=0, stdout="[]", stderr="")
        client = GitHubClient(repository="owner/repo")
        assert client.list_labels() == {}

    @mock.patch("subprocess.run")
    def test_list_labels_single(self, mock_run):
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps([{"name": "bug", "color": "D73A4A", "description": "A bug"}]),
            stderr="",
        )

        client = GitHubClient(repository="owner/repo")
        labels = client.list_labels()

        assert len(labels) == 1
        assert labels["bug"].name == "bug"
        assert labels["bug"].color == "D73A4A"
        assert labels["bug"].description == "A bug"
