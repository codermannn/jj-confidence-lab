"""Pure semantic comparison, grouped by logical identity, not graph text."""

from dataclasses import asdict, dataclass

from jj_lab.vcs.models import RepositorySnapshot


@dataclass(frozen=True)
class Difference:
    category: str
    subject: str
    before: object
    after: object


def compare(before: RepositorySnapshot, after: RepositorySnapshot) -> tuple[Difference, ...]:
    return compare_dicts(asdict(before), asdict(after))


def compare_dicts(before: dict, after: dict) -> tuple[Difference, ...]:
    result = []
    old = {}
    new = {}
    for revision in before["revisions"]:
        old.setdefault(revision["change_id"], []).append(revision)
    for revision in after["revisions"]:
        new.setdefault(revision["change_id"], []).append(revision)
    rewritten_parents = {
        old[key][0]["commit_id"]: new[key][0]["commit_id"]
        for key in old.keys() & new.keys()
        if len(old[key]) == len(new[key]) == 1
        and old[key][0]["commit_id"] != new[key][0]["commit_id"]
    }
    for change in sorted(old.keys() | new.keys()):
        left, right = old.get(change, []), new.get(change, [])
        category = "CREATED" if not left else "REMOVED" if not right else "UNCHANGED"
        result.append(Difference(category, f"change {change}", bool(left), bool(right)))
        if left and right:
            for field in ("commit_id", "parents", "description", "conflict", "divergent"):
                a, b = [r[field] for r in left], [r[field] for r in right]
                if a != b:
                    category = (
                        "CONFLICT CHANGES" if field in {"conflict", "divergent"} else "CHANGED"
                    )
                    # Do not infer automatic rewriting solely from different commit hashes.
                    if (
                        field == "parents"
                        and len(left) == len(right) == 1
                        and tuple(rewritten_parents.get(p, p) for p in left[0]["parents"])
                        == tuple(right[0]["parents"])
                    ):
                        category = "AUTOMATICALLY REWRITTEN"
                    result.append(Difference(category, f"{change} {field}", a, b))
    for field in (
        "working_copy",
        "files",
        "bookmarks",
        "remote_refs",
        "git_head",
        "git_symbolic_head",
        "git_refs",
        "git_index",
        "git_in_progress",
    ):
        if before[field] != after[field]:
            category = "REMOTE CHANGES" if field == "remote_refs" else "CHANGED"
            result.append(Difference(category, field, before[field], after[field]))
    if before["remote_refs"] == after["remote_refs"]:
        result.append(
            Difference("UNCHANGED", "remote_refs", before["remote_refs"], after["remote_refs"])
        )
    return tuple(result)
