from jj_lab.scenarios import conflicts, fundamentals, interoperability
from jj_lab.scenarios.base import Scenario


def scenarios() -> list[Scenario]:
    return fundamentals.scenarios() + interoperability.scenarios() + conflicts.scenarios()
