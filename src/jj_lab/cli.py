"""Presentation and orchestration only; repository mutations live below this layer."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from jj_lab.core.command import CommandRunner
from jj_lab.core.doctor import PROJECT
from jj_lab.core.doctor import doctor as check_environment
from jj_lab.core.doctor import versions as tool_versions
from jj_lab.core.environment import Environment, LabError
from jj_lab.inspect.compare import compare_dicts
from jj_lab.inspect.snapshot import dump, human_views, snapshot
from jj_lab.repos.factory import create, destroy, reopen
from jj_lab.ui import render

app = typer.Typer(no_args_is_help=True, help="Disposable Git + Jujutsu laboratory")
scenario_app = typer.Typer(no_args_is_help=True)
conflict_app = typer.Typer(no_args_is_help=True)
evidence_app = typer.Typer(no_args_is_help=True)
checkpoint_app = typer.Typer(no_args_is_help=True)
behavior_app = typer.Typer(no_args_is_help=True)
forge_app = typer.Typer(no_args_is_help=True)
for name, child in [
    ("scenario", scenario_app),
    ("conflict", conflict_app),
    ("evidence", evidence_app),
    ("checkpoint", checkpoint_app),
    ("behavior", behavior_app),
    ("forge", forge_app),
]:
    app.add_typer(child, name=name)


def console() -> Console:
    return Console(no_color=bool(os.environ.get("NO_COLOR")), highlight=False)


def environment() -> Environment:
    return Environment.load()


def active():
    env = environment()
    marker = env.root / "active"
    if not marker.exists():
        raise LabError("No active repository. Run ./lab start.")
    return reopen(CommandRunner(env), Path(marker.read_text()))


def registry():
    from jj_lab.scenarios.registry import scenarios

    return {s.name: s for s in scenarios()}


def recent(name: str | None = None) -> Path:
    env = environment()
    base = env.guard(env.root / "artifacts" / "evidence")
    if name:
        base = env.guard(base / name)
    paths = sorted(
        base.glob("*/metadata.json") if name else base.glob("*/*/metadata.json"),
        key=lambda p: p.parent.name,
    )
    if not paths:
        raise LabError("No evidence yet. Run ./lab scenario run working-copy.")
    return paths[-1].parent


@app.command()
def versions():
    console().print_json(data=tool_versions(CommandRunner(environment())))


@app.command()
def doctor(verbose: bool = False):
    result = check_environment(environment())
    out = console()
    for name, value in result["versions"].items():
        out.print(f"✓ {name:8} {value}", style="green")
    for check in result["checks"]:
        out.print(f"✓ {check}", style="green")
    if verbose:
        out.print(f"LAB_ROOT={environment().root}; no inherited Git/jj configuration")


@app.command()
def start():
    console().print(Panel("jj-confidence-lab\nDisposable Git + Jujutsu laboratory"))
    doctor()
    env = environment()
    if not (env.root / "active").exists():
        reset(all_=False)
    console().print(
        "Nothing here touches your real repositories.\nTry: lab state · lab scenario list"
    )


@app.command()
def reset(all_: bool = typer.Option(False, "--all")):
    env = environment()
    runner = CommandRunner(env)
    if all_:
        runs = env.root / "runs"
        if runs.exists():
            for marker in sorted(runs.glob("*/*/.lab-owned")):
                destroy(runner, marker.parent)
    path = env.root / "interactive"
    if path.exists():
        destroy(runner, path)
    t = create(runner, path)
    (env.root / "active").write_text(str(t.path))
    console().print("✓ Disposable repositories reset. Evidence retained.", style="green")


@app.command()
def state():
    t = active()
    render.state(console(), snapshot(t), t.alice.jj("log", "-n", "8").stdout)


@app.command()
def graph():
    console().print(active().alice.jj("log", "-r", "all()").stdout, markup=False)


@app.command()
def xray():
    render.xray(console(), snapshot(active()))


@app.command()
def compare(
    a: Annotated[str | None, typer.Argument()] = None,
    b: Annotated[str | None, typer.Argument()] = None,
):
    if bool(a) != bool(b):
        raise LabError("Supply both checkpoint names or neither.")
    env = environment()
    paths = (
        [env.guard(env.root / "checkpoints" / f"{n}.json") for n in (a, b)]
        if a
        else [recent() / "before.json", recent() / "after.json"]
    )
    render.differences(console(), compare_dicts(*(json.loads(p.read_text()) for p in paths)))


@app.command()
def why():
    path = recent()
    meta = json.loads((path / "metadata.json").read_text())
    console().print(
        f"Operation: {meta['operation']}\nExpected invariant: {meta['invariant']}", markup=False
    )
    compare()
    checks = json.loads((path / "assertions.json").read_text())
    for check in checks:
        console().print(f"{'✓' if check['passed'] else '✗'} {check['name']}", markup=False)
    after = json.loads((path / "after.json").read_text())
    console().print(
        f"Git sees HEAD {after['git_head']} ({after['git_symbolic_head'] or 'detached/unborn'}).",
        markup=False,
    )
    console().print(f"Evidence: {path}")


@app.command("coworker-view")
def coworker_view():
    bob = active().bob
    bob.git("fetch", "origin")
    for args in [
        ("branch", "-avv"),
        ("log", "--graph", "--decorate", "--oneline", "--all"),
        ("ls-tree", "-r", "origin/main"),
    ]:
        console().print("$ git " + " ".join(args), style="dim")
        result = bob.git(*args, allow_failure=True)
        console().print(result.stdout + result.stderr, markup=False)


@scenario_app.command("list")
def scenario_list():
    table = Table("Category", "Experiment", "Purpose")
    for s in registry().values():
        table.add_row(s.category, s.name, s.summary)
    console().print(table)


@scenario_app.command("show")
def scenario_show(name: str):
    s = registry().get(name)
    if s is None:
        raise LabError(f"Unknown scenario {name}. Run lab scenario list.")
    console().print(
        Panel(
            f"{s.summary}\nOperation: {s.operation}\nInvariant: {s.invariant}\n"
            + "\n".join(s.sources),
            title=s.name,
        )
    )


@scenario_app.command("run")
def scenario_run(
    name: str,
    json_: bool = typer.Option(False, "--json"),
    verbose: bool = False,
    show_commands: bool = False,
):
    from jj_lab.scenarios.base import execute

    s = registry().get(name)
    if s is None:
        raise LabError(f"Unknown scenario {name}. Run lab scenario list.")
    run = execute(s, environment())
    if json_:
        typer.echo((run.path / "metadata.json").read_text())
    else:
        out = console()
        out.print(Panel(s.summary, title="Experiment: " + name))
        out.print("Fixture setup: local origin + Alice (jj), Bob and Carol (Git).", style="dim")
        if run.before:
            render.state(out, run.before)
        out.print("Operation under test", style="bold")
        for cmd in run.runner.records:
            if (
                verbose
                or cmd.phase == "operation"
                or (show_commands and cmd.phase not in {"fixture"})
            ):
                out.print(f"[{cmd.phase}] $ " + " ".join(cmd.argv), markup=False, style="dim")
        if run.after:
            render.state(out, run.after, run.after_views.get("jj log", ""))
        for check in run.context.checks:
            out.print(
                f"{'✓' if check.passed else '✗'} {check.name}",
                style="green" if check.passed else "red",
                markup=False,
            )
            if not check.passed:
                out.print(f"Expected: {check.expected}\nObserved: {check.actual}", markup=False)
        if run.error:
            out.print(run.error, style="red", markup=False)
        out.print(f"{run.status} · Evidence: {run.path}\nTry: lab compare · lab xray · lab why")
    if run.status != "PASS":
        raise typer.Exit(1)


@scenario_app.command("verify")
def verify():
    from jj_lab.scenarios.base import execute

    failures = []
    for s in registry().values():
        result = execute(s, environment())
        console().print(f"{result.status:4} {s.name} · {result.path}")
        if result.status != "PASS":
            failures.append(s.name)
    if failures:
        raise LabError("Failed experiments: " + ", ".join(failures))


@conflict_app.command("list")
@app.command("conflicts")
def conflicts():
    for s in registry().values():
        if s.category.startswith("conflict") or s.name == "divergent":
            console().print(f"{s.name:24} {s.summary}")


@conflict_app.command("run")
def conflict_run(name: str, json_: bool = typer.Option(False, "--json")):
    s = registry().get(name)
    if not s or not (s.category.startswith("conflict") or name == "divergent"):
        raise LabError("Choose a scenario from lab conflict list.")
    scenario_run(name, json_=json_, verbose=False, show_commands=False)


@conflict_app.command("inspect")
def conflict_inspect():
    t = active()
    render.xray(console(), snapshot(t))
    for name, value in human_views(t).items():
        if name in {"jj resolve --list", "jj status", "jj log"}:
            console().print(name, style="dim")
            console().print(value, markup=False)


@evidence_app.command("list")
def evidence_list():
    for path in sorted((environment().root / "artifacts" / "evidence").glob("*/*/metadata.json")):
        value = json.loads(path.read_text())
        console().print(f"{value['status']} {value['name']} {path.parent}")


@evidence_app.command("show")
def evidence_show(name: Annotated[str | None, typer.Argument()] = None):
    path = recent(name)
    console().print((path / "summary.md").read_text(), markup=False)
    console().print(f"Raw evidence: {path}")


@app.command()
def commands():
    console().print((recent() / "commands.jsonl").read_text(), markup=False)


@checkpoint_app.command("save")
def checkpoint_save(name: str):
    if not name.replace("-", "").replace("_", "").isalnum():
        raise LabError("Checkpoint names accept letters, numbers, - and _.")
    env = environment()
    path = env.guard(env.root / "checkpoints" / f"{name}.json")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(dump(snapshot(active())), indent=2))
    console().print(f"Saved {name}")


@checkpoint_app.command("list")
def checkpoint_list():
    for path in sorted((environment().root / "checkpoints").glob("*.json")):
        console().print(path.stem)


@behavior_app.command("report")
def behavior_report():
    from jj_lab.evidence.reporting import generate

    path = generate(environment())
    console().print(f"Generated reports: {path}")


@behavior_app.command("diff")
def behavior_diff(old: Path, new: Path):
    import difflib

    console().print(
        "".join(
            difflib.unified_diff(
                old.read_text().splitlines(True),
                new.read_text().splitlines(True),
                str(old),
                str(new),
            )
        ),
        markup=False,
    )


@forge_app.command("doctor")
def forge_doctor():
    from jj_lab.forge.client import Forgejo

    result = Forgejo(CommandRunner(environment())).doctor()
    console().print(f"✓ Forgejo {result['version']} · isolated Alice and Bob accounts")
    console().print("UI: http://localhost:3080 · Try: ./lab forge run")


@forge_app.command("run")
def forge_run(json_: bool = typer.Option(False, "--json")):
    from jj_lab.forge.scenario import scenario
    from jj_lab.scenarios.base import execute

    run = execute(scenario(), environment())
    if json_:
        typer.echo((run.path / "metadata.json").read_text())
    else:
        console().print(
            Panel("Local Forgejo: publish → PR → fetch → rebase → update → review → merge")
        )
        for assertion in run.context.checks:
            console().print(
                f"{'✓' if assertion.passed else '✗'} {assertion.name}",
                style="green" if assertion.passed else "red",
            )
            if not assertion.passed:
                console().print(f"Expected: {assertion.expected}\nActual: {assertion.actual}")
        if run.error:
            console().print(run.error, style="red", markup=False)
        console().print(f"{run.status} · Evidence: {run.path}")
        if url := run.context.observations.get("pr_url"):
            console().print(f"PR: {url}")
    if run.status != "PASS":
        raise typer.Exit(1)


@forge_app.command("status")
def forge_status():
    forge_doctor()
    evidence_show("forgejo-pr")


@app.command()
def check():
    commands = [
        ["uv", "run", "--locked", "ruff", "format", "--check", "."],
        ["uv", "run", "--locked", "ruff", "check", "."],
        ["shellcheck", "lab", "containers/forgejo-init.sh"],
        *[
            ["uv", "run", "--locked", "pytest", "-q", f"tests/{kind}"]
            for kind in ("unit", "integration", "scenarios")
        ],
    ]
    for argv in commands:
        console().print("$ " + " ".join(argv), style="dim")
        result = subprocess.run(argv, cwd=PROJECT, shell=False)
        if result.returncode:
            raise LabError("Quality gate failed: " + " ".join(argv))
    doctor()


def main():
    debug = "--debug" in sys.argv
    if debug:
        sys.argv.remove("--debug")
    try:
        app()
    except Exception as exc:
        if debug:
            raise
        Console(stderr=True).print(
            f"✗ {exc}\nUse --debug for a traceback.", style="red", markup=False
        )
        raise SystemExit(1) from None
