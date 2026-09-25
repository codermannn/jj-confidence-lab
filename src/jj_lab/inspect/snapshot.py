import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path

from jj_lab.repos.factory import Actor, Topology
from jj_lab.vcs.models import (
    Bookmark,
    ChangeId,
    CommitId,
    Conflict,
    FileState,
    GitRef,
    Operation,
    RepositorySnapshot,
    Revision,
)

REVISION_TEMPLATE = (
    "'{\"revision\":' ++ json(self) ++ ',\"conflict\":' ++ json(conflict) "
    "++ ',\"divergent\":' ++ json(divergent) ++ ',\"files\":[' ++ "
    "conflicted_files.map(|f| '{\"path\":' ++ json(f.path()) ++ ',\"sides\":' "
    '++ json(f.conflict_side_count()) ++ \'}\').join(",") ++ "]}\\n"'
)
BOOKMARK_TEMPLATE = (
    "'{\"name\":' ++ json(name) ++ ',\"remote\":' ++ json(remote) "
    "++ ',\"added\":' ++ json(added_targets.map(|c| c.commit_id())) "
    "++ ',\"removed\":' ++ json(removed_targets.map(|c| c.commit_id())) "
    '++ \',"conflict":\' ++ json(conflict) ++ \',"tracked":\' ++ json(tracked) ++ "}\\n"'
)


def parse_revisions(output: str) -> tuple[Revision, ...]:
    revisions = []
    for line in output.splitlines():
        item = json.loads(line)
        rev = item["revision"]
        revisions.append(
            Revision(
                ChangeId(rev["change_id"]),
                CommitId(rev["commit_id"]),
                tuple(CommitId(p) for p in rev["parents"]),
                rev["description"],
                item["conflict"],
                item["divergent"],
                tuple(Conflict(**f) for f in item["files"]),
            )
        )
    return tuple(revisions)


def revisions(actor: Actor, revset: str) -> tuple[Revision, ...]:
    return parse_revisions(
        actor.jj("log", "--no-graph", "-r", revset, "-T", REVISION_TEMPLATE).stdout
    )


def refs(actor: Actor, remote: bool = False) -> tuple[GitRef, ...]:
    args = ("--git-dir", str(actor.remote)) if remote else ()
    raw = actor.git(*args, "for-each-ref", "--format=%(refname)%09%(objectname)").stdout
    return tuple(
        GitRef(name, CommitId(commit))
        for name, commit in (line.split("\t", 1) for line in raw.splitlines())
    )


def filesystem(path: Path) -> tuple[FileState, ...]:
    """Walk content only, never follow links or inspect .git/.jj internals."""
    entries = []
    for directory, dirs, files in os.walk(path, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in {".git", ".jj"})
        links = [d for d in dirs if (Path(directory) / d).is_symlink()]
        dirs[:] = [d for d in dirs if d not in links]
        for name in sorted(files + links):
            p = Path(directory) / name
            if name in {".git", ".jj"}:
                continue
            is_link = p.is_symlink()
            data = os.readlink(p).encode() if is_link else p.read_bytes()
            entries.append(
                FileState(
                    str(p.relative_to(path)),
                    "symlink" if is_link else "file",
                    data.decode(errors="replace"),
                    hashlib.sha256(data).hexdigest(),
                )
            )
    return tuple(sorted(entries, key=lambda f: f.path))


def snapshot(topology: Topology) -> RepositorySnapshot:
    a = topology.alice
    # Explicit snapshot/import boundary, then semantic reads on the integrated state.
    a.jj("status")
    wc = revisions(a, "@")[0]
    visible = revisions(a, "all()")
    bookmarks = tuple(
        Bookmark(
            v["name"],
            v["remote"],
            tuple(v["added"]),
            tuple(v["removed"]),
            v["conflict"],
            v["tracked"],
        )
        for v in (
            json.loads(line)
            for line in a.jj(
                "bookmark", "list", "--all-remotes", "-T", BOOKMARK_TEMPLATE
            ).stdout.splitlines()
        )
    )
    change_template = (
        'diff.files().map(|f| json(f.status()) ++ "\\t" ++ json(f.path()) ++ "\\n").join("")'
    )
    changes = tuple(
        tuple(json.loads(part) for part in line.split("\t"))
        for line in a.jj("log", "--no-graph", "-r", "@", "-T", change_template).stdout.splitlines()
    )
    ops = tuple(
        json.loads(line)
        for line in a.jj(
            "op", "log", "--no-graph", "-n", "8", "-T", 'json(self) ++ "\\n"'
        ).stdout.splitlines()
    )
    ops = tuple(
        Operation(
            o["id"],
            tuple(o["parents"]),
            o["description"],
            o["is_snapshot"],
            o["time"]["start"],
            o["time"]["end"],
        )
        for o in ops
    )
    head = a.git("rev-parse", "--verify", "HEAD", allow_failure=True)
    symbolic = a.git("symbolic-ref", "-q", "HEAD", allow_failure=True)
    return RepositorySnapshot(
        wc,
        visible,
        tuple(r.commit_id for r in revisions(a, "heads(all())")),
        bookmarks,
        filesystem(a.path),
        changes,
        head.stdout.strip() if head.exit_code == 0 else None,
        symbolic.stdout.strip() if symbolic.exit_code == 0 else None,
        refs(a),
        a.git("ls-files", "--stage", "-z").stdout,
        a.git("status", "--porcelain=v2", "-z").stdout,
        refs(a, remote=True),
        ops,
        tuple(
            name
            for name in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "rebase-merge", "rebase-apply")
            if (a.path / ".git" / name).exists()
        ),
    )


def human_views(topology: Topology) -> dict[str, str]:
    a = topology.alice
    commands = {
        "jj status": ("status",),
        "jj log": ("log", "-r", "all()"),
        "jj bookmark list": ("bookmark", "list", "--all-remotes"),
        "jj resolve --list": ("resolve", "--list"),
        "jj op log": ("op", "log", "-n", "6"),
    }
    views = {name: a.jj(*args, allow_failure=True).stdout for name, args in commands.items()}
    for args in [
        ("status",),
        ("log", "--graph", "--decorate", "--oneline", "--all"),
        ("diff",),
        ("diff", "--cached"),
    ]:
        r = a.git(*args, allow_failure=True)
        views["git " + " ".join(args)] = r.stdout + r.stderr
    return views


def dump(snapshot_value: RepositorySnapshot) -> dict:
    return asdict(snapshot_value)
