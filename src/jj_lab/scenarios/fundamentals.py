from jj_lab.assertions import semantic as check
from jj_lab.inspect.snapshot import revisions
from jj_lab.repos.factory import Actor
from jj_lab.scenarios.base import Context, Scenario


def modify(c: Context):
    c.alice.write("app.conf", "mode=production\n")
    c.alice.jj("status")


def evolving(c: Context):
    modify(c)
    first = c.capture("first-edit")
    c.alice.write("app.conf", "mode=testing\n")
    c.alice.jj("status")
    second = c.capture("second-edit")
    c.checks += [
        check.same_change(first.working_copy, second.working_copy),
        check.rewritten(first.working_copy, second.working_copy),
    ]


def review_evolution(c: Context):
    """Model three review rounds of one logical change."""
    a = c.alice
    a.commit("payment validation", {"payment.txt": "draft\n"})
    first = c.capture("review-1")
    a.write("payment.txt", "draft\nvalidated\n")
    a.jj("status")
    second = c.capture("review-2")
    a.write("payment.txt", "draft\nvalidated\napproved\n")
    a.jj("status")
    third = c.capture("review-3")
    c.values["review_versions"] = [
        first.working_copy.commit_id,
        second.working_copy.commit_id,
        third.working_copy.commit_id,
    ]
    c.observations["review_versions"] = c.values["review_versions"]
    c.checks += [
        check.same_change(first.working_copy, second.working_copy),
        check.same_change(second.working_copy, third.working_copy),
        check.rewritten(first.working_copy, second.working_copy),
        check.rewritten(second.working_copy, third.working_copy),
        check.equal("three review versions recorded", len(set(c.values["review_versions"])), 3),
    ]


def new(c: Context):
    c.alice.jj("new", "-m", "child")


def edit_arrange(c: Context):
    c.values["target"] = c.alice.commit("payment", {"payment.txt": "unfinished\n"})
    c.alice.jj("new", "-m", "other")


def edit(c: Context):
    c.alice.jj("edit", c.values["target"])


def squash_arrange(c: Context):
    c.values["target"] = c.alice.commit("parent", {"parent.txt": "parent\n"})
    c.alice.jj("new", "-m", "child")
    c.alice.write("child.txt", "child\n")


def squash(c: Context):
    c.alice.jj("squash", "-m", "combined")


def split_arrange(c: Context):
    c.values["source"] = c.alice.commit(
        "payment feature",
        {"payment.txt": "amount=10\n", "receipt.txt": "pending\n"},
    )


def split(c: Context):
    c.alice.jj("split", "payment.txt", "-r", c.values["source"], "-m", "payment logic")


def absorb_arrange(c: Context):
    a = c.alice
    c.values["parent"] = a.commit(
        "payment validation",
        {"payment.txt": "amount=10\nstatus=pending\n"},
    )
    a.jj("new", "-m", "review correction")
    a.write("payment.txt", "amount=12\nstatus=pending\n")


def absorb(c: Context):
    c.alice.jj("absorb")


def diffedit_arrange(c: Context):
    c.values["target"] = c.alice.commit(
        "payment validation",
        {"payment.txt": "amount=10\nstatus=pending\n"},
    )


def diffedit(c: Context):
    # The pinned container has no interactive editor. A no-op diff editor still
    # exercises jj's diffedit boundary without pretending to edit via VS Code.
    tool_config = c.topology.path / "diffedit-tool.toml"
    tool_config.write_text(
        "[merge-tools.lab-noop]\n"
        'program = "true"\n'
        'edit-args = ["$left", "$right"]\n'
        'diff-args = ["$left", "$right"]\n'
    )
    c.alice.jj(
        "--config-file",
        str(tool_config),
        "diffedit",
        "--tool",
        "lab-noop",
        "-r",
        c.values["target"],
    )


def bisect_arrange(c: Context):
    a = c.alice
    c.values["good"] = a.commit("baseline", {"payment.txt": "validated\n"})
    for label, content in (
        ("formatting", "validated\nformatted\n"),
        ("regression", "validated\nformatted\nBUG\n"),
        ("follow-up", "validated\nformatted\nBUG\nfollow-up\n"),
    ):
        a.jj("new")
        c.values[label] = a.commit(label, {"payment.txt": content})
    c.values["bad"] = c.values["regression"]


def bisect(c: Context):
    result = c.alice.jj(
        "bisect",
        "run",
        "--range",
        "root()..@",
        "--",
        "sh",
        "-c",
        "! grep -q '^BUG$' payment.txt",
    )
    c.observations["bisect_output"] = result.stdout
    c.values["found"] = c.alice.revision(c.values["bad"], field="change_id")
    c.values["bisect_target"] = c.alice.jj("show", "-r", c.values["bad"]).stdout
    c.observations["bisect_target"] = c.values["bisect_target"]


def recover(c: Context):
    c.alice.jj("describe", "-m", "deliberate operation")
    c.capture("deliberate")
    c.alice.jj("undo")


def context_switch(c: Context):
    a = c.alice
    payment = a.commit("unfinished payment", {"payment.txt": "in progress\n"})
    payment_state = c.capture("payment")
    a.jj("new", "main", "-m", "urgent login")
    login = a.commit("urgent login", {"login.txt": "fixed\n"})
    urgent = c.capture("login")
    a.jj("edit", payment)
    c.values["payment"] = payment
    c.checks += [
        check.parent(urgent.working_copy, a.revision("main")),
        check.equal("independent logical changes", payment != login, True),
        check.equal(
            "payment Git object exists",
            a.git("cat-file", "-t", payment_state.working_copy.commit_id).stdout.strip(),
            "commit",
        ),
        check.equal("no Git stash", a.git("stash", "list").stdout, ""),
    ]


def stack(c: Context):
    a = c.alice
    ids = []
    for name in "ABC":
        if ids:
            a.jj("new")
        ids.append(a.commit(name, {name + ".txt": name + "\n"}))
    c.values["stack"] = ids


def rewrite_ancestor(c: Context):
    c.alice.jj("describe", "-r", c.values["stack"][0], "-m", "A rewritten")


def stack_assertions(c, before, after):
    result = []
    for identity in c.values["stack"]:
        old, current = before.by_change(identity)[0], after.by_change(identity)[0]
        result += [check.same_change(old, current), check.rewritten(old, current)]
    for parent_id, child_id in zip(c.values["stack"], c.values["stack"][1:], strict=False):
        result.append(
            check.parent(after.by_change(child_id)[0], after.by_change(parent_id)[0].commit_id)
        )
    return result


def workspace(c: Context):
    path = c.topology.path / "second-workspace"
    c.alice.jj("workspace", "add", str(path))
    second = Actor("Alice", path, "jj", c.alice.runner, c.alice.remote)
    second.write("agent.txt", "parallel workspace work\n")
    second.jj("status")
    c.observations["workspace_list"] = c.alice.jj("workspace", "list").stdout
    c.observations["second_workspace_status"] = second.jj("status").stdout
    c.checks += [
        check.equal("second workspace created", (path / ".jj").is_dir(), True),
        check.equal(
            "second workspace has independent files",
            (path / "agent.txt").read_text(),
            "parallel workspace work\n",
        ),
    ]


def scenarios() -> list[Scenario]:
    def s(name, summary, operation, invariant, act, assertions, **kwargs):
        return Scenario(
            name,
            summary,
            "fundamentals",
            operation,
            invariant,
            act,
            assertions,
            sources=("https://docs.jj-vcs.dev/latest/working-copy/",),
            **kwargs,
        )

    return [
        s(
            "empty-clone",
            "Inspect an empty colocated clone",
            "jj status; git rev-parse",
            "Both repositories exist and jj has a working-copy revision",
            lambda c: c.alice.jj("status"),
            lambda c, b, a: [
                check.equal(".jj exists", (c.alice.path / ".jj").is_dir(), True),
                check.equal(".git exists", (c.alice.path / ".git").is_dir(), True),
                check.equal(
                    "Git repository",
                    c.alice.git("rev-parse", "--is-inside-work-tree").stdout.strip(),
                    "true",
                ),
                check.equal("working-copy revision", bool(a.working_copy.change_id), True),
            ],
            empty=True,
        ),
        s(
            "working-copy",
            "Observe a file edit becoming a revision",
            "write app.conf; jj status",
            "Change ID stable; commit ID rewritten",
            modify,
            lambda c, b, a: [
                check.same_change(b.working_copy, a.working_copy),
                check.rewritten(b.working_copy, a.working_copy),
                check.file_content(a, "app.conf", "mode=production\n"),
            ],
        ),
        s(
            "evolving-change",
            "Snapshot two successive edits",
            "write; jj status; write; jj status",
            "Both snapshots preserve logical identity",
            evolving,
            lambda c, b, a: [check.same_change(b.working_copy, a.working_copy)],
        ),
        s(
            "review-evolution",
            "Record successive versions of one reviewable change",
            "edit; jj status; edit; jj status",
            "Each review version rewrites the commit but retains the change identity",
            review_evolution,
            lambda c, b, a: [
                check.file_content(a, "payment.txt", "draft\nvalidated\napproved\n"),
                check.same_change(b.working_copy, a.working_copy),
            ],
            tags=(
                "interdiff",
                "review",
            ),
        ),
        s(
            "new",
            "Create a child working-copy revision",
            "jj new -m child",
            "New change is a child of previous revision",
            new,
            lambda c, b, a: [
                check.parent(a.working_copy, b.working_copy.commit_id),
                check.equal(
                    "new logical identity",
                    a.working_copy.change_id != b.working_copy.change_id,
                    True,
                ),
            ],
        ),
        s(
            "new-vs-edit",
            "Edit an existing revision after creating a child",
            "jj edit <payment>",
            "Existing logical identity becomes working copy",
            edit,
            lambda c, b, a: [
                check.equal(
                    "existing identity selected", a.working_copy.change_id, c.values["target"]
                ),
                check.file_content(a, "payment.txt", "unfinished\n"),
            ],
            arrange=edit_arrange,
        ),
        s(
            "describe",
            "Rewrite description metadata",
            "jj describe -m named",
            "Same change, different commit",
            lambda c: c.alice.jj("describe", "-m", "named"),
            lambda c, b, a: [
                check.same_change(b.working_copy, a.working_copy),
                check.rewritten(b.working_copy, a.working_copy),
            ],
        ),
        s(
            "squash",
            "Move child content into its parent",
            "jj squash -m combined",
            "Parent change contains both files",
            squash,
            lambda c, b, a: [
                check.file_content(a, "parent.txt", "parent\n"),
                check.file_content(a, "child.txt", "child\n"),
                check.equal(
                    "parent rewritten",
                    b.by_change(c.values["target"])[0].commit_id
                    != a.by_change(c.values["target"])[0].commit_id,
                    True,
                ),
            ],
            arrange=squash_arrange,
        ),
        s(
            "split",
            "Separate one change into focused logical changes",
            "jj split payment.txt -r <change> -m payment logic",
            "Selected content moves to its own change and remaining content stays separate",
            split,
            lambda c, b, a: [
                check.equal(
                    "split created another revision", len(a.revisions), len(b.revisions) + 1
                ),
                check.file_content(a, "payment.txt", "amount=10\n"),
                check.file_content(a, "receipt.txt", "pending\n"),
            ],
            arrange=split_arrange,
            tags=(
                "stacking",
                "review",
            ),
        ),
        s(
            "diffedit",
            "Run a diff-editor boundary on a revision",
            "jj diffedit --tool lab-noop -r <change>",
            "Diffedit leaves the selected revision valid without opening a host editor",
            diffedit,
            lambda c, b, a: [
                check.change_exists(a, c.values["target"]),
                check.file_content(a, "payment.txt", "amount=10\nstatus=pending\n"),
            ],
            arrange=diffedit_arrange,
            tags=(
                "editor",
                "review",
            ),
        ),
        s(
            "absorb",
            "Move a focused follow-up into its ancestor change",
            "jj absorb",
            "The follow-up line is absorbed into the closest mutable ancestor",
            absorb,
            lambda c, b, a: [
                check.file_content(a, "payment.txt", "amount=12\nstatus=pending\n"),
                check.change_exists(a, c.values["parent"]),
            ],
            arrange=absorb_arrange,
            tags=(
                "stacking",
                "review",
            ),
        ),
        s(
            "bisect",
            "Find the first revision that introduces a regression",
            "jj bisect run --range root()..@ -- sh -c <test>",
            "Binary search identifies the known regression change",
            bisect,
            lambda c, b, a: [
                check.equal("first bad change found", c.values["found"], c.values["bad"]),
                check.equal(
                    "bad revision contains regression", "BUG" in c.values["bisect_target"], True
                ),
            ],
            arrange=bisect_arrange,
            tags=(
                "debugging",
                "history",
            ),
        ),
        s(
            "undo",
            "Recover an operation",
            "jj describe; jj undo",
            "Previous commit identity and content restored",
            recover,
            lambda c, b, a: [
                check.equal("commit restored", a.working_copy.commit_id, b.working_copy.commit_id),
                check.operation_recorded(b, a),
            ],
        ),
        s(
            "operation-history",
            "Inspect repository operation history",
            "jj describe; jj op log",
            "Mutation adds an operation with description",
            lambda c: c.alice.jj("describe", "-m", "operation"),
            lambda c, b, a: [
                check.operation_recorded(b, a),
                check.equal("operation description", bool(a.operations[0].description), True),
            ],
        ),
        s(
            "context-switch",
            "Preserve unfinished work across an urgent fix",
            "jj new main; jj edit <payment>",
            "Payment content survives independent work without stash",
            context_switch,
            lambda c, b, a: [
                check.change_exists(a, c.values["payment"]),
                check.file_content(a, "payment.txt", "in progress\n"),
                check.detached(a),
            ],
        ),
        s(
            "descendant-rewrite",
            "Rewrite the ancestor of a three-change stack",
            "jj describe -r A",
            "A, B, C retain change IDs and rewrite commit IDs and ancestry",
            rewrite_ancestor,
            stack_assertions,
            arrange=stack,
        ),
        s(
            "workspace",
            "Create another jj workspace",
            "jj workspace add",
            "Additional working copy shares history",
            workspace,
            lambda c, b, a: [
                check.equal("two working copies", len(revisions(c.alice, "working_copies()")), 2)
            ],
        ),
    ]
