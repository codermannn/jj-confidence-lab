"""Exercise API lag without retrying PR mutations."""

from unittest.mock import Mock

import pytest

from jj_lab.core.environment import LabError
from jj_lab.forge.client import ForgejoAPIError
from jj_lab.forge.scenario import wait_published


def test_waits_for_nonempty_repo_and_expected_commit(monkeypatch):
    monkeypatch.setattr("jj_lab.forge.scenario.time.sleep", lambda _: None)
    api = Mock()
    api.request.side_effect = [
        {"empty": True},
        {"commit": {"id": "old"}},
        {"empty": False},
        ForgejoAPIError(404, "missing branch"),
        {"empty": False},
        {"commit": {"id": "new"}},
    ]
    wait_published(api, "/repos/alice/lab-test", {"feature": "new"})
    assert api.request.call_count == 6
    assert all(c.args[0] == "GET" for c in api.request.call_args_list)


def test_auth_failure_is_not_retried():
    api = Mock()
    api.request.side_effect = ForgejoAPIError(403, "forbidden")
    with pytest.raises(ForgejoAPIError):
        wait_published(api, "/repos/alice/lab-test", {"feature": "new"})
    assert api.request.call_count == 1


def test_missing_branch_times_out(monkeypatch):
    monkeypatch.setattr("jj_lab.forge.scenario.time.monotonic", Mock(side_effect=[0, 21]))
    api = Mock()
    api.request.side_effect = ForgejoAPIError(404, "missing")
    with pytest.raises(LabError, match="20s"):
        wait_published(api, "/repos/alice/lab-test", {"feature": "new"})
