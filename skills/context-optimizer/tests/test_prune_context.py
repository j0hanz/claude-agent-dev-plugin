"""Tests for context-optimizer prune_context."""

import prune_context


def test_to_markdown_kv_simple():
    data = {"status": "success", "files_changed": 3}
    lines = prune_context.to_markdown_kv(data)
    assert "status: success" in lines
    assert "files_changed: 3" in lines


def test_to_markdown_kv_nested():
    data = {
        "status": "failure",
        "details": {"errors": ["NullPointer", "AuthException"], "code": 500},
    }
    lines = prune_context.to_markdown_kv(data)
    assert "status: failure" in lines
    assert "details_errors: NullPointer, AuthException" in lines
    assert "details_code: 500" in lines


def test_filter_logs_no_errors():
    logs = "\n".join(f"Test case {i} passed." for i in range(20))
    filtered = prune_context.filter_logs(logs)
    assert "... [omitted 10 lines of passing logs] ..." in filtered
    assert "Test case 0 passed." in filtered
    assert "Test case 19 passed." in filtered


def test_filter_logs_with_traceback():
    logs = (
        "Suite started\n"
        "Initializing database\n"
        "Traceback (most recent call last):\n"
        '  File "main.py", line 10, in <module>\n'
        "    run_app()\n"
        "ValueError: invalid configuration\n"
        "Clean teardown completed\n"
    )
    filtered = prune_context.filter_logs(logs)
    assert "Traceback (most recent call last):" in filtered
    assert "ValueError: invalid configuration" in filtered
    assert "Initializing database" in filtered


def test_update_rolling_summary(tmp_path):
    summary_file = tmp_path / "rolling_summary.md"

    # 1. First entry
    prune_context.update_rolling_summary(
        summary_file,
        timestamp="2026-06-21T10:00:00",
        done="created api stub",
        blocking="none",
        next_step="test endpoints",
        decisions="use fastAPI",
        current_skill="test-driven-development",
    )

    content1 = summary_file.read_text(encoding="utf-8")
    assert "done: created api stub" in content1
    assert "current_skill: test-driven-development" in content1
    assert "## Session: 2026-06-21T10:00:00" in content1

    # 2. Second entry
    prune_context.update_rolling_summary(
        summary_file,
        timestamp="2026-06-22T10:00:00",
        done="wrote unit tests",
        blocking="env configs",
        next_step="deploy to dev",
        decisions="pinned requirements",
    )

    content2 = summary_file.read_text(encoding="utf-8")
    assert "done: wrote unit tests" in content2
    assert "## Session: 2026-06-21T10:00:00" in content2

    # 3. Third entry
    prune_context.update_rolling_summary(
        summary_file,
        timestamp="2026-06-23T10:00:00",
        done="deployed to dev",
        blocking="none",
        next_step="monitor performance",
        decisions="none",
    )

    content3 = summary_file.read_text(encoding="utf-8")
    assert "## Session: 2026-06-23T10:00:00" in content3
    assert "## Session: 2026-06-22T10:00:00" in content3
    assert "## Session: 2026-06-21T10:00:00" in content3

    # 4. Fourth entry - triggers collapsing on the earliest (2026-06-21)
    prune_context.update_rolling_summary(
        summary_file,
        timestamp="2026-06-24T10:00:00",
        done="monitored app",
        blocking="none",
        next_step="done",
        decisions="none",
    )

    content4 = summary_file.read_text(encoding="utf-8")
    assert "## Session: 2026-06-24T10:00:00 (Current)" in content4
    assert "## Session: 2026-06-21T10:00:00 (Archived)" in content4
    assert "- created api stub" in content4
    assert (
        "blocking: none"
        not in content4.split("## Session: 2026-06-21T10:00:00 (Archived)")[1]
    )
