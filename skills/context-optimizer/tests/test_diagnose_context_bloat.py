"""Tests for context-optimizer diagnose_context_bloat."""

import diagnose_context_bloat


def test_parse_gitignore(tmp_path):
    (tmp_path / ".gitignore").write_text(
        "node_modules/\n# comment\ndist\n", encoding="utf-8"
    )
    ignores = diagnose_context_bloat.parse_gitignore(tmp_path)
    assert ignores == {"node_modules", "dist"}


def test_scan_files_flags_unignored_heavy_dir(tmp_path):
    (tmp_path / "node_modules").mkdir()
    large_files, unignored_dirs = diagnose_context_bloat.scan_files(tmp_path, set())
    assert "node_modules" in unignored_dirs


def test_scan_files_respects_gitignore(tmp_path):
    (tmp_path / "node_modules").mkdir()
    large_files, unignored_dirs = diagnose_context_bloat.scan_files(
        tmp_path, {"node_modules"}
    )
    assert "node_modules" not in unignored_dirs


def test_scan_files_flags_oversized_loc(tmp_path):
    big_file = tmp_path / "big.py"
    big_file.write_text("\n".join(f"x = {i}" for i in range(600)), encoding="utf-8")
    large_files, _ = diagnose_context_bloat.scan_files(tmp_path, set())
    assert any(f.name == "big.py" for f, _, _ in large_files)


def test_scan_files_flags_lockfile(tmp_path):
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    large_files, _ = diagnose_context_bloat.scan_files(tmp_path, set())
    assert any(reason == "Lockfile" for _, reason, _ in large_files)


def test_check_instruction_stubs_flags_verbose_claude_md(tmp_path):
    (tmp_path / "CLAUDE.md").write_text(
        "\n".join(f"line {i}" for i in range(10)), encoding="utf-8"
    )
    warnings = diagnose_context_bloat.check_instruction_stubs(tmp_path)
    assert warnings


def test_check_instruction_stubs_allows_stub_referencing_agents_md(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("See AGENTS.md", encoding="utf-8")
    warnings = diagnose_context_bloat.check_instruction_stubs(tmp_path)
    assert not warnings
