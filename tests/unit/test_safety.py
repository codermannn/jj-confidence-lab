from pathlib import Path

import pytest

from jj_lab.core.environment import LabError
from jj_lab.inspect.snapshot import filesystem
from jj_lab.repos.factory import destroy


def test_guard_rejects_escape_and_root(environment, tmp_path):
    for path in [tmp_path.parent / "outside", tmp_path / "..", tmp_path]:
        with pytest.raises(LabError):
            environment.guard(path)


def test_guard_resolves_symlink_escape(environment, tmp_path):
    (tmp_path / "escape").symlink_to(tmp_path.parent)
    with pytest.raises(LabError):
        environment.guard(tmp_path / "escape" / "outside")


def test_delete_requires_owned_subdirectory(runner, tmp_path):
    innocent = tmp_path / "innocent"
    innocent.mkdir()
    (innocent / "keep").write_text("safe")
    with pytest.raises(LabError):
        destroy(runner, innocent)
    assert (innocent / "keep").read_text() == "safe"


def test_process_environment_does_not_inherit_credentials(environment, monkeypatch):
    for name in [
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_CONFIG",
        "SSH_AUTH_SOCK",
        "GH_TOKEN",
        "JJ_CONFIG",
    ]:
        monkeypatch.setenv(name, "host-secret")
    env = environment.process("Bob")
    assert "host-secret" not in env.values()
    assert env["GIT_ALLOW_PROTOCOL"] == "file"
    assert env["GIT_CONFIG_GLOBAL"] == "/dev/null"
    assert Path(env["JJ_CONFIG"]).is_relative_to(environment.root)


def test_filesystem_does_not_follow_links(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    secret = tmp_path / "secret"
    secret.mkdir()
    (secret / "token").write_text("NEVER READ")
    (repo / "link").symlink_to(secret)
    (repo / ".git").mkdir()
    (repo / ".git" / "config").write_text("hidden")
    entries = filesystem(repo)
    assert len(entries) == 1
    assert entries[0].kind == "symlink"
    assert "NEVER READ" not in entries[0].content
