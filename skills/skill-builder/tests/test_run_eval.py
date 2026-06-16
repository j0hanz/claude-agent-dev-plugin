"""Tests for run_eval's error/non-trigger separation (fail-loud behavior).

The trigger detector spawns `claude -p` subprocesses, which cannot run in unit
tests, so run_single_query is monkeypatched. These tests pin the aggregation
contract: infrastructure failures (timeout/crash) must be counted as errors and
excluded from the trigger rate, never silently treated as "did not trigger".
"""

import asyncio
from pathlib import Path

import pytest

import scripts.run_eval as run_eval


def _run(eval_set, fake, **kwargs):
    """Invoke run_eval with _run_single_query_fn injected."""
    defaults = dict(
        skill_name="demo",
        description="desc",
        num_workers=4,
        timeout=5,
        project_root=Path("."),
        runs_per_query=3,
        trigger_threshold=0.5,
        _run_single_query_fn=fake,
    )
    defaults.update(kwargs)
    return asyncio.run(run_eval.run_eval(eval_set=eval_set, **defaults))


def test_all_runs_timeout_are_errors_not_nontriggers():
    async def fake(*args, **kwargs):
        return False, "timeout"

    out = _run([{"query": "q", "should_trigger": True}], fake)
    r = out["results"][0]
    assert r["errors"] == 3
    assert r["runs"] == 0  # no valid observations
    assert r["triggers"] == 0
    assert out["summary"]["errors"] == 3


def test_trigger_rate_computed_over_valid_runs_only():
    calls = {"n": 0}

    async def fake(*args, **kwargs):
        calls["n"] += 1
        # First two runs trigger cleanly; third crashes.
        if calls["n"] <= 2:
            return True, None
        return False, "exit:1"

    out = _run([{"query": "q", "should_trigger": True}], fake)
    r = out["results"][0]
    assert r["errors"] == 1
    assert r["runs"] == 2
    assert r["triggers"] == 2
    assert r["trigger_rate"] == pytest.approx(1.0)  # 2/2, not 2/3
    assert r["pass"] is True


def test_exceptions_counted_as_errors():
    async def fake(*args, **kwargs):
        raise RuntimeError("boom")

    out = _run([{"query": "q", "should_trigger": False}], fake)
    r = out["results"][0]
    assert r["errors"] == 3
    assert r["runs"] == 0


def test_clean_nontrigger_is_not_an_error():
    async def fake(*args, **kwargs):
        return False, None

    out = _run([{"query": "q", "should_trigger": True}], fake)
    r = out["results"][0]
    assert r["errors"] == 0
    assert r["runs"] == 3
    assert r["trigger_rate"] == pytest.approx(0.0)
    assert r["pass"] is False
