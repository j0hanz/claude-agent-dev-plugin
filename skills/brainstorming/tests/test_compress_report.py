"""Tests for brainstorming compress_report."""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

import compress_report  # noqa: E402


def test_compress_report_empty():
    report = {"feature_area": "Test", "related_files": []}
    cfg = compress_report.CompressConfig()
    compressed = compress_report.compress(report, cfg)
    assert isinstance(compressed, dict)
    assert compressed["feature_area"] == "Test"
    assert "_compressed" in compressed


def test_compress_report_with_data():
    report = {
        "feature_area": "Test",
        "related_files": [
            {"path": "src/main.py", "last_commit": "Initial commit", "has_tests": True}
        ],
        "interface_shapes": ["Class User"],
        "unknowns": ["How is auth handled?"],
        "analogous_features": ["Auth"],
    }
    cfg = compress_report.CompressConfig()
    compressed = compress_report.compress(report, cfg)
    assert compressed["related_files"][0]["path"] == "src/main.py"
    assert "Class User" in compressed["interface_shapes"]
    assert "How is auth handled?" in compressed["unknowns"]
    assert "Auth" in compressed["analogous_features"]


def test_compress_report_invalid_type():
    import pytest

    cfg = compress_report.CompressConfig()
    with pytest.raises(TypeError, match="expected a JSON object"):
        compress_report.compress([1, 2, 3], cfg)


def test_non_negative_int_validation():
    import pytest
    import argparse

    assert compress_report._non_negative_int("5") == 5
    assert compress_report._non_negative_int("0") == 0
    with pytest.raises(argparse.ArgumentTypeError, match="value must be >= 0"):
        compress_report._non_negative_int("-1")
    with pytest.raises(argparse.ArgumentTypeError, match="invalid int value"):
        compress_report._non_negative_int("not-an-int")
