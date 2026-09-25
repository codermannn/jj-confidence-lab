import json

import pytest

from jj_lab.scenarios.base import execute
from jj_lab.scenarios.registry import scenarios


@pytest.mark.parametrize("scenario", scenarios(), ids=lambda s: s.name)
def test_real_scenario(scenario, environment):
    run = execute(scenario, environment)
    failed = [c for c in run.context.checks if not c.passed]
    assert run.status == "PASS", (
        f"{run.error}\n{failed}\nEvidence: {run.path}\n{run.after_views.get('jj log', '')}"
    )
    for name in [
        "metadata.json",
        "commands.jsonl",
        "before.json",
        "after.json",
        "before.txt",
        "after.txt",
        "compare.txt",
        "xray.txt",
        "assertions.json",
        "summary.md",
    ]:
        assert (run.path / name).is_file(), name
    assert json.loads((run.path / "metadata.json").read_text())["jj_version"].startswith(
        "jj 0.45.1"
    )
    assert run.context.checks
