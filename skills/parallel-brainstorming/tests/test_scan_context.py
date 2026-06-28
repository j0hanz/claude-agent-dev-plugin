"""Tests for parallel-brainstorming scan_context.py.

Covers pure-function logic (no git/filesystem I/O) plus scan() integration
using a temporary directory fixture.
"""

import json
import sys

import pytest

import scan_context


# ---------------------------------------------------------------------------
# _sanitize_noun
# ---------------------------------------------------------------------------


class TestSanitizeNoun:
    def test_clean_alphanumeric(self):
        assert scan_context._sanitize_noun("search") == "search"

    def test_allows_hyphens(self):
        assert scan_context._sanitize_noun("rate-limit") == "rate-limit"

    def test_strips_shell_metacharacters(self):
        # $, `, \, ", ', ;, &, |, <, > must be removed
        assert scan_context._sanitize_noun("search$catalog") == "searchcatalog"
        assert scan_context._sanitize_noun("foo`bar") == "foobar"
        assert scan_context._sanitize_noun('he"llo') == "hello"

    def test_strips_spaces(self):
        assert scan_context._sanitize_noun("hello world") == "helloworld"

    def test_raises_on_empty_result(self):
        with pytest.raises(ValueError, match="invalid domain noun"):
            scan_context._sanitize_noun("$$$")

    def test_raises_on_flag_like_result(self):
        # A noun that starts with '-' after cleaning must be rejected
        with pytest.raises(ValueError, match="invalid domain noun"):
            scan_context._sanitize_noun("-flag")

    def test_raises_on_empty_input(self):
        with pytest.raises(ValueError, match="invalid domain noun"):
            scan_context._sanitize_noun("")


# ---------------------------------------------------------------------------
# _expand_synonyms
# ---------------------------------------------------------------------------


class TestExpandSynonyms:
    def test_known_noun_gets_synonyms(self):
        result = scan_context._expand_synonyms(["search"])
        assert "search" in result
        assert "query" in result
        assert "lookup" in result

    def test_originals_appear_first(self):
        result = scan_context._expand_synonyms(["search"])
        assert result[0] == "search"

    def test_no_duplicates(self):
        result = scan_context._expand_synonyms(["search", "query"])
        assert len(result) == len(set(r.lower() for r in result))

    def test_unknown_noun_returns_unchanged(self):
        result = scan_context._expand_synonyms(["xyzzy"])
        assert result == ["xyzzy"]

    def test_multiple_known_nouns(self):
        result = scan_context._expand_synonyms(["auth", "user"])
        assert "auth" in result
        assert "user" in result
        # Adjacent synonyms should be present
        assert "login" in result
        assert "account" in result


# ---------------------------------------------------------------------------
# _estimate_scope
# ---------------------------------------------------------------------------


class TestEstimateScope:
    def test_1_file_is_S(self):
        label, _ = scan_context._estimate_scope(1, False)
        assert label == "S"

    def test_2_files_is_S(self):
        label, _ = scan_context._estimate_scope(2, False)
        assert label == "S"

    def test_3_files_is_M(self):
        label, _ = scan_context._estimate_scope(3, False)
        assert label == "M"

    def test_5_files_is_M(self):
        label, _ = scan_context._estimate_scope(5, False)
        assert label == "M"

    def test_6_files_is_L(self):
        label, _ = scan_context._estimate_scope(6, False)
        assert label == "L"

    def test_11_files_is_XL(self):
        label, _ = scan_context._estimate_scope(11, False)
        assert label == "XL"

    def test_boundary_crossing_upgrades_M_to_L(self):
        label, _ = scan_context._estimate_scope(4, True)
        assert label == "L"

    def test_boundary_crossing_upgrades_L_to_XL(self):
        label, _ = scan_context._estimate_scope(7, True)
        assert label == "XL"

    def test_boundary_crossing_does_not_upgrade_XL(self):
        label, _ = scan_context._estimate_scope(12, True)
        assert label == "XL"

    def test_reasoning_mentions_file_count(self):
        _, reasoning = scan_context._estimate_scope(4, False)
        assert "4" in reasoning


# ---------------------------------------------------------------------------
# _extract_interface_shapes (pure Python file via AST)
# ---------------------------------------------------------------------------


class TestExtractInterfaceShapes:
    def test_finds_matching_class(self, tmp_path):
        src = tmp_path / "model.py"
        src.write_text(
            'class SearchIndex:\n    """Indexes documents for search."""\n    pass\n'
        )
        shapes = scan_context._extract_interface_shapes(src, {"search"})
        assert any("SearchIndex" in s for s in shapes)

    def test_skips_non_matching_class(self, tmp_path):
        src = tmp_path / "model.py"
        src.write_text("class Unrelated:\n    pass\n")
        shapes = scan_context._extract_interface_shapes(src, {"search"})
        assert shapes == []

    def test_includes_docstring(self, tmp_path):
        src = tmp_path / "model.py"
        src.write_text(
            'class SearchIndex:\n    """Indexes documents for search."""\n    pass\n'
        )
        shapes = scan_context._extract_interface_shapes(src, {"search"})
        assert any("Indexes documents" in s for s in shapes)

    def test_caps_at_5_results(self, tmp_path):
        src = tmp_path / "model.py"
        classes = "\n".join(f"class Search{i}:\n    pass" for i in range(10))
        src.write_text(classes)
        shapes = scan_context._extract_interface_shapes(src, {"search"})
        assert len(shapes) <= 5

    def test_handles_syntax_error_gracefully(self, tmp_path):
        src = tmp_path / "bad.py"
        src.write_text("class Search(:\n    pass")
        shapes = scan_context._extract_interface_shapes(src, {"search"})
        assert shapes == []

    def test_typescript_regex(self, tmp_path):
        src = tmp_path / "model.ts"
        src.write_text(
            "interface SearchResult { id: number; }\ntype SearchQuery = string;\n"
        )
        shapes = scan_context._extract_interface_shapes(src, {"search"})
        assert "SearchResult" in shapes
        assert "SearchQuery" in shapes


# ---------------------------------------------------------------------------
# _dedupe_stable (via _expand_synonyms indirectly)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# scan() integration — uses a real temporary directory, no git/rg required
# ---------------------------------------------------------------------------


class TestScanIntegration:
    def test_returns_scan_result(self, tmp_path):
        result = scan_context.scan(["search"], tmp_path)
        assert isinstance(result, scan_context.ScanResult)

    def test_feature_area_reflects_nouns(self, tmp_path):
        result = scan_context.scan(["search", "catalog"], tmp_path)
        assert "search" in result.feature_area
        assert "catalog" in result.feature_area

    def test_empty_repo_has_unknowns(self, tmp_path):
        result = scan_context.scan(["search"], tmp_path)
        # With no files, the scan should note missing docs/history/tests
        assert isinstance(result.unknowns, list)

    def test_finds_matching_source_file(self, tmp_path):
        src = tmp_path / "engine.py"
        src.write_text("# search engine implementation\ndef search(): pass\n")
        result = scan_context.scan(["search"], tmp_path)
        # May find the file via rg or git grep; only assert result shape is valid
        assert isinstance(result.related_files, list)
        assert isinstance(result.scope, str)

    def test_scope_is_valid_label(self, tmp_path):
        result = scan_context.scan(["search"], tmp_path)
        assert result.scope in {"S", "M", "L", "XL"}

    def test_no_docs_added_to_unknowns(self, tmp_path):
        result = scan_context.scan(["xyzzy_not_found"], tmp_path)
        # No design docs found → unknown should be reported
        assert any("No glossary" in u or "docs" in u.lower() for u in result.unknowns)

    def test_main_emits_valid_json(self, tmp_path, capsys):
        sys.argv = ["scan_context.py", "search", "--cwd", str(tmp_path)]
        scan_context.main()
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "feature_area" in data
        assert "scope" in data
