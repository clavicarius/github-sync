"""
Test cases for CSV loading and handling.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from gh_sync_labels import load_labels


class TestLoadLabels:
    def test_load_valid_csv(self):
        with TemporaryDirectory() as tmpdir:
            csv_file = Path(tmpdir) / "labels.csv"
            csv_file.write_text(
                "Category;Label;Color;Description\n"
                ";bug;D73A4A;A bug\n"
                ";feature;1D76DB;A feature\n",
                encoding="utf-8",
            )

            labels = load_labels(csv_file)
            assert len(labels) == 2
            assert "bug" in labels
            assert "feature" in labels

    def test_load_csv_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="CSV file not found"):
            load_labels(Path("nonexistent.csv"))

    def test_load_csv_missing_columns(self):
        with TemporaryDirectory() as tmpdir:
            csv_file = Path(tmpdir) / "labels.csv"
            csv_file.write_text("Category;Label;Color\n;bug;D73A4A\n", encoding="utf-8")

            with pytest.raises(ValueError, match="Missing CSV columns"):
                load_labels(csv_file)

    def test_load_csv_invalid_color(self):
        with TemporaryDirectory() as tmpdir:
            csv_file = Path(tmpdir) / "labels.csv"
            csv_file.write_text(
                "Category;Label;Color;Description\n;bug;INVALID;A bug\n",
                encoding="utf-8",
            )

            with pytest.raises(ValueError, match="Invalid CSV row"):
                load_labels(csv_file)

    def test_load_csv_duplicate_labels(self):
        with TemporaryDirectory() as tmpdir:
            csv_file = Path(tmpdir) / "labels.csv"
            csv_file.write_text(
                "Category;Label;Color;Description\n"
                ";bug;D73A4A;A bug\n"
                ";bug;FF0000;Another bug\n",
                encoding="utf-8",
            )

            with pytest.raises(ValueError, match="Duplicate label name"):
                load_labels(csv_file)
