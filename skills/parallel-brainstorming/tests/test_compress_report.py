"""Tests for parallel-brainstorming compress_report."""

import compress_report


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
