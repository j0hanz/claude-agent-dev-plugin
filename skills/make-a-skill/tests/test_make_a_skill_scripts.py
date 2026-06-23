"""Tests for skills/make-a-skill/scripts — scaffold_skill, validate_skill."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scaffold_skill import scaffold  # noqa: E402
from validate_skill import _resolve_skill_md, validate_skill  # noqa: E402

_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"


# ---------------------------------------------------------------------------
# scaffold_skill
# ---------------------------------------------------------------------------


def test_scaffold_writes_skill_md_with_real_name(tmp_path: Path) -> None:
    created = scaffold("demo-skill", out_dir=tmp_path)
    skill_md = tmp_path / "demo-skill" / "SKILL.md"
    assert created == [skill_md]
    content = skill_md.read_text(encoding="utf-8")
    assert "name: demo-skill" in content
    assert "{{FILL" in content  # description and body are placeholders


def test_scaffold_rejects_uppercase_name(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        scaffold("Demo-Skill", out_dir=tmp_path)


def test_scaffold_rejects_path_separator_in_name(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        scaffold("demo/skill", out_dir=tmp_path)


def test_scaffold_refuses_overwrite_without_force(tmp_path: Path) -> None:
    scaffold("demo-skill", out_dir=tmp_path)
    with pytest.raises(FileExistsError):
        scaffold("demo-skill", out_dir=tmp_path)
    scaffold("demo-skill", out_dir=tmp_path, force=True)  # does not raise


def test_scaffold_force_does_not_clobber_drafted_skill_md(tmp_path: Path) -> None:
    """Once a scaffolded SKILL.md has been drafted (no '{{FILL' markers left),
    --force must refuse to overwrite it rather than silently destroying the
    drafted content just because the user wanted to add a missing optional
    dir like --evals."""
    scaffold("demo-skill", out_dir=tmp_path)
    skill_md = tmp_path / "demo-skill" / "SKILL.md"
    drafted = (
        '---\nname: demo-skill\ndescription: "a fully drafted real description"\n'
        "---\n\nReal drafted content, no placeholders left.\n"
    )
    skill_md.write_text(drafted, encoding="utf-8")
    with pytest.raises(FileExistsError):
        scaffold("demo-skill", out_dir=tmp_path, force=True)
    assert skill_md.read_text(encoding="utf-8") == drafted


@pytest.mark.parametrize("bad_name", ["", "a--b", "-foo", "foo-", "Demo_Skill", "con"])
def test_scaffold_rejects_degenerate_and_reserved_names(
    tmp_path: Path, bad_name: str
) -> None:
    with pytest.raises(ValueError):
        scaffold(bad_name, out_dir=tmp_path)


def test_scaffold_optional_dirs(tmp_path: Path) -> None:
    created = scaffold(
        "demo-skill",
        out_dir=tmp_path,
        with_scripts=True,
        with_references=True,
        with_evals=True,
    )
    paths = {p.name for p in created}
    assert "demo_skill.py" in paths
    assert "checklist.md" in paths
    assert "evals.json" in paths
    evals_data = json.loads(
        (tmp_path / "demo-skill" / "evals" / "evals.json").read_text()
    )
    assert isinstance(evals_data, list)
    assert len(evals_data) == 1
    assert "expectations" in evals_data[0]


# ---------------------------------------------------------------------------
# validate_skill — structural errors
# ---------------------------------------------------------------------------


def test_freshly_scaffolded_skill_fails_validation(tmp_path: Path) -> None:
    scaffold("demo-skill", out_dir=tmp_path)
    errors, _ = validate_skill(tmp_path / "demo-skill" / "SKILL.md")
    assert any("description" in e and "FILL" in e for e in errors)
    assert any("unfilled" in e for e in errors)


def test_fully_drafted_skill_passes_validation(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """\
---
name: demo-skill
description: "Does a demonstration thing for tests. Not for production use. Trigger on: 'demo skill', 'run the demo'."
disable-model-invocation: false
---

# demo-skill

Does exactly one thing, for test purposes.

## Step 1: Do the thing

Run the thing.
""",
        encoding="utf-8",
    )
    errors, warnings = validate_skill(skill_dir / "SKILL.md")
    assert errors == []


def test_name_directory_mismatch_is_error(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        '---\nname: wrong-name\ndescription: "x" \n---\n\n# demo\n',
        encoding="utf-8",
    )
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert any("does not match" in e for e in errors)


def test_non_kebab_name_matching_non_kebab_directory_is_still_an_error(
    tmp_path: Path,
) -> None:
    """A name that matches its (also non-kebab) directory must still be
    flagged as not kebab-case — the mismatch check and the kebab-case check
    are independent and must not short-circuit each other."""
    skill_dir = tmp_path / "Demo_Skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        '---\nname: Demo_Skill\ndescription: "x"\n---\n\n# demo\n',
        encoding="utf-8",
    )
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert any("not kebab-case" in e for e in errors)
    assert not any("does not match" in e for e in errors)


def test_missing_frontmatter_is_error(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "# demo-skill\n\nNo frontmatter here.\n", encoding="utf-8"
    )
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert any("frontmatter" in e.lower() for e in errors)


def test_dangling_reference_link_is_error(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        '---\nname: demo-skill\ndescription: "long enough description text padded out to a hundred and twenty characters minimum so the warning does not fire here, ok"\n---\n\n'
        "# demo-skill\n\nRead `references/missing.md` for details.\n",
        encoding="utf-8",
    )
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert any("references/missing.md" in e for e in errors)


def test_reference_link_escaping_skill_dir_is_flagged_not_followed(
    tmp_path: Path,
) -> None:
    """A `scripts/../../../etc/passwd`-style link must be reported as a
    dangling reference, never resolved (and followed) outside skill_dir."""
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    outside_secret = tmp_path / "secret.txt"
    outside_secret.write_text("hi", encoding="utf-8")
    (skill_dir / "SKILL.md").write_text(
        '---\nname: demo-skill\ndescription: "long enough description text padded out to a hundred and twenty characters minimum so the warning does not fire here, ok"\n---\n\n'
        "# demo-skill\n\nRead `scripts/../../secret.txt` for details.\n",
        encoding="utf-8",
    )
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert any("scripts/../../secret.txt" in e for e in errors)


def test_placeholder_mentioned_in_code_span_is_not_an_error(tmp_path: Path) -> None:
    """A skill explaining the {{FILL convention in backticks (like make-a-skill's
    own SKILL.md) must not be flagged as having an unfilled placeholder."""
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        '---\nname: demo-skill\ndescription: "long enough description text padded out to a hundred and twenty characters minimum so the warning does not fire here, ok"\n---\n\n'
        "# demo-skill\n\nFill in every `{{FILL: ...}}` placeholder before validating.\n",
        encoding="utf-8",
    )
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert errors == []


# ---------------------------------------------------------------------------
# validate_skill — evals.json shape variants
# ---------------------------------------------------------------------------


def _base_skill(tmp_path: Path) -> Path:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        '---\nname: demo-skill\ndescription: "long enough description text padded out to a hundred and twenty characters minimum so the warning does not fire here, ok"\n---\n\n'
        "# demo-skill\n\nDoes a thing.\n",
        encoding="utf-8",
    )
    return skill_dir


def test_evals_bare_array_shape_is_valid(tmp_path: Path) -> None:
    skill_dir = _base_skill(tmp_path)
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir()
    (evals_dir / "evals.json").write_text(
        json.dumps([{"prompt": "do the thing", "assertions": ["it did the thing"]}]),
        encoding="utf-8",
    )
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert errors == []


def test_evals_object_shape_is_valid(tmp_path: Path) -> None:
    skill_dir = _base_skill(tmp_path)
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir()
    (evals_dir / "evals.json").write_text(
        json.dumps(
            {
                "skill_name": "demo-skill",
                "evals": [
                    {"prompt": "do the thing", "expectations": ["it did the thing"]}
                ],
            }
        ),
        encoding="utf-8",
    )
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert errors == []


def test_malformed_evals_json_is_error(tmp_path: Path) -> None:
    skill_dir = _base_skill(tmp_path)
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir()
    (evals_dir / "evals.json").write_text("{not valid json", encoding="utf-8")
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert any("not valid JSON" in e for e in errors)


def test_vague_adjective_is_warning_not_error(tmp_path: Path) -> None:
    skill_dir = _base_skill(tmp_path)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        skill_md.read_text(encoding="utf-8") + "\nThis is a simple and robust step.\n",
        encoding="utf-8",
    )
    errors, warnings = validate_skill(skill_md)
    assert errors == []
    assert any("simple" in w for w in warnings)
    assert any("robust" in w for w in warnings)


def test_reference_path_inside_fenced_code_block_is_not_flagged(tmp_path: Path) -> None:
    """A references/scripts/evals-looking path that only appears inside a
    fenced (triple-backtick) example must not be treated as a real link —
    only a genuine inline-backtick or markdown-link reference should be
    existence-checked."""
    skill_dir = _base_skill(tmp_path)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        skill_md.read_text(encoding="utf-8")
        + "\n```\nexample layout: references/not-a-real-file.md\n```\n",
        encoding="utf-8",
    )
    errors, _ = validate_skill(skill_md)
    assert errors == []


def test_disable_model_invocation_must_be_lowercase_bool_literal(
    tmp_path: Path,
) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        '---\nname: demo-skill\ndescription: "long enough description text padded out to a hundred and twenty characters minimum so the warning does not fire here, ok"\ndisable-model-invocation: False\n---\n\n'
        "# demo-skill\n\nDoes a thing.\n",
        encoding="utf-8",
    )
    _, warnings = validate_skill(skill_dir / "SKILL.md")
    assert any("disable-model-invocation" in w for w in warnings)


def test_description_missing_trigger_clause_is_warning(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        '---\nname: demo-skill\ndescription: "long enough description text padded out to a hundred and twenty characters minimum, but with no trigger clause at all"\n---\n\n'
        "# demo-skill\n\nDoes a thing.\n",
        encoding="utf-8",
    )
    _, warnings = validate_skill(skill_dir / "SKILL.md")
    assert any("Trigger on" in w for w in warnings)


def test_description_too_short_is_warning(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        '---\nname: demo-skill\ndescription: "too short"\n---\n\n# demo-skill\n\nDoes a thing.\n',
        encoding="utf-8",
    )
    _, warnings = validate_skill(skill_dir / "SKILL.md")
    assert any("too terse" in w for w in warnings)


def test_description_too_long_is_warning(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    long_desc = "x" * 1100 + " Trigger on: 'demo'."
    (skill_dir / "SKILL.md").write_text(
        f'---\nname: demo-skill\ndescription: "{long_desc}"\n---\n\n# demo-skill\n\nDoes a thing.\n',
        encoding="utf-8",
    )
    _, warnings = validate_skill(skill_dir / "SKILL.md")
    assert any("ceiling" in w for w in warnings)


def test_body_over_token_budget_is_warning(tmp_path: Path) -> None:
    skill_dir = _base_skill(tmp_path)
    skill_md = skill_dir / "SKILL.md"
    huge_body = "word " * 6000  # well over the ~5000-token estimate
    skill_md.write_text(
        skill_md.read_text(encoding="utf-8") + "\n" + huge_body + "\n", encoding="utf-8"
    )
    _, warnings = validate_skill(skill_md)
    assert any("token" in w.lower() for w in warnings)


def test_passive_voice_is_warning(tmp_path: Path) -> None:
    skill_dir = _base_skill(tmp_path)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        skill_md.read_text(encoding="utf-8")
        + "\nThe file is be parsed by the script.\n",
        encoding="utf-8",
    )
    _, warnings = validate_skill(skill_md)
    assert any("passive voice" in w.lower() for w in warnings)


def test_unreferenced_sibling_script_file_is_warning(tmp_path: Path) -> None:
    skill_dir = _base_skill(tmp_path)
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "helper.py").write_text(
        "# never mentioned in SKILL.md\n", encoding="utf-8"
    )
    _, warnings = validate_skill(skill_dir / "SKILL.md")
    assert any("helper.py" in w for w in warnings)


def test_evals_case_missing_prompt_is_error(tmp_path: Path) -> None:
    skill_dir = _base_skill(tmp_path)
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir()
    (evals_dir / "evals.json").write_text(
        json.dumps([{"assertions": ["something"]}]), encoding="utf-8"
    )
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert any("missing required field 'prompt'" in e for e in errors)


def test_evals_case_without_assertions_or_expectations_is_warning(
    tmp_path: Path,
) -> None:
    skill_dir = _base_skill(tmp_path)
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir()
    (evals_dir / "evals.json").write_text(
        json.dumps([{"prompt": "do the thing"}]), encoding="utf-8"
    )
    _, warnings = validate_skill(skill_dir / "SKILL.md")
    assert any("no checkable success criteria" in w for w in warnings)


def test_evals_case_with_fill_placeholder_is_error(tmp_path: Path) -> None:
    skill_dir = _base_skill(tmp_path)
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir()
    (evals_dir / "evals.json").write_text(
        json.dumps([{"prompt": "FILL: a realistic prompt", "assertions": ["x"]}]),
        encoding="utf-8",
    )
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert any("unfilled 'FILL:' placeholder" in e for e in errors)


def test_evals_case_not_an_object_is_error(tmp_path: Path) -> None:
    skill_dir = _base_skill(tmp_path)
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir()
    (evals_dir / "evals.json").write_text(
        json.dumps(["not an object"]), encoding="utf-8"
    )
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert any("must be an object" in e for e in errors)


def test_evals_empty_cases_list_is_error(tmp_path: Path) -> None:
    skill_dir = _base_skill(tmp_path)
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir()
    (evals_dir / "evals.json").write_text(json.dumps([]), encoding="utf-8")
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert any("non-empty list" in e for e in errors)


def test_evals_skill_name_mismatch_is_warning(tmp_path: Path) -> None:
    skill_dir = _base_skill(tmp_path)
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir()
    (evals_dir / "evals.json").write_text(
        json.dumps(
            {
                "skill_name": "other-skill",
                "evals": [{"prompt": "do the thing", "assertions": ["x"]}],
            }
        ),
        encoding="utf-8",
    )
    _, warnings = validate_skill(skill_dir / "SKILL.md")
    assert any("does not match the skill directory" in w for w in warnings)


# ---------------------------------------------------------------------------
# validate_skill — _resolve_skill_md path resolution
# ---------------------------------------------------------------------------


def test_resolve_skill_md_accepts_explicit_skill_md_path(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("x", encoding="utf-8")
    assert _resolve_skill_md(str(skill_md)) == skill_md.resolve()


def test_resolve_skill_md_accepts_directory_path(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    assert _resolve_skill_md(str(skill_dir)) == (skill_dir / "SKILL.md").resolve()


def test_resolve_skill_md_finds_bare_name_under_dot_claude_skills(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    skill_dir = tmp_path / ".claude" / "skills" / "demo-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("x", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert _resolve_skill_md("demo-skill") == (skill_dir / "SKILL.md").resolve()


def test_resolve_skill_md_finds_bare_name_under_plugin_skills(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    skill_dir = tmp_path / "skills" / "demo-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("x", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert _resolve_skill_md("demo-skill") == (skill_dir / "SKILL.md").resolve()


def test_resolve_skill_md_bare_name_with_no_match_falls_back_to_dot_claude_skills(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert (
        _resolve_skill_md("nonexistent-skill")
        == (
            tmp_path / ".claude" / "skills" / "nonexistent-skill" / "SKILL.md"
        ).resolve()
    )


# ---------------------------------------------------------------------------
# CLI entry points (subprocess — exercises argparse wiring and exit codes)
# ---------------------------------------------------------------------------


def test_scaffold_cli_creates_skill_and_prints_next_steps(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPTS_DIR / "scaffold_skill.py"),
            "demo-skill",
            "--dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Created:" in result.stdout
    assert "validate_skill.py demo-skill" in result.stdout
    assert (tmp_path / "demo-skill" / "SKILL.md").exists()


def test_scaffold_cli_invalid_name_exits_nonzero(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPTS_DIR / "scaffold_skill.py"),
            "Bad_Name",
            "--dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Invalid name" in result.stderr


def test_validate_cli_exits_zero_on_valid_skill(tmp_path: Path) -> None:
    skill_dir = _base_skill(tmp_path)
    result = subprocess.run(
        [sys.executable, str(_SCRIPTS_DIR / "validate_skill.py"), str(skill_dir)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "VALID" in result.stdout


def test_validate_cli_exits_nonzero_on_errors(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# no frontmatter\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(_SCRIPTS_DIR / "validate_skill.py"), str(skill_dir)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "INVALID" in result.stdout
    assert "ERRORS:" in result.stdout


def test_validate_cli_strict_fails_on_warnings_only(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        '---\nname: demo-skill\ndescription: "too short"\n---\n\n# demo-skill\n\nDoes a thing.\n',
        encoding="utf-8",
    )
    # Without --strict: warnings alone don't fail the run.
    lenient = subprocess.run(
        [sys.executable, str(_SCRIPTS_DIR / "validate_skill.py"), str(skill_dir)],
        capture_output=True,
        text=True,
    )
    assert lenient.returncode == 0

    strict = subprocess.run(
        [
            sys.executable,
            str(_SCRIPTS_DIR / "validate_skill.py"),
            str(skill_dir),
            "--strict",
        ],
        capture_output=True,
        text=True,
    )
    assert strict.returncode == 1
    assert "INVALID" in strict.stdout


def test_validate_cli_prints_errors_before_warnings(tmp_path: Path) -> None:
    """ERRORS: should appear before WARNINGS: in the output so the
    actionable failures aren't buried below informational warnings."""
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        '---\nname: wrong-name\ndescription: "too short"\n---\n\n# demo\n',
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(_SCRIPTS_DIR / "validate_skill.py"), str(skill_dir)],
        capture_output=True,
        text=True,
    )
    assert result.stdout.index("ERRORS:") < result.stdout.index("WARNINGS:")
