import importlib.metadata
import platform
import tomllib
from pathlib import Path

from packaging.markers import Marker

from jj_lab.core.command import CommandRunner
from jj_lab.core.environment import Environment, LabError
from jj_lab.inspect.snapshot import snapshot
from jj_lab.repos.factory import create, destroy

JJ_VERSION = "0.45.1"
PROJECT = Path(__file__).resolve().parents[3]


def versions(runner: CommandRunner) -> dict[str, str]:
    return {
        "jj": runner.run("jj", ["--version"], runner.environment.root).stdout.strip(),
        "git": runner.run("git", ["--version"], runner.environment.root).stdout.strip(),
        "Python": platform.python_version(),
        "uv": runner.run("uv", ["--version"], runner.environment.root).stdout.strip(),
        **{name: importlib.metadata.version(name) for name in ("typer", "rich", "pytest", "ruff")},
    }


def doctor(environment: Environment) -> dict:
    runner = CommandRunner(environment)
    found = versions(runner)
    if not found["jj"].startswith(f"jj {JJ_VERSION}"):
        raise LabError(f"Expected jj {JJ_VERSION}, got {found['jj']}. Rebuild with ./lab start.")
    if tuple(map(int, found["git"].split()[2].split(".")[:2])) < (2, 41):
        raise LabError("Git >=2.41 required. Rebuild with ./lab start.")
    if found["Python"] != "3.13.12" or not found["uv"].startswith("uv 0.11.3 "):
        raise LabError("Python/uv differs from pin. Rebuild with ./lab start.")
    lock = tomllib.loads((PROJECT / "uv.lock").read_text())
    packages = {package["name"]: package for package in lock["package"]}
    root_package = packages["jj-confidence-lab"]
    pending = [*root_package["dependencies"], *root_package["dev-dependencies"]["dev"]]
    checked = set()
    while pending:
        edge = pending.pop()
        if edge.get("marker") and not Marker(edge["marker"]).evaluate():
            continue
        name = edge["name"]
        if name in checked:
            continue
        checked.add(name)
        package = packages[name]
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            raise LabError(f"Missing locked dependency {name}. Run uv sync --locked.") from None
        if actual != package["version"]:
            raise LabError(f"Lock mismatch: {name}. Run uv sync --locked.")
        pending.extend(package.get("dependencies", []))
    import tempfile

    # mkdir is reserved by mkdtemp, while factory owns creation of its child.
    parent = Path(tempfile.mkdtemp(prefix="doctor-", dir=environment.root))
    try:
        t = create(runner, parent / "fixture")
        observed = snapshot(t)
        if not (t.alice.path / ".git").is_dir() or not (t.alice.path / ".jj").is_dir():
            raise LabError("Colocation failed. Inspect jj git clone diagnostics.")
        if observed.git_head != observed.working_copy.parents[0]:
            raise LabError("Unexpected automatic Git HEAD mapping. Review pinned jj behavior.")
        evidence = environment.guard(environment.root / "artifacts")
        evidence.mkdir(exist_ok=True)
        probe = evidence / ".doctor"
        probe.write_text("writable")
        probe.unlink()
        destroy(runner, t.path)
    finally:
        if not list(parent.iterdir()):
            parent.rmdir()
    return {
        "versions": found,
        "checks": [
            "locked dependencies",
            "isolated Git/jj config",
            "writable lab root",
            "local bare origin",
            "Git clone",
            "colocated jj clone",
            "automatic Git HEAD mapping",
            "evidence directory",
        ],
    }
