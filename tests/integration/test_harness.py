import json
import sys
from dataclasses import asdict

import pytest
from typer.testing import CliRunner

from jj_lab.cli import app
from jj_lab.core.environment import LabError
from jj_lab.inspect.compare import compare
from jj_lab.inspect.snapshot import snapshot
from jj_lab.scenarios.base import Scenario, execute


def test_runner_captures_expected_failure_and_raises_on_required_success(runner, environment):
    code = 'import sys; print("out"); print("err",file=sys.stderr); sys.exit(7)'
    r = runner.run(sys.executable, ["-c", code], environment.root, allow_failure=True)
    assert r.exit_code == 7 and r.stdout == "out\n" and r.stderr == "err\n"
    assert r.duration >= 0 and r.argv[1] == "-c"
    with pytest.raises(LabError, match="err"):
        r.require_success()
    assert len(runner.records) == 1


def test_factory_real_objects_and_serializable_state(topology):
    before = snapshot(topology)
    assert before.git_head == before.working_copy.parents[0]
    assert before.git_symbolic_head is None
    assert topology.bob.git("cat-file", "-t", "HEAD").stdout.strip() == "commit"
    topology.alice.write("weird\tname\n.txt", "arbitrary path\n")
    after = snapshot(topology)
    assert before.working_copy.change_id == after.working_copy.change_id
    assert before.working_copy.commit_id != after.working_copy.commit_id
    assert any(f.path == "weird\tname\n.txt" for f in after.files)
    assert any(d.subject.endswith("commit_id") for d in compare(before, after))
    assert json.loads(json.dumps(asdict(after)))["working_copy"]["change_id"]


def test_remote_override_is_refused_before_transport(topology):
    topology.alice.git("remote", "set-url", "origin", "https://example.test/not-a-lab")
    with pytest.raises(LabError, match="harness-created"):
        topology.alice.jj("git", "push", "--bookmark", "main")


def test_symlink_write_escape_is_refused(topology, tmp_path):
    (topology.alice.path / "escape").symlink_to(tmp_path.parent)
    with pytest.raises(LabError):
        topology.alice.write("escape/do-not-create", "bad")


def test_failing_scenario_retains_evidence(environment):
    def fail(c):
        c.alice.jj("not-a-command")

    s = Scenario(
        "failure",
        "deliberate failure",
        "test",
        "invalid jj command",
        "failure recorded",
        fail,
        lambda c, b, a: [],
    )
    result = execute(s, environment)
    assert result.status == "FAIL"
    assert (result.path / "commands.jsonl").is_file()
    assert "not-a-command" in (result.path / "summary.md").read_text()
    assert json.loads((result.path / "before.json").read_text())
    assert json.loads((result.path / "after.json").read_text()) is None


def test_cli_json_and_actionable_errors(environment, monkeypatch):
    monkeypatch.setenv("LAB_ROOT", str(environment.root))
    cli = CliRunner()
    missing = cli.invoke(app, ["state"])
    # main() owns error presentation; invoking app directly exposes typed domain errors.
    assert isinstance(missing.exception, LabError)
    result = cli.invoke(app, ["scenario", "run", "working-copy", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["status"] == "PASS"
    assert "\x1b" not in result.output
    assert cli.invoke(app, ["checkpoint", "save", "one"]).exit_code == 0
    assert cli.invoke(app, ["checkpoint", "save", "two"]).exit_code == 0
    assert cli.invoke(app, ["compare", "one", "two"]).exit_code == 0
    assert cli.invoke(app, ["xray"]).exit_code == 0


def test_missing_binary_still_records_fixture_failure(environment):
    from jj_lab.core.environment import Environment
    from jj_lab.scenarios.registry import scenarios

    isolated = Environment(environment.root, "/no-such-toolchain")
    run = execute(scenarios()[0], isolated)
    assert run.status == "FAIL"
    assert "No such file" in run.error
    commands = [json.loads(line) for line in (run.path / "commands.jsonl").read_text().splitlines()]
    assert commands[0]["exit_code"] == 127
    assert json.loads((run.path / "before.json").read_text()) is None


def test_hosted_remote_rejects_changed_push_url(topology):
    from jj_lab.forge.client import HostedRemote

    remote = HostedRemote(topology.alice, "lab-fixture")
    (topology.path / ".forgejo-origin").write_text(remote.url)
    topology.alice.git("remote", "add", "forgejo", remote.url)
    topology.alice.git("remote", "set-url", "--push", "forgejo", "https://example.test/foreign")
    with pytest.raises(LabError, match="remote changed"):
        remote.validate()
    with pytest.raises(LabError, match="registered local origin"):
        topology.alice.git("push", "forgejo", "main")


def test_checkpoint_inspection_does_not_pollute_action_exit_status(topology):
    from jj_lab.scenarios.base import Context

    runner = topology.alice.runner
    runner.phase = "operation"
    start = len(runner.records)
    Context(topology).capture("state")
    assert runner.phase == "operation"
    recorded = runner.records[start:]
    assert all(r.phase == "checkpoint:state" for r in recorded)
    # Detached symbolic-ref is a normal inspection exit, not a failed mutation.
    assert any(r.exit_code == 1 for r in recorded)
