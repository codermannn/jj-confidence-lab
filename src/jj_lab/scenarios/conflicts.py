"""Conflict experiments: file conflicts, ref conflicts and divergence stay distinct."""

from jj_lab.assertions import semantic as check
from jj_lab.inspect.snapshot import revisions
from jj_lab.scenarios.base import Context, Scenario
from jj_lab.scenarios.interoperability import stale_arrange

KINDS = {
    "negative-control": "Independent files",
    "separate-hunks": "Independent hunks in one file",
    "identical-edit": "Identical concurrent edits",
    "text-same-line": "Same-line text conflict",
    "multiple-hunks": "Two separated conflict hunks",
    "multiple-files": "Conflicts in two files",
    "partial-resolution": "Resolve one hunk while another remains",
    "modify-delete": "Modify versus delete",
    "add-add": "Different additions at the same path",
    "rename-modify": "Rename versus modification",
    "rename-rename": "Different rename destinations",
    "file-directory": "File versus directory",
    "file-symlink": "File versus symlink",
    "stacked": "Conflict under a three-change stack",
    "unresolved-rebase": "Transform a still-conflicted change",
}
NEGATIVE = {"negative-control", "separate-hunks", "identical-edit"}
EXPLORATORY = {
    "modify-delete",
    "add-add",
    "rename-modify",
    "rename-rename",
    "file-directory",
    "file-symlink",
}


def side(c: Context, who: str, kind: str):
    a = c.alice
    value = "production" if who == "A" else "testing"
    if kind == "negative-control":
        a.write("app.conf" if who == "A" else "other.txt", value + "\n")
    elif kind == "identical-edit":
        a.write("app.conf", "mode=identical\n")
    elif kind == "separate-hunks":
        a.write(
            "long.txt",
            ("first=A\n" if who == "A" else "first=base\n")
            + "gap\n" * 20
            + ("last=B\n" if who == "B" else "last=base\n"),
        )
    elif kind in {"multiple-hunks", "partial-resolution"}:
        a.write("long.txt", f"first={value}\n" + "gap\n" * 20 + f"last={value}\n")
    elif kind == "modify-delete":
        if who == "B":
            a.remove("app.conf")
        else:
            a.write("app.conf", "mode=production\n")
    elif kind == "add-add":
        a.write("new.txt", value + "\n")
    elif kind in {"rename-modify", "rename-rename"}:
        if who == "A" or kind == "rename-rename":
            a.rename("app.conf", who + ".conf")
        else:
            a.write("app.conf", "mode=testing\n")
    elif kind == "file-directory":
        if who == "A":
            a.write("node", "file\n")
        else:
            a.write("node/child", "directory child\n")
    elif kind == "file-symlink":
        if who == "A":
            a.write("node", "file\n")
        else:
            a.symlink("node", "app.conf")
    else:
        a.write("app.conf", f"mode={value}\n")
        if kind == "multiple-files":
            a.write("other.txt", value + "\n")


def arrange(kind: str):
    def setup(c: Context):
        c.values["kind"] = kind
        a = c.alice
        side(c, "A", kind)
        a.jj("describe", "-m", "A")
        c.values["source"] = a.revision(field="change_id")
        c.values["stack"] = [c.values["source"]]
        if kind == "stacked":
            for label in ("B", "C"):
                a.jj("new")
                c.values["stack"].append(a.commit(label, {label + ".txt": label + "\n"}))
        c.values["tip"] = a.revision(field="change_id")
        a.jj("new", "main")
        side(c, "B", kind)
        a.jj("describe", "-m", "destination")
        c.values["destination"] = a.revision(field="change_id")
        a.jj("edit", c.values["tip"])

    return setup


def rebase(c: Context):
    r = c.alice.jj(
        "rebase", "-s", c.values["source"], "-d", c.values["destination"], allow_failure=True
    )
    c.observations.update(operation_succeeds=r.exit_code == 0, operation_exit_code=r.exit_code)
    c.checks.append(check.equal("rebase command completed", r.exit_code, 0))


def inspect_conflict(c: Context):
    a = c.alice
    state = c.capture("conflicted")
    conflicted = [r for r in state.revisions if r.conflict]
    c.observations.update(
        conflicted_revision_created=bool(conflicted),
        conflict_sides=sorted({f.sides for r in conflicted for f in r.conflicts}),
        can_postpone=None,
        can_transform_unresolved=None,
        resolve_applicable=None,
        manual_resolution_possible=None,
        descendants_affected=None,
        git_view_reliable=None,
        known_limitation="Git cannot interpret jj logical conflicts" if conflicted else "",
        conflicted_revisions=[r.commit_id for r in conflicted],
        materialization={f.path: f.content for f in state.files},
        resolve_list=a.jj("resolve", "--list", allow_failure=True).stdout,
    )
    if not conflicted:
        return
    c.observations["git_conflicted_object"] = a.git(
        "cat-file", "-p", conflicted[0].commit_id
    ).stdout
    c.observations["git_conflicted_tree"] = a.git("ls-tree", "-r", conflicted[0].commit_id).stdout
    c.checks.append(
        check.equal(
            "conflict encoded in jj-specific Git headers",
            "\njj:trees " in c.observations["git_conflicted_object"],
            True,
        )
    )
    # This field asks whether ordinary Git understands logical conflict semantics.
    c.observations["git_view_reliable"] = False
    source = c.values["source"]
    operation = state.operations[0].id

    def restore():
        a.jj("op", "restore", operation)

    # Probes are separately checkpointed; the primary after snapshot stays the rebase result.
    a.jj("new", "-m", "postponed")
    postponed = c.capture("postponed")
    c.observations["can_postpone"] = bool([r for r in postponed.revisions if r.conflict])
    restore()
    a.jj("new", c.values["destination"], "-m", "destination advances again")
    a.write("advance.txt", "new destination\n")
    destination = a.revision(field="change_id")
    result = a.jj("rebase", "-s", source, "-d", destination, allow_failure=True)
    transformed = c.capture("transformed-unresolved")
    c.observations["can_transform_unresolved"] = result.exit_code == 0
    c.observations["transformed_conflict_sides"] = sorted(
        {f.sides for r in transformed.revisions for f in r.conflicts}
    )
    if c.values.get("kind") == "unresolved-rebase":
        transformed_source = transformed.by_change(source)[0]
        c.checks += [
            check.conflicted(transformed_source),
            check.equal(
                "logical conflict retains two sides after rebase",
                [f.sides for f in transformed_source.conflicts],
                [2],
            ),
        ]
    restore()
    result = a.jj("resolve", "-r", source, "--tool", ":ours", allow_failure=True)
    resolved_tool = c.capture("tool-resolution")
    c.observations["resolve_exit_code"] = result.exit_code
    c.observations["resolve_message"] = result.stderr
    c.observations["resolve_applicable"] = (
        result.exit_code == 0 and not resolved_tool.by_change(source)[0].conflict
    )
    restore()
    a.jj("edit", source)
    targets = revisions(a, "@")[0].conflicts
    for conflict in targets:
        p = a.path / conflict.path
        if p.is_dir() or p.is_symlink():
            c.observations["known_limitation"] += (
                "; manual path resolution requires an explicit tree choice"
            )
            continue
        a.write(conflict.path, "resolved by manual edit\n")
    manual = c.capture("manual-resolution")
    c.observations["manual_resolution_possible"] = not manual.by_change(source)[0].conflict
    descendants = c.values.get("stack", [source])[1:]
    c.observations["descendants_affected"] = any(
        state.by_change(identity)[0].commit_id != manual.by_change(identity)[0].commit_id
        for identity in descendants
    )
    if descendants:
        c.checks += [
            check.equal(
                "ancestor resolution clears descendant conflicts",
                any(manual.by_change(i)[0].conflict for i in descendants),
                False,
            )
        ]
        for identity in descendants:
            c.checks += [
                check.same_change(state.by_change(identity)[0], manual.by_change(identity)[0]),
                check.rewritten(state.by_change(identity)[0], manual.by_change(identity)[0]),
            ]
    restore()
    a.jj("describe", "-r", source, "-m", "undo probe")
    a.jj("undo")
    undo = c.capture("undo-probe")
    c.observations["undo_preserves_conflict"] = undo.by_change(source)[0].conflict
    c.checks.append(
        check.equal(
            "undo restores conflicted source",
            undo.by_change(source)[0].commit_id,
            state.by_change(source)[0].commit_id,
        )
    )
    restore()


def partial(c: Context):
    inspect_conflict(c)
    a = c.alice
    a.jj("edit", c.values["source"])
    content = (a.path / "long.txt").read_text()
    lines = content.splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if line.startswith("<<<<<<<"))
    end = next(i for i, line in enumerate(lines[start:], start) if line.startswith(">>>>>>>"))
    a.write("long.txt", "".join(lines[:start]) + "first=resolved\n" + "".join(lines[end + 1 :]))
    state = c.capture("partial-resolution")
    c.observations["partial_resolution_remains_conflicted"] = state.working_copy.conflict
    c.checks += [
        check.conflicted(state.working_copy),
        check.equal(
            "resolved hunk retained",
            (a.path / "long.txt").read_text().startswith("first=resolved\n"),
            True,
        ),
    ]

    a.jj("op", "restore", c.checkpoints["conflicted"].operations[0].id)


def many_arrange(c: Context):
    a = c.alice
    sides = []
    for i in range(3):
        a.jj("new", "main")
        sides.append(a.commit(f"side {i}", {"app.conf": f"mode=side-{i}\n"}))
    c.values["sides"] = sides


def many(c: Context):
    r = c.alice.jj("new", *c.values["sides"], "-m", "three-sided merge")
    c.values["source"] = c.alice.revision(field="change_id")
    c.values["destination"] = c.values["sides"][0]
    c.observations.update(operation_succeeds=r.exit_code == 0, operation_exit_code=r.exit_code)


def bookmark_fetch(c: Context):
    r = c.alice.jj("git", "fetch")
    c.observations.update(operation_succeeds=r.exit_code == 0, operation_exit_code=r.exit_code)


def bookmark_observe(c: Context):
    a = c.alice
    state = c.capture("bookmark-conflicted")
    result = a.jj("git", "push", "--bookmark", "main", allow_failure=True)
    c.observations.update(
        bookmark_conflicted=any(b.conflict for b in state.bookmarks),
        conflicted_revision_created=any(r.conflict for r in state.revisions),
        conflict_sides=[],
        push_exit_code=result.exit_code,
        known_limitation="Reference conflict, not a file conflict",
    )
    c.checks += [check.equal("conflicted bookmark push rejected", result.exit_code != 0, True)]
    a.jj("bookmark", "set", "main", "-r", "@", "--allow-backwards")
    resolved = c.capture("bookmark-resolved")
    c.checks += [
        check.equal(
            "explicit target resolves bookmark", any(b.conflict for b in resolved.bookmarks), False
        )
    ]
    c.observations["resolution"] = (
        "jj bookmark set main -r @ --allow-backwards (explicit choice of local side)"
    )
    a.jj("op", "restore", state.operations[0].id)


def divergent_arrange(c: Context):
    a = c.alice
    a.commit("evolving", {"evolve.txt": "old\n"})
    c.values["old"] = a.revision()
    c.values["change"] = a.revision(field="change_id")
    a.write("evolve.txt", "new\n")
    a.jj("status")


def divergent(c: Context):
    r = c.alice.jj("new", c.values["old"], "-m", "revive predecessor")
    c.observations.update(operation_succeeds=r.exit_code == 0, operation_exit_code=r.exit_code)


def converge(c: Context):
    state = c.capture("divergent")
    result = c.alice.jj("converge", "--no-interactive", allow_failure=True)
    resolved = c.capture("converged")
    c.observations.update(
        converge_exit_code=result.exit_code,
        converge_message=result.stderr,
        visible_successors_before=len(state.by_change(c.values["change"])),
        visible_successors_after=len(resolved.by_change(c.values["change"])),
        known_limitation=(
            "Experimental converge heuristics; exit success alone does not prove convergence"
        ),
    )
    c.checks += [check.equal("fixture converges", len(resolved.by_change(c.values["change"])), 1)]
    c.alice.jj("op", "restore", state.operations[0].id)


def scenarios() -> list[Scenario]:
    result = []
    for name, summary in KINDS.items():

        def assertions(c, b, a, kind=name):
            source = a.by_change(c.values["source"])[0]
            checks = [
                check.same_change(b.by_change(c.values["source"])[0], source),
                check.parent(source, c.alice.revision(c.values["destination"])),
            ]
            if kind not in EXPLORATORY:
                checks.append(check.conflicted(source, kind not in NEGATIVE))
            return checks

        result.append(
            Scenario(
                name,
                summary,
                "conflicts.files",
                "jj rebase -s A -d destination",
                "Record logical conflicts separately from command exit status",
                rebase,
                assertions,
                arrange=arrange(name),
                observe=partial if name == "partial-resolution" else inspect_conflict,
                sources=(
                    "https://docs.jj-vcs.dev/latest/conflicts/",
                    "https://docs.jj-vcs.dev/latest/technical/conflicts/",
                ),
                classification="EXPLORATORY"
                if name in EXPLORATORY
                else "DOCUMENTED_AND_REPRODUCED",
            )
        )
    result += [
        Scenario(
            "many-sided",
            "Create a three-sided logical content conflict",
            "conflicts.files",
            "jj new side1 side2 side3",
            "Three logical conflict sides are observable",
            many,
            lambda c, b, a: [
                check.conflicted(a.working_copy),
                check.equal("three sides", a.working_copy.conflicts[0].sides, 3),
            ],
            arrange=many_arrange,
            observe=inspect_conflict,
            tags=("advanced",),
        ),
        Scenario(
            "bookmark",
            "Fetch incompatible local and remote bookmark movements",
            "conflicts.bookmarks",
            "jj git fetch",
            "Bookmark conflict differs from file conflict",
            bookmark_fetch,
            lambda c, b, a: [
                check.equal(
                    "main bookmark conflicted",
                    any(x.conflict for x in a.bookmarks if x.name == "main"),
                    True,
                ),
                check.conflicted(a.working_copy, False),
            ],
            arrange=stale_arrange,
            observe=bookmark_observe,
            sources=("https://docs.jj-vcs.dev/latest/bookmarks/",),
        ),
        Scenario(
            "divergent",
            "Revive an obsolete commit with the same change identity",
            "divergence",
            "jj new <hidden predecessor>; jj converge --no-interactive",
            "Multiple visible commit IDs share one change ID",
            divergent,
            lambda c, b, a: [
                check.equal("two visible successors", len(a.by_change(c.values["change"])), 2)
            ],
            arrange=divergent_arrange,
            observe=converge,
            sources=("https://docs.jj-vcs.dev/latest/guides/divergence/",),
            classification="VERSION_SENSITIVE",
        ),
    ]
    return result
