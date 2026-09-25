from pathlib import Path

from jj_lab.core.command import CommandResult, CommandRunner
from jj_lab.core.environment import LabError


def git(
    runner: CommandRunner,
    path: Path,
    args: tuple[str, ...],
    env: dict[str, str],
    *,
    allow_failure: bool = False,
) -> CommandResult:
    return runner.run("git", list(args), path, env, allow_failure=allow_failure)


def jj(
    runner: CommandRunner,
    path: Path,
    args: tuple[str, ...],
    env: dict[str, str],
    *,
    allow_failure: bool = False,
) -> CommandResult:
    return runner.run(
        "jj", ["--color=never", "--no-pager", *args], path, env, allow_failure=allow_failure
    )


def validate_origin(runner: CommandRunner, path: Path, env: dict[str, str], remote: Path) -> None:
    """Check both fetch and push URLs before every automated network-like operation."""
    for flag in ([], ["--push"]):
        result = git(runner, path, ("remote", "get-url", *flag, "--all", "origin"), env)
        urls = result.stdout.splitlines()
        if urls != [str(remote)] or runner.environment.guard(remote) != remote:
            raise LabError(f"Only the harness-created local origin is allowed: {urls}")
    if not (remote / "lab-owned").is_file():
        raise LabError("Remote is missing its lab ownership marker.")
