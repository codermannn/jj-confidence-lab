import os

import pytest

from jj_lab.core.command import CommandRunner
from jj_lab.core.environment import Environment
from jj_lab.repos.factory import create


@pytest.fixture
def environment(tmp_path):
    return Environment(tmp_path.resolve(), os.environ["PATH"])


@pytest.fixture
def runner(environment):
    return CommandRunner(environment)


@pytest.fixture
def topology(runner, environment):
    return create(runner, environment.root / "fixture")
