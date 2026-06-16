"""Tests for brainstorming compress_report."""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

import compress_report  # noqa: E402


def test_compress_report_empty():
    report = {"files": [], "key_unknowns": [], "analogous_features": []}
    compressed = compress_report.compress(report)
    assert isinstance(compressed, str)
    assert "Codebase Context Report" in compressed


def test_compress_report_with_data():
    report = {
        "files": [{"path": "src/main.py", "summary": "Main entry point."}],
        "key_unknowns": ["How is auth handled?"],
        "analogous_features": [{"name": "Auth", "path": "src/auth.py"}],
    }
    compressed = compress_report.compress(report)
    assert "src/main.py" in compressed
    assert "How is auth handled?" in compressed
    assert "src/auth.py" in compressed
