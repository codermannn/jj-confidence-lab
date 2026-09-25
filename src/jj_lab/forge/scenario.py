"""A real PR lifecycle on the optional local Forgejo service."""

import time

from jj_lab.assertions import semantic as check
from jj_lab.core.environment import LabError
from jj_lab.forge.client import WEB_URL, Forgejo, ForgejoAPIError, HostedRemote
from jj_lab.scenarios.base import Context, Scenario


def arrange(c: Context):
    a, b = c.alice, c.bob
    api = Forgejo(a.runner)
    c.observations["forgejo_version"] = api.doctor()["version"]
    name = "lab-" + c.topology.path.name.lower().replace(".", "-")
    api.request(
        "POST",
        "/user/repos",
        {
            "name": name,
            "private": False,
            "auto_init": False,
            "description": "Disposable jj-confidence-lab experiment",
        },
    )
    remote = HostedRemote(a, name)
    (c.topology.path / ".forgejo-origin").write_text(remote.url)
    for actor in (a, b):
        actor.git("remote", "add", "forgejo", remote.url)
    # Bob gets write access to this disposable repository, never a real external account.
    api.request("PUT", f"/repos/alice/{name}/collaborators/bob", {"permission": "write"})
    remote.git("push", "main")
    remote.jj("fetch")
    c.values.update(api=api, name=name, alice_remote=remote, bob_remote=HostedRemote(b, name))
    c.values["change"] = a.commit("Payment validation", {"payment.txt": "validation added\n"})


def wait_pr(c: Context, *, head: str | None = None, mergeable: bool = False, merged: bool = False):
    route = f"/repos/alice/{c.values['name']}/pulls/{c.values['pr']}"
    deadline = time.monotonic() + 20
    while True:
        pr = c.values["api"].request("GET", route)
        if (
            (head is None or pr["head"]["sha"] == head)
            and (not mergeable or pr.get("mergeable"))
            and (not merged or pr.get("merged"))
        ):
            return pr
        if time.monotonic() >= deadline:
            raise LabError("Forgejo PR state did not converge in 20s. Raw API evidence retained.")
        time.sleep(0.25)


def lifecycle(c: Context):
    a, b = c.alice, c.bob
    api = c.values["api"]
    alice, bob = c.values["alice_remote"], c.values["bob_remote"]
    route = f"/repos/alice/{c.values['name']}"
    a.jj("bookmark", "create", "feature", "-r", "@")
    alice.jj("push", "--bookmark", "feature")
    published = c.capture("published")
    pr = api.request(
        "POST",
        route + "/pulls",
        {
            "base": "main",
            "head": "feature",
            "title": "Payment validation experiment",
            "body": "Local laboratory PR; disposable test data.",
        },
    )
    c.values["pr"] = pr["number"]
    c.observations["pr_url"] = f"{WEB_URL}/alice/{c.values['name']}/pulls/{pr['number']}"
    c.observations["pr_before"] = pr
    c.checks += [
        check.equal(
            "PR points at published jj commit", pr["head"]["sha"], published.working_copy.commit_id
        )
    ]
    b.commit("Urgent login fix", {"login.txt": "urgent fix\n"})
    bob.git("push", "main")
    remote_before = alice.refs()
    alice.jj("fetch")
    fetched = c.capture("fetched")
    c.checks += [
        check.equal(
            "fetch alone preserves feature ancestry",
            fetched.working_copy.parents,
            published.working_copy.parents,
        )
    ]
    a.jj("rebase", "-s", c.values["change"], "-d", "main@forgejo")
    rebased = c.capture("rebased")
    c.checks += [
        check.same_change(published.working_copy, rebased.working_copy),
        check.rewritten(published.working_copy, rebased.working_copy),
        check.parent(rebased.working_copy, remote_before["refs/heads/main"]),
    ]
    alice.jj("push", "--bookmark", "feature")
    updated = wait_pr(c, head=rebased.working_copy.commit_id, mergeable=True)
    c.observations["pr_after_rebase"] = updated
    c.checks += [
        check.equal("same PR updated", updated["number"], pr["number"]),
        check.equal(
            "PR head follows rewrite", updated["head"]["sha"], rebased.working_copy.commit_id
        ),
        check.equal(
            "Forgejo branch matches PR", alice.refs()["refs/heads/feature"], updated["head"]["sha"]
        ),
    ]
    review = api.request(
        "POST",
        route + f"/pulls/{pr['number']}/reviews",
        {
            "event": "APPROVED",
            "body": "Verified by disposable Bob actor.",
            "commit_id": rebased.working_copy.commit_id,
        },
        actor="bob",
    )
    c.observations["review"] = review
    c.checks.append(check.equal("Bob approval submitted", review["state"], "APPROVED"))
    if review["state"] != "APPROVED":
        raise LabError("Forgejo did not record an approved review; refusing to merge.")
    deadline = time.monotonic() + 20
    retries = 0
    while True:
        try:
            api.request(
                "POST",
                route + f"/pulls/{pr['number']}/merge",
                {
                    "Do": "merge",
                    "head_commit_id": rebased.working_copy.commit_id,
                    "delete_branch_after_merge": False,
                },
                actor="bob",
            )
            break
        except ForgejoAPIError as exc:
            # Upstream returns this exact 405 before mutation while checking mergeability.
            if (
                exc.status != 405
                or "Please try again later" not in exc.body
                or time.monotonic() >= deadline
            ):
                raise
            retries += 1
            time.sleep(0.25)
            wait_pr(c, head=rebased.working_copy.commit_id, mergeable=True)
    merged = wait_pr(c, merged=True)
    c.observations["merge_readiness_retries"] = retries
    c.observations["operation_succeeds"] = True
    c.observations["pr_merged"] = merged
    alice.jj("fetch")
    bob.git("fetch")
    c.observations["hosted_remote_refs"] = alice.refs()
    c.observations["bob_log"] = b.git("log", "--graph", "--oneline", "--all").stdout
    c.checks += [
        check.equal("PR merged", merged["merged"], True),
        check.equal(
            "Bob receives merged payment",
            b.git("show", "forgejo/main:payment.txt").stdout,
            "validation added\n",
        ),
        check.equal(
            "Bob receives urgent fix",
            b.git("show", "forgejo/main:login.txt").stdout,
            "urgent fix\n",
        ),
    ]
    c.observations["known_limitation"] = (
        "Forgejo models PR lifecycle, not GitHub-specific policy or UI."
    )


def scenario() -> Scenario:
    return Scenario(
        "forgejo-pr",
        "Publish, rebase, review and merge a real local PR",
        "interoperability.hosted",
        "jj git push; Forgejo PR; Bob push; jj fetch/rebase/push; review/merge; fetch",
        "A rewritten Git commit updates the same PR while retaining jj change identity",
        lifecycle,
        lambda c, b, a: [
            check.equal(
                "working change remains locatable", bool(a.by_change(c.values["change"])), True
            )
        ],
        arrange=arrange,
        sources=(
            "https://forgejo.org/docs/latest/user/api/usage/",
            "https://docs.jj-vcs.dev/latest/git-compatibility/",
        ),
        tags=("optional-forgejo",),
    )
