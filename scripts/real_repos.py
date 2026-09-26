"""Import pinned public histories into local Forgejo and rehearse jj workflows."""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib import error, request

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT / ".real-repos"
FORGEJO = "http://localhost:3080"
USER = "alice"
PASSWORD = "Lab-only-password-2026!"
AUTH = "Basic " + base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()


@dataclass(frozen=True)
class Repository:
    name: str
    source: str
    commit: str
    depth: int
    edit_file: str
    language: str

    @property
    def forgejo_name(self) -> str:
        return f"real-{self.name}"

    @property
    def local_url(self) -> str:
        return f"{FORGEJO}/{USER}/{self.forgejo_name}.git"


def repositories() -> dict[str, Repository]:
    data = tomllib.loads((PROJECT / "real-repos.toml").read_text())
    return {item["name"]: Repository(**item) for item in data["repository"]}


def run(*args: str, cwd: Path | None = None, capture: bool = False) -> str:
    result = subprocess.run(
        args,
        cwd=cwd or PROJECT,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else ""


def git(repo: Path, *args: str, capture: bool = False) -> str:
    return run(
        "git", "-c", f"http.extraHeader=Authorization: {AUTH}", *args, cwd=repo, capture=capture
    )


def jj(repo: Path, *args: str, capture: bool = False) -> str:
    relative = repo.resolve().relative_to(ROOT.resolve())
    command = (
        "docker",
        "compose",
        "run",
        "--rm",
        "-T",
        "-v",
        f"{ROOT}:/real",
        "-w",
        f"/real/{relative}",
        "--entrypoint",
        "jj",
        "lab",
        "--config",
        "user.name=Alice",
        "--config",
        "user.email=alice@example.test",
        *args,
    )
    return run(*command, capture=capture)


def api(method: str, path: str, body: dict | None = None) -> dict | None:
    api_request = request.Request(
        FORGEJO + "/api/v1" + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={"Authorization": AUTH, "Content-Type": "application/json"},
    )
    try:
        with request.urlopen(api_request, timeout=20) as response:
            content = response.read()
    except error.HTTPError as exc:
        if method == "POST" and exc.code == 409:
            return None
        raise RuntimeError(f"Forgejo {exc.code}: {exc.read().decode()}") from exc
    return json.loads(content) if content else None


def prepare_one(spec: Repository) -> dict:
    target = ROOT / spec.name
    if target.exists():
        remote = git(target, "remote", "get-url", "origin", capture=True)
        if remote != spec.local_url:
            raise RuntimeError(f"Refusing unexpected existing remote in {target}: {remote}")
        head = git(target, "rev-parse", "HEAD", capture=True)
        if head != spec.commit:
            raise RuntimeError(
                f"Refusing modified import {target}: expected {spec.commit}, got {head}"
            )
        print(f"REUSE {spec.name}: {target}")
        return inventory(spec, target)

    staging = ROOT / f".import-{spec.name}-{os.getpid()}"
    staging.mkdir(parents=True)
    try:
        run("git", "init", "--initial-branch=main", str(staging))
        # Fetch by immutable object ID. The source remote is never stored.
        fetch_args = ["git", "fetch", "--no-tags"]
        if spec.depth:
            fetch_args.extend(("--depth", str(spec.depth)))
        fetch_args.extend((spec.source, spec.commit))
        run(*fetch_args, cwd=staging)
        run("git", "switch", "-c", "main", "FETCH_HEAD", cwd=staging)
        actual = run("git", "rev-parse", "HEAD", cwd=staging, capture=True)
        if actual != spec.commit:
            raise RuntimeError(f"Pinned commit mismatch for {spec.name}: {actual}")

        api(
            "POST",
            "/user/repos",
            {
                "name": spec.forgejo_name,
                "private": False,
                "auto_init": False,
                "description": (
                    f"Local jj rehearsal of {spec.name}; imported from pinned public history"
                ),
            },
        )
        run("git", "remote", "add", "origin", spec.local_url, cwd=staging)
        git(staging, "push", "-u", "origin", "main")
        staging.rename(target)
        jj(target, "git", "init", "--colocate", ".")
        jj(target, "bookmark", "track", "main", "--remote", "origin")
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    record = inventory(spec, target)
    provenance = ROOT / "provenance"
    provenance.mkdir(exist_ok=True)
    (provenance / f"{spec.name}.json").write_text(
        json.dumps(
            {
                "source": spec.source,
                "pinned_commit": spec.commit,
                "local_remote": spec.local_url,
                "imported_at": int(time.time()),
            },
            indent=2,
        )
        + "\n"
    )
    print(f"IMPORTED {spec.name}: {target}")
    return record


def inventory(spec: Repository, target: Path) -> dict:
    return {
        "name": spec.name,
        "language": spec.language,
        "path": str(target),
        "head": git(target, "rev-parse", "HEAD", capture=True),
        "commits_available": int(git(target, "rev-list", "--count", "HEAD", capture=True)),
        "origin": git(target, "remote", "get-url", "origin", capture=True),
        "source_remote_present": spec.source in git(target, "remote", "-v", capture=True),
    }


def prepare(selected: list[Repository]) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    run("./lab", "forge", "start")
    report = [prepare_one(spec) for spec in selected]
    (ROOT / "inventory.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


def fresh_run(spec: Repository, scenario: str) -> Path:
    source = ROOT / spec.name
    if not source.exists():
        raise RuntimeError("Run `make real-prepare` first.")
    stamp = time.strftime("%Y%m%d-%H%M%S")
    target = ROOT / "runs" / f"{spec.name}-{scenario}-{stamp}"
    target.parent.mkdir(parents=True, exist_ok=True)
    git(PROJECT, "clone", spec.local_url, str(target))
    jj(target, "git", "init", "--colocate", ".")
    return target


def append(path: Path, text: str) -> None:
    with path.open("a") as stream:
        stream.write("\n" + text + "\n")


def stacked(spec: Repository) -> dict:
    repo = fresh_run(spec, "stacked")
    jj(repo, "new", "main", "-m", "docs: explain payment validation")
    append(repo / spec.edit_file, "jj lab: payment validation")
    jj(repo, "bookmark", "create", "validation", "-r", "@")
    jj(repo, "new", "-m", "docs: explain payment receipts")
    append(repo / spec.edit_file, "jj lab: payment receipts")
    jj(repo, "bookmark", "create", "receipt", "-r", "@")
    child_change = jj(repo, "log", "-r", "receipt", "--no-graph", "-T", "change_id", capture=True)
    child_before = jj(repo, "log", "-r", "receipt", "--no-graph", "-T", "commit_id", capture=True)
    jj(repo, "edit", "validation")
    append(repo / spec.edit_file, "jj lab: reject negative payments")
    jj(repo, "status")
    child_after = jj(repo, "log", "-r", "receipt", "--no-graph", "-T", "commit_id", capture=True)
    current_change = jj(repo, "log", "-r", "receipt", "--no-graph", "-T", "change_id", capture=True)
    parent = jj(repo, "log", "-r", "receipt-", "--no-graph", "-T", "commit_id", capture=True)
    validation = jj(repo, "log", "-r", "validation", "--no-graph", "-T", "commit_id", capture=True)
    assert child_before != child_after
    assert child_change == current_change
    assert parent == validation
    return {"scenario": "stacked", "path": str(repo), "child_rebased": True}


def megamerge(spec: Repository) -> dict:
    repo = fresh_run(spec, "megamerge")
    jj(repo, "new", "main", "-m", "experiment: linux payment path")
    (repo / "jj-lab-linux.txt").write_text("linux path\n")
    jj(repo, "bookmark", "create", "linux-path", "-r", "@")
    jj(repo, "new", "main", "-m", "experiment: windows payment path")
    (repo / "jj-lab-windows.txt").write_text("windows path\n")
    jj(repo, "bookmark", "create", "windows-path", "-r", "@")
    jj(repo, "new", "linux-path", "windows-path", "-m", "integration: test both paths")
    parents = jj(repo, "log", "-r", "@", "--no-graph", "-T", "parents.len()", capture=True)
    assert parents == "2"
    assert (repo / "jj-lab-linux.txt").is_file()
    assert (repo / "jj-lab-windows.txt").is_file()
    return {"scenario": "megamerge", "path": str(repo), "parents": 2}


def workspace(spec: Repository) -> dict:
    repo = fresh_run(spec, "workspace")
    second = repo.parent / (repo.name + "-agent-two")
    container_second = "/real/" + str(second.relative_to(ROOT))
    jj(
        repo,
        "workspace",
        "add",
        container_second,
        "-r",
        "main",
        "-m",
        "agent two investigation",
    )
    (second / "jj-lab-agent-two.txt").write_text("parallel investigation\n")
    jj(second, "status")
    assert not (repo / "jj-lab-agent-two.txt").exists()
    listing = jj(repo, "workspace", "list", capture=True)
    assert "agent-two" in listing
    return {"scenario": "workspace", "path": str(repo), "second_workspace": str(second)}


SCENARIOS = {"stacked": stacked, "megamerge": megamerge, "workspace": workspace}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "list", "run"))
    parser.add_argument("--repo", choices=tuple(repositories()) + ("all",), default="all")
    parser.add_argument("--scenario", choices=tuple(SCENARIOS) + ("all",), default="all")
    args = parser.parse_args()
    specs = repositories()
    selected = list(specs.values()) if args.repo == "all" else [specs[args.repo]]
    if args.command == "prepare":
        prepare(selected)
    elif args.command == "list":
        print((ROOT / "inventory.json").read_text() if (ROOT / "inventory.json").exists() else "[]")
    else:
        chosen = list(SCENARIOS) if args.scenario == "all" else [args.scenario]
        results = [SCENARIOS[name](spec) for spec in selected for name in chosen]
        (ROOT / "latest-results.json").write_text(json.dumps(results, indent=2) + "\n")
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError, AssertionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
