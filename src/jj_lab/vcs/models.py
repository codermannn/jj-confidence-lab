"""Immutable observations; a logical change is deliberately not a Git commit."""

from dataclasses import dataclass
from typing import NewType

ChangeId = NewType("ChangeId", str)
CommitId = NewType("CommitId", str)


@dataclass(frozen=True)
class Conflict:
    path: str
    sides: int


@dataclass(frozen=True)
class Revision:
    change_id: ChangeId
    commit_id: CommitId
    parents: tuple[CommitId, ...]
    description: str
    conflict: bool
    divergent: bool
    conflicts: tuple[Conflict, ...]


@dataclass(frozen=True)
class Bookmark:
    name: str
    remote: str | None
    added: tuple[CommitId, ...]
    removed: tuple[CommitId, ...]
    conflict: bool
    tracked: bool


@dataclass(frozen=True)
class GitRef:
    name: str
    target: CommitId


@dataclass(frozen=True)
class FileState:
    path: str
    kind: str
    content: str
    sha256: str


@dataclass(frozen=True)
class Operation:
    id: str
    parents: tuple[str, ...]
    description: str
    is_snapshot: bool
    started: str
    ended: str


@dataclass(frozen=True)
class RepositorySnapshot:
    working_copy: Revision
    revisions: tuple[Revision, ...]
    heads: tuple[CommitId, ...]
    bookmarks: tuple[Bookmark, ...]
    files: tuple[FileState, ...]
    filesystem_changes: tuple[tuple[str, str], ...]
    git_head: str | None
    git_symbolic_head: str | None
    git_refs: tuple[GitRef, ...]
    git_index: str
    git_status: str
    remote_refs: tuple[GitRef, ...]
    operations: tuple[Operation, ...]
    git_in_progress: tuple[str, ...]

    def by_change(self, change: str) -> tuple[Revision, ...]:
        return tuple(r for r in self.revisions if r.change_id == change)
