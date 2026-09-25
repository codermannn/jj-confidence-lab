import json
import re
from dataclasses import asdict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from jj_lab.inspect.compare import Difference
from jj_lab.vcs.models import RepositorySnapshot


def compact(value: object, limit: int = 160) -> str:
    text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
    text = re.sub(r"\b[0-9a-f]{40,128}\b", lambda m: m[0][:12], text)
    text = re.sub(r"\b[k-z]{32}\b", lambda m: m[0][:8], text)
    return text if len(text) <= limit else text[:limit] + "… (full value in JSON)"


def state(console: Console, s: RepositorySnapshot, graph: str = "") -> None:
    wc = s.working_copy
    console.print(
        Panel(
            f"change  {wc.change_id[:12]}\ncommit  {wc.commit_id[:12]}\n"
            f"parents {', '.join(p[:12] for p in wc.parents)}\n"
            f"conflicts {len(wc.conflicts)} · divergent {wc.divergent}\n"
            f"files   {compact(s.filesystem_changes)}",
            title="Working copy",
            border_style="cyan",
        )
    )
    console.print(
        "Bookmarks: " + compact([asdict(b) for b in s.bookmarks if b.remote != "git"], 350),
        markup=False,
    )
    if graph:
        console.print(graph, markup=False)


def xray(console: Console, s: RepositorySnapshot) -> None:
    lenses = [
        (
            "FILESYSTEM",
            "content scan (does not follow symlinks)",
            [(f.path, f"{f.kind}: {f.content}") for f in s.files],
        ),
        (
            "JUJUTSU",
            "jj status; jj log -T <JSON>; jj bookmark list --all-remotes -T <JSON>",
            [
                ("change", s.working_copy.change_id),
                ("commit", s.working_copy.commit_id),
                ("parents", s.working_copy.parents),
                ("conflicts", [asdict(c) for c in s.working_copy.conflicts]),
                ("bookmarks", [asdict(b) for b in s.bookmarks]),
            ],
        ),
        (
            "GIT",
            "git rev-parse HEAD; git symbolic-ref -q HEAD; git for-each-ref; git ls-files --stage",
            [
                ("HEAD", s.git_head),
                ("symbolic HEAD", s.git_symbolic_head or "detached/unborn"),
                ("refs", [asdict(r) for r in s.git_refs]),
                ("index", s.git_index.replace("\0", "\n")),
                ("in progress", s.git_in_progress),
            ],
        ),
        (
            "REMOTE",
            "git --git-dir <origin.git> for-each-ref",
            [(r.name, r.target) for r in s.remote_refs],
        ),
    ]
    for title, command, rows in lenses:
        table = Table(title=title, show_header=False, box=None)
        table.add_column(style="magenta" if title == "GIT" else "cyan")
        table.add_column()
        for key, value in rows:
            table.add_row(key, compact(value, 500))
        console.print(table)
        console.print(command, style="dim", markup=False)
    if any(r.conflict for r in s.revisions):
        console.print(
            "CAUTION: jj is authoritative for logical conflicts; "
            "Git trees/index are not a merge-resolution model.",
            style="yellow",
        )
    if s.git_in_progress:
        console.print(
            "CAUTION: unfinished Git operation detected; inspect raw Git evidence.", style="yellow"
        )


def differences(console: Console, changes: tuple[Difference, ...]) -> None:
    table = Table("Category", "Subject", "Before → After")
    for d in changes:
        if d.subject == "working_copy":
            continue  # Individual identity/parent rows already show this change.
        table.add_row(
            d.category, compact(d.subject), compact(d.before, 85) + " → " + compact(d.after, 85)
        )
    console.print(table)
