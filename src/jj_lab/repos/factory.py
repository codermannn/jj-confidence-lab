import shutil
from dataclasses import dataclass
from pathlib import Path

from jj_lab.core.command import CommandResult, CommandRunner
from jj_lab.core.environment import LabError
from jj_lab.vcs import adapters


@dataclass(frozen=True)
class Actor:
    name: str
    path: Path
    preferred_vcs: str
    runner: CommandRunner
    remote: Path

    @property
    def environment(self) -> dict[str, str]:
        return self.runner.environment.process(self.name)

    @property
    def email(self) -> str:
        return f"{self.name.lower()}@example.test"

    def git(self, *args: str, allow_failure: bool = False) -> CommandResult:
        if args and args[0] in {"fetch", "push", "pull"}:
            if len(args) < 2 or args[1] != "origin":
                raise LabError(
                    "Use the registered local origin; hosted transport has its own adapter."
                )
            adapters.validate_origin(self.runner, self.path, self.environment, self.remote)
            if any(":" in arg or "/" in arg for arg in args[1:] if not arg.startswith("refs/")):
                raise LabError("Transport accepts configured local origin only.")
        return adapters.git(
            self.runner, self.path, args, self.environment, allow_failure=allow_failure
        )

    def jj(self, *args: str, allow_failure: bool = False) -> CommandResult:
        if args[:2] in {("git", "fetch"), ("git", "push")}:
            adapters.validate_origin(self.runner, self.path, self.environment, self.remote)
            if "--remote" in args and args[args.index("--remote") + 1] != "origin":
                raise LabError("Only origin is allowed.")
        return adapters.jj(
            self.runner, self.path, args, self.environment, allow_failure=allow_failure
        )

    def file(self, name: str) -> Path:
        path = self.runner.environment.guard(self.path / name)
        if not path.is_relative_to(self.path) or any(
            p in {".git", ".jj"} for p in Path(name).parts
        ):
            raise LabError(f"Not a workspace content path: {name}")
        return path

    def write(self, name: str, content: str) -> None:
        path = self.file(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        self.runner.event("write", path, content)

    def remove(self, name: str) -> None:
        path = self.file(name)
        path.unlink()
        self.runner.event("remove", path)

    def rename(self, source: str, target: str) -> None:
        src, dst = self.file(source), self.file(target)
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        self.runner.event("rename", src, target)

    def symlink(self, name: str, target: str) -> None:
        path = self.file(name)
        self.file(target)  # Reject any escaping link target.
        path.symlink_to(target)
        self.runner.event("symlink", path, target)

    def revision(self, rev: str = "@", field: str = "commit_id") -> str:
        return self.jj("log", "--no-graph", "-r", rev, "-T", field).stdout.strip()

    def commit(self, message: str, files: dict[str, str]) -> str:
        for name, content in files.items():
            self.write(name, content)
        if self.preferred_vcs == "git":
            self.git("add", ".")
            self.git("commit", "-m", message)
            return self.git("rev-parse", "HEAD").stdout.strip()
        self.jj("describe", "-m", message)
        return self.revision(field="change_id")


@dataclass(frozen=True)
class Topology:
    path: Path
    remote: Path
    alice: Actor
    bob: Actor
    carol: Actor


def create(runner: CommandRunner, path: Path, *, empty: bool = False) -> Topology:
    path = runner.environment.guard(path)
    if path.exists():
        raise LabError(f"Fixture already exists: {path}; choose a new run or lab reset.")
    path.mkdir(parents=True)
    (path / ".lab-owned").write_text("jj-confidence-lab\n")
    remote = path / "origin.git"
    runner.run("git", ["init", "--bare", "--initial-branch=main", str(remote)], path)
    (remote / "lab-owned").write_text("jj-confidence-lab\n")
    bob = Actor("Bob", path / "bob", "git", runner, remote)
    runner.run("git", ["clone", str(remote), str(bob.path)], path, bob.environment)
    if not empty:
        bob.commit(
            "Seed main",
            {
                "app.conf": "mode=development\n",
                "other.txt": "base\n",
                "long.txt": "first=base\n" + "gap\n" * 20 + "last=base\n",
            },
        )
        bob.git("push", "origin", "main")
    alice = Actor("Alice", path / "alice", "jj", runner, remote)
    runner.run(
        "jj", ["git", "clone", "--colocate", str(remote), str(alice.path)], path, alice.environment
    )
    carol = Actor("Carol", path / "carol", "git", runner, remote)
    runner.run("git", ["clone", str(remote), str(carol.path)], path, carol.environment)
    return Topology(path, remote, alice, bob, carol)


def reopen(runner: CommandRunner, path: Path) -> Topology:
    path = runner.environment.guard(path)
    if not (path / ".lab-owned").is_file():
        raise LabError("No active fixture. Run lab start or lab scenario run working-copy.")
    remote = path / "origin.git"
    return Topology(
        path,
        remote,
        Actor("Alice", path / "alice", "jj", runner, remote),
        Actor("Bob", path / "bob", "git", runner, remote),
        Actor("Carol", path / "carol", "git", runner, remote),
    )


def destroy(runner: CommandRunner, path: Path) -> None:
    path = runner.environment.guard(path)
    if not (path / ".lab-owned").is_file():
        raise LabError(f"Refusing deletion without ownership marker: {path}")
    shutil.rmtree(path)
