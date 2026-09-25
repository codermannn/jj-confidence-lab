import json
from dataclasses import FrozenInstanceError

import pytest

from jj_lab.evidence.recorder import normalized
from jj_lab.inspect.compare import compare_dicts
from jj_lab.inspect.snapshot import parse_revisions


def test_revision_parser_keeps_change_commit_and_conflict_sides_separate():
    rev = {
        "revision": {
            "change_id": "logical",
            "commit_id": "object",
            "parents": ["parent"],
            "description": 'message\nwith "quotes"',
        },
        "conflict": True,
        "divergent": False,
        "files": [{"path": "file\twith\nnewlines", "sides": 3}],
    }
    result = parse_revisions(json.dumps(rev))[0]
    assert result.change_id != result.commit_id
    assert result.parents == ("parent",)
    assert result.conflicts[0].sides == 3
    assert result.conflicts[0].path == "file\twith\nnewlines"
    with pytest.raises(FrozenInstanceError):
        result.description = "mutate"


def state(revisions):
    return dict(
        revisions=revisions,
        working_copy={},
        files=[],
        bookmarks=[],
        remote_refs=[],
        git_head=None,
        git_symbolic_head=None,
        git_refs=[],
        git_index="",
        git_in_progress=[],
    )


def test_compare_preserves_divergent_successors():
    a = dict(
        change_id="X",
        commit_id="a",
        parents=["root"],
        description="",
        conflict=False,
        divergent=False,
    )
    b = dict(a, commit_id="b", divergent=True)
    diff = compare_dicts(state([a]), state([dict(a, divergent=True), b]))
    change = next(d for d in diff if d.subject == "X commit_id")
    assert change.before == ["a"]
    assert change.after == ["a", "b"]
    assert any(d.category == "CONFLICT CHANGES" for d in diff)
    assert not any(d.category == "CREATED" for d in diff)


def test_normalization_preserves_raw_input():
    text = "/private/lab/" + "f" * 40 + " 2026-09-25T12:00:00Z"
    result = normalized(text, "/private/lab")
    assert "<LAB_ROOT>" in result and "<TIME>" in result
    assert "f" * 40 not in result
    assert "f" * 40 in text


def test_generated_baseline_retains_measured_values(environment):
    from jj_lab.evidence.reporting import generate
    from jj_lab.scenarios.registry import scenarios

    for s in scenarios():
        path = environment.root / "artifacts" / "evidence" / s.name / "run"
        path.mkdir(parents=True)
        (path / "metadata.json").write_text(
            json.dumps(
                {
                    "name": s.name,
                    "category": s.category,
                    "jj_version": "jj 0.45.1",
                    "status": "PASS",
                    "classification": s.classification,
                    "error": None,
                    "observations": {"operation_succeeds": True, "conflict_sides": [2]},
                }
            )
        )
        (path / "assertions.json").write_text("[]")
    directory = generate(environment)
    baseline = json.loads((directory / "baselines" / "jj-0.45.1" / "results.json").read_text())
    assert baseline[0]["observations"]["operation_succeeds"] is True
    assert baseline[0]["observations"]["conflict_sides"] == [2]


def test_forgejo_api_rejects_foreign_routes_before_io(runner):
    from jj_lab.core.environment import LabError
    from jj_lab.forge.client import Forgejo

    api = Forgejo(runner)
    for path in [
        "https://example.test",
        "//example.test",
        "/repos/real/project",
        "/repos/alice/lab-test/../../user",
    ]:
        with pytest.raises(LabError):
            api.request("GET", path)
    assert not runner.records
