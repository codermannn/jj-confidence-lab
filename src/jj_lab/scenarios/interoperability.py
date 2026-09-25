from jj_lab.assertions import semantic as check
from jj_lab.inspect.snapshot import revisions
from jj_lab.scenarios.base import Context, Scenario


def local_work(c: Context):
    c.values["local"] = c.alice.commit("local work", {"payment.txt": "pending\n"})


def fetch(c: Context):
    c.bob.commit("Bob advances main", {"bob.txt": "remote update\n"})
    c.bob.git("push", "origin", "main")
    c.capture("remote-before-fetch")
    c.alice.jj("git", "fetch")


def rebase_arrange(c: Context):
    local_work(c)
    fetch(c)


def rebase(c: Context):
    c.alice.jj("rebase", "-s", c.values["local"], "-d", "main")


def publish(c: Context):
    c.alice.jj("bookmark", "create", "feature", "-r", "@")
    c.alice.jj("git", "push", "--bookmark", "feature")
    c.bob.git("fetch", "origin")
    c.observations["bob_commit"] = c.bob.git("cat-file", "-p", "origin/feature").stdout
    c.checks += [
        check.equal(
            "Bob receives ordinary commit",
            c.bob.git("rev-parse", "origin/feature").stdout.strip(),
            c.alice.revision(),
        )
    ]


def stale_arrange(c: Context):
    c.alice.commit("Alice advances main", {"alice.txt": "local\n"})
    c.alice.jj("bookmark", "set", "main", "-r", "@")
    c.bob.commit("Bob advances main", {"bob.txt": "remote\n"})
    c.bob.git("push", "origin", "main")


def stale_push(c: Context):
    r = c.alice.jj("git", "push", "--bookmark", "main", allow_failure=True)
    c.observations.update(
        operation_succeeds=r.exit_code == 0,
        push_exit_code=r.exit_code,
        push_message=r.stderr,
        recovery="Fetch, inspect/resolve the bookmark targets, then explicitly push.",
    )
    c.checks += [check.equal("stale push rejected", r.exit_code != 0, True)]


def mixed(c: Context):
    c.alice.git("switch", "-c", "git-work")
    c.alice.write("git.txt", "ordinary git mutation\n")
    c.alice.git("add", "git.txt")
    c.alice.git("commit", "-m", "Git authored commit")
    c.values["git_commit"] = c.alice.git("rev-parse", "HEAD").stdout.strip()
    c.alice.jj("status")


def index(c: Context):
    c.alice.write("app.conf", "mode=staged\n")
    c.alice.git("add", "app.conf")
    c.observations["staged_before_jj"] = c.alice.git("diff", "--cached").stdout
    c.observations["index_before_jj"] = c.alice.git("ls-files", "--stage").stdout
    c.alice.write("app.conf", "mode=unstaged\n")
    c.observations["git_diff_before_jj"] = c.alice.git("diff").stdout
    c.alice.jj("status")
    c.observations["git_cached_after_jj"] = c.alice.git("diff", "--cached").stdout
    c.observations["jj_diff_after"] = c.alice.jj("diff").stdout
    c.observations["git_fsck"] = c.alice.git("fsck", allow_failure=True).stderr


def objects(c: Context):
    a = c.alice
    for stage in ("before", "after"):
        rev = revisions(a, "@")[0]
        c.observations[stage] = {
            "commit": rev.commit_id,
            "object": a.git("cat-file", "-p", rev.commit_id).stdout,
            "tree": a.git("ls-tree", "-r", rev.commit_id).stdout,
            "jj_show": a.jj("show", "-r", rev.commit_id).stdout,
        }
        if stage == "before":
            a.jj("describe", "-m", "rewritten object")


def pending_merge(c: Context):
    a = c.alice
    a.git("switch", "-c", "left", "main")
    a.write("app.conf", "mode=left\n")
    a.git("add", ".")
    a.git("commit", "-m", "left")
    a.git("switch", "-c", "right", "main")
    a.write("app.conf", "mode=right\n")
    a.git("add", ".")
    a.git("commit", "-m", "right")
    r = a.git("merge", "left", allow_failure=True)
    c.observations["git_merge_exit"] = r.exit_code
    c.observations["git_unmerged_index"] = a.git("ls-files", "--unmerged").stdout
    c.observations["merge_head_before_jj"] = (a.path / ".git" / "MERGE_HEAD").is_file()
    c.observations["known_limitation"] = (
        "jj import clears pending Git merge state in this fixture but snapshots Git conflict "
        "markers as ordinary content, without a jj logical conflict."
    )
    c.observations["jj_status"] = a.jj("status", allow_failure=True).stdout
    c.checks.append(check.equal("Git merge unresolved", r.exit_code != 0, True))


def scenarios() -> list[Scenario]:
    def s(name, summary, op, invariant, act, assertions, **kw):
        return Scenario(
            name,
            summary,
            "interoperability",
            op,
            invariant,
            act,
            assertions,
            sources=("https://docs.jj-vcs.dev/latest/git-compatibility/",),
            **kw,
        )

    return [
        s(
            "remote-update",
            "Fetch a Git coworker's update",
            "Bob commit/push; jj git fetch",
            "Fetch moves remote state without rebasing local work",
            fetch,
            lambda c, b, a: [
                check.equal(
                    "local ancestry unchanged", a.working_copy.parents, b.working_copy.parents
                ),
                check.equal("remote changed", a.remote_refs != b.remote_refs, True),
                check.equal(
                    "main moved",
                    next(x.added for x in a.bookmarks if x.name == "main" and x.remote is None)
                    != b.working_copy.parents,
                    True,
                ),
            ],
            arrange=local_work,
        ),
        s(
            "rebase",
            "Rebase local work onto fetched main",
            "jj rebase -s local -d main",
            "Logical identity persists while commit and parent change",
            rebase,
            lambda c, b, a: [
                check.same_change(b.working_copy, a.working_copy),
                check.rewritten(b.working_copy, a.working_copy),
                check.parent(a.working_copy, c.alice.revision("main")),
                check.equal("remote unchanged", a.remote_refs, b.remote_refs),
            ],
            arrange=rebase_arrange,
        ),
        s(
            "coworker",
            "Publish a bookmark to an ordinary Git clone",
            "jj bookmark create; jj git push; git fetch",
            "Local bookmark, Git branch, remote and Bob agree",
            publish,
            lambda c, b, a: [
                check.bookmark(a, "feature", a.working_copy.commit_id),
                check.remote_ref(a, "refs/heads/feature", a.working_copy.commit_id),
                check.equal(
                    "local Git ref",
                    next(r.target for r in a.git_refs if r.name == "refs/heads/feature"),
                    a.working_copy.commit_id,
                ),
            ],
            arrange=local_work,
        ),
        s(
            "push-safety",
            "Attempt a push against an unexpectedly moved remote",
            "jj git push --bookmark main",
            "Rejected push leaves remote unchanged",
            stale_push,
            lambda c, b, a: [
                check.equal("remote unchanged after rejection", a.remote_refs, b.remote_refs)
            ],
            arrange=stale_arrange,
        ),
        s(
            "mixed-mutation",
            "Import a real Git switch and commit",
            "git switch; git commit; jj status",
            "Git commit appears as parent of jj working copy",
            mixed,
            lambda c, b, a: [
                check.parent(a.working_copy, c.values["git_commit"]),
                check.operation_recorded(b, a),
                check.file_content(a, "git.txt", "ordinary git mutation\n"),
            ],
        ),
        s(
            "detached-head",
            "Inspect HEAD in an ordinary jj workspace",
            "git symbolic-ref; git rev-parse; jj status",
            "Git HEAD points at working-copy parent and is detached",
            lambda c: c.alice.jj("status"),
            lambda c, b, a: [
                check.detached(a),
                check.equal("HEAD is parent", a.git_head, a.working_copy.parents[0]),
            ],
        ),
        s(
            "git-index",
            "Observe staged and unstaged contents around jj snapshot",
            "git add; edit; jj status",
            "jj snapshots working filesystem, not staged contents",
            index,
            lambda c, b, a: [
                check.file_content(a, "app.conf", "mode=unstaged\n"),
                check.same_change(b.working_copy, a.working_copy),
                check.equal("staging was observed", bool(c.observations["staged_before_jj"]), True),
            ],
        ),
        s(
            "git-underneath",
            "Read jj revisions with Git object plumbing",
            "git cat-file; git ls-tree; jj describe",
            "Clean jj revisions are real Git commit objects",
            objects,
            lambda c, b, a: [
                check.same_change(b.working_copy, a.working_copy),
                check.rewritten(b.working_copy, a.working_copy),
                check.equal(
                    "object parent matches",
                    f"parent {a.working_copy.parents[0]}\n" in c.observations["after"]["object"],
                    True,
                ),
            ],
        ),
        s(
            "mixed-pending-merge",
            "Observe jj during an unfinished Git merge",
            "git merge; jj status",
            "Record pending Git state separately from jj conflict interpretation",
            pending_merge,
            lambda c, b, a: [
                check.equal(
                    "Git MERGE_HEAD cleared by import", "MERGE_HEAD" in a.git_in_progress, False
                ),
                check.conflicted(a.working_copy, False),
                check.equal(
                    "Git text markers remain ordinary content",
                    any("<<<<<<< HEAD" in f.content for f in a.files),
                    True,
                ),
            ],
            classification="VERSION_SENSITIVE",
        ),
    ]
