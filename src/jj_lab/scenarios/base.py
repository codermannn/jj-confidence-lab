"""Explicit ARRANGE → ACT → OBSERVE → ASSERT → REPORT lifecycle."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from jj_lab.assertions.semantic import Assertion
from jj_lab.core.command import CommandRunner
from jj_lab.core.environment import Environment, LabError
from jj_lab.inspect.snapshot import human_views, snapshot
from jj_lab.repos.factory import Topology, create
from jj_lab.vcs.models import RepositorySnapshot


@dataclass
class Context:
    topology: Topology | None
    values: dict = field(default_factory=dict)
    observations: dict = field(default_factory=dict)
    checkpoints: dict[str, RepositorySnapshot] = field(default_factory=dict)
    checks: list[Assertion] = field(default_factory=list)

    @property
    def alice(self):
        if self.topology is None:
            raise LabError("Fixture has not been created.")
        return self.topology.alice

    @property
    def bob(self):
        if self.topology is None:
            raise LabError("Fixture has not been created.")
        return self.topology.bob

    def capture(self, name: str) -> RepositorySnapshot:
        if self.topology is None:
            raise LabError("Fixture has not been created.")
        runner = self.topology.alice.runner
        previous_phase = runner.phase
        runner.phase = f"checkpoint:{name}"
        try:
            state = snapshot(self.topology)
            self.checkpoints[name] = state
            return state
        finally:
            runner.phase = previous_phase


def nothing(context: Context) -> None:
    pass


@dataclass(frozen=True)
class Scenario:
    name: str
    summary: str
    category: str
    operation: str
    invariant: str
    act: Callable[[Context], None]
    assertions: Callable[[Context, RepositorySnapshot, RepositorySnapshot], list[Assertion]]
    arrange: Callable[[Context], None] = nothing
    observe: Callable[[Context], None] = nothing
    sources: tuple[str, ...] = ("https://docs.jj-vcs.dev/latest/cli-reference/",)
    tags: tuple[str, ...] = ()
    classification: str = "DOCUMENTED_AND_REPRODUCED"
    empty: bool = False


@dataclass
class Run:
    scenario: Scenario
    context: Context
    runner: CommandRunner
    path: Path
    before: RepositorySnapshot | None = None
    after: RepositorySnapshot | None = None
    before_views: dict = field(default_factory=dict)
    after_views: dict = field(default_factory=dict)
    status: str = "FAIL"
    error: str | None = None


def execute(scenario: Scenario, environment: Environment) -> Run:
    runner = CommandRunner(environment)
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    path = environment.guard(environment.root / "artifacts" / "evidence" / scenario.name / run_id)
    path.mkdir(parents=True)
    # Fixture creation failures also retain command records.
    run = Run(scenario, Context(None), runner, path)
    try:
        topology = create(
            runner, environment.root / "runs" / scenario.name / run_id, empty=scenario.empty
        )
        run.context = context = Context(topology)
        scenario.arrange(context)
        runner.phase = "before"
        run.before = snapshot(topology)
        run.before_views = human_views(topology)
        runner.phase = "operation"
        scenario.act(context)
        runner.phase = "observe"
        run.after = snapshot(topology)
        run.after_views = human_views(topology)
        action_results = [r for r in runner.records if r.phase == "operation"]
        context.observations.setdefault(
            "operation_succeeds", all(r.exit_code == 0 for r in action_results)
        )
        context.observations.setdefault(
            "operation_exit_codes", [r.exit_code for r in action_results]
        )
        context.observations.setdefault(
            "conflicted_revision_created", any(r.conflict for r in run.after.revisions)
        )
        context.observations.setdefault(
            "conflict_sides", sorted({f.sides for r in run.after.revisions for f in r.conflicts})
        )
        runner.phase = "probe"
        scenario.observe(context)
        runner.phase = "assert"
        context.checks.extend(scenario.assertions(context, run.before, run.after))
        if not context.checks:
            raise LabError("Scenario has no semantic assertions.")
        run.status = "PASS" if all(c.passed for c in context.checks) else "FAIL"
        (environment.root / "active").write_text(str(topology.path))
    except Exception as exc:
        run.error = f"{type(exc).__name__}: {exc}"
        run.status = "FAIL"
    finally:
        from jj_lab.evidence.recorder import record

        record(run)
    return run
