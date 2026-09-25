from dataclasses import dataclass

from jj_lab.vcs.models import RepositorySnapshot, Revision


@dataclass(frozen=True)
class Assertion:
    name: str
    passed: bool
    expected: object
    actual: object


def equal(name: str, actual: object, expected: object) -> Assertion:
    return Assertion(name, actual == expected, expected, actual)


def same_change(before: Revision, after: Revision) -> Assertion:
    return equal("change ID remains stable", after.change_id, before.change_id)


def rewritten(before: Revision, after: Revision) -> Assertion:
    return equal("Git commit ID rewritten", after.commit_id != before.commit_id, True)


def parent(child: Revision, expected: str) -> Assertion:
    return equal("parent relationship", expected in child.parents, True)


def ancestor(state: RepositorySnapshot, older: str, newer: str) -> Assertion:
    graph = {r.commit_id: r.parents for r in state.revisions}
    pending, visited = [newer], set()
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        pending.extend(graph.get(current, ()))
    return equal("ancestor relationship", older in visited, True)


def change_exists(state: RepositorySnapshot, change: str) -> Assertion:
    return equal("change remains locatable", bool(state.by_change(change)), True)


def file_content(state: RepositorySnapshot, path: str, content: str) -> Assertion:
    actual = next((f.content for f in state.files if f.path == path), None)
    return equal(f"file {path}", actual, content)


def bookmark(state: RepositorySnapshot, name: str, target: str) -> Assertion:
    actual = next((b.added for b in state.bookmarks if b.name == name and b.remote is None), ())
    return equal(f"bookmark {name}", actual, (target,))


def remote_ref(state: RepositorySnapshot, name: str, target: str) -> Assertion:
    actual = next((r.target for r in state.remote_refs if r.name == name), None)
    return equal(f"remote ref {name}", actual, target)


def conflicted(revision: Revision, expected: bool = True) -> Assertion:
    return equal("file conflict state", revision.conflict, expected)


def operation_recorded(before: RepositorySnapshot, after: RepositorySnapshot) -> Assertion:
    return equal("operation recorded", before.operations[0].id != after.operations[0].id, True)


def detached(state: RepositorySnapshot) -> Assertion:
    return equal("Git HEAD detached", state.git_symbolic_head, None)
