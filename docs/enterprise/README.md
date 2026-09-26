# Enterprise workflows: one payment service, two tools

A workflow answers **who integrates what, into which line, after which checks**.
Git and jj manipulate history; neither replaces those decisions. This is a
survey of widely documented workflow families, not a measured popularity ranking
or a claim to enumerate every company's custom process. Sources checked in
September 2026 are linked beside the relevant policy.

## Start here

Follow Phase 2 first. Then run on the host:

```sh
# Refresh the pinned tools and open a disposable container shell.
make start
make shell
```

Inside that shell, follow [the Git lane](git.md), sections 0–6, one block at a
time. Open another `make shell` and follow [the jj lane](jj.md), sections 0–6.
Both use the same payment files, actors and sequence of business decisions.
Each lane creates its own sandbox with two local bare remotes. Nothing in
these blocks pushes the course repository or bypasses its protected main.
The endpoint named forgejo is a **local transport stand-in**, not the HTTP
server; [the hosted selective-push lab](../09-selective-push.md) supplies that
separate end-to-end PR exercise.

Read each lesson below before its corresponding command section. Predict the
result, run the block, inspect the graph, and answer the teach-back question.
The `test` commands fail if the promised result is false. No CI, approval,
release tag or real deployment is simulated by merely moving a bookmark.

## 1. Small changes: trunk-based development and GitHub Flow

**When:** a continuously delivered payment service with one current version.
Trunk-based development emphasizes frequent integration into one mainline,
often through very short branches and feature flags. GitHub Flow emphasizes
branch → PR → checks/review → merge. These can coexist; a PR branch that lives
for weeks is not made trunk-based merely by targeting main.

**Developer:** use lane section 1. Git starts a branch before the edit. jj starts
a change and attaches a bookmark when ready to publish. Both publish an ordinary
Git branch for the same review. A real flag needs application logic and tests;
our file only makes the disabled rollout state visible.

**Release engineer:** keep main releasable, test the integration revision,
then deploy a recorded artifact. Integrating a disabled feature is not enabling
it for customers. Keep flags owned and remove them after rollout.

**Tradeoff:** short feedback loops require reliable tests and small slices. jj
makes reshaping those slices easier; it does not make incomplete code safe.

**Teach back:** why can code merge before customers can use the feature?

Sources: [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow)
and [trunk-based development](https://trunkbaseddevelopment.com/).

## 2. Feature branches and stacked reviews

**When:** validation and receipts need independent reviews, but receipts depend
on validation. Long-lived feature branches isolate larger work at the cost of
integration delay. Stacked reviews split dependent work into smaller units;
they are a review technique, not a release policy.

**Developer:** lane section 2 creates two changes and rewrites the first. Git
explicitly rebases the child branch with `--onto`; jj rebases local descendants
as part of the parent rewrite. Inspect and repush every affected review branch.

**Reviewer:** create validation → main and receipt → validation PRs. Approve and
land the bottom review first. A rebase can invalidate review assumptions even
when the jj change ID remains stable. If the host squash-merges validation,
fetch and rebase only the remaining receipt work onto the new main, then retarget
its PR to main and rerun checks. Do not assume old and squashed ancestors have
the same identity. jj bookmarks do not automatically create or retarget PRs.

**Teach back:** why do two stacked changes differ from two versions of one change?

Source: [jj's GitHub workflow and stacked-change guidance](https://docs.jj-vcs.dev/latest/github/).

## 3. Release Flow: stable lines, hotfixes and backports

**When:** customers still run payment v1 while main develops v2. Cut a release
line late from a known revision; accept fixes rather than new features there.
A release train adds a schedule and admission cutoff to this policy.

**Developer:** lane section 3 deliberately puts unrelated next-version work
before a rounding fix. Git cherry-picks the fix onto the release base. jj
`duplicate --onto` creates a new change containing the patch on that base.
The assertions prove the unrelated feature stays out and the duplicate has a
new change identity. Dependencies can still make a backport conflict or fail
tests: selection by commit is not proof of compatibility.

**Release engineer:** reproduce and fix on main first where possible, then
backport and test each supported line. If an emergency can only be fixed on a
release line, explicitly assign the forward-port to main so the next release
does not reintroduce it. Open a backport PR targeting the release branch, record
its artifact and release version, and keep issued release tags fixed.

**Teach back:** why does a green main build not certify the backported build?

Source: [branch for release](https://trunkbaseddevelopment.com/branch-for-release/).

## 4. GitFlow: separate integration and release histories

**When:** an existing organization uses develop, stabilization branches, and
several supported versions with scheduled releases. GitFlow is not a default
recommendation for every enterprise; its author recommends simpler flows for
continuous delivery.

**Developer:** lane section 4 rehearses feature → develop → release. It starts
from the saved baseline in the same repository; `production` models GitFlow's
main so we do not overwrite the earlier lessons. Git uses explicit merge
commits; jj creates commits with multiple parents. Conflicts still require
resolution and testing.

**Release engineer:** integrate release fixes back into develop. A production
hotfix must reach production and develop (or the active release line when
appropriate). The executable lesson checks that both contain the security fix.
Hosted deployments would use protected PRs for these integration steps.

**Tradeoff:** this policy provides separate stabilization space, but every extra
long-lived line creates propagation obligations. jj reduces local editing
friction without removing them.

**Teach back:** what fails next month if today's hotfix only reaches production?

Source: [original GitFlow model and the author's later qualification](https://nvie.com/posts/a-successful-git-branching-model/).

## 5. Forking, upstream contribution and two destinations

**When:** contributors cannot write upstream, or you rehearse the same project
on local Forgejo before publishing to GitHub. Those are different permission
models even though both have two remotes.

**Developer:** lane section 5 publishes one contribution only to the second
remote and asserts origin has no such branch. For an actual fork, conventionally
name canonical read-only history `upstream` and your writable fork `origin`.
Fetch the canonical main, rebase explicitly, publish to the writable host, and
open a cross-repository PR. In the existing course setup GitHub is `origin` and
the rehearsal server is `forgejo`; the names themselves grant no permissions.

**Release engineer:** do not blindly track independently diverging main branches
as one local main. Select the authority and apply checks there. Rewriting local
ancestors affects local descendants, not both servers automatically.

**Teach back:** which explicit command updates the second remote?

Source: [jj multiple-remotes guidance](https://docs.jj-vcs.dev/latest/guides/multiple-remotes/).

## 6. GitLab Flow, environment branches and GitOps

**When:** integration and deployment need different schedules. GitLab Flow
combines feature review with environment or release lines according to the
team's delivery needs. If you use main → staging → production branches,
promote approved ancestry forward and reconcile drift; environment-specific
edits on source branches make clean promotion harder.

**Alternative:** lane section 6 uses environment directories on one line. It
copies a tested artifact identifier into production desired state, then creates
a forward revert. Git commits staged files; jj describes the current change.
Neither command executes a rollout. The sample identifier is deliberately fake,
and there is no Kubernetes reconciler or registry in this lab.

**Release engineer:** in real GitOps, a controller observes versioned desired
state and reconciles the environment. Promote the same immutable artifact,
record approvals and health checks, and roll back via an auditable desired-state
change. An artifact rollback cannot necessarily undo a database migration.
Do not move an issued release tag or use `jj op restore` to undo production.

**Teach back:** what additional system must act after the promotion commit merges?

Sources: [GitLab Flow](https://about.gitlab.com/topics/version-control/what-is-gitlab-flow/)
and [OpenGitOps principles](https://opengitops.dev/).

## 7. Merge policy: three different outcomes

This decision applies to every branch workflow above:

- **Merge commit:** retains feature commits and records integration with multiple
  parents. Git's `merge --no-ff` and jj's `new BASE TIP` are exercised in section 4.
- **Fast-forward:** moves the integration name to an existing descendant; adds
  no merge commit. Git `merge --ff-only` verifies ancestry. jj `bookmark set`
  simply selects a target, so inspect ancestry and respect server protection.
  The controlled descendant case is exercised in section 1.
- **Squash merge:** creates a new integrated commit containing the combined
  result. Local `jj squash` is an editing operation, not the server's PR merge
  button. A server squash need not preserve your original jj change identity.
- **Rebase-and-merge:** replays commits on the destination and may change their
  IDs. Fetch the result and reconcile dependent work; do not infer identity
  preservation from the host's label.

A bookmark publishes one tip plus ancestry. A change's obsolete versions are
not additional stacked commits that the server must merge. See the Phase 2
split/squash labs for local editing before applying a host merge policy.

## 8. Busy main: merge queues and merge trains

**When:** many PRs pass individually but fail when combined. After review,
a queue tests the proposed integration with main and earlier queued work.
A jj user publishes the same ordinary branch as a Git user and joins the same
host queue. Local automatic rebasing is not a merge queue.

**How:** configure required checks for queue-generated revisions and enable the
host's queue policy. GitHub Actions needs the following additional event;
this is a configuration example, not an enabled queue in this lab:

```yaml
# Test queued integration revisions as well as PRs.
on:
  pull_request:
  merge_group:
```

The jj CI action already verifies the event SHA; it must continue to test that
SHA rather than fetching a newer main. Queue availability depends on hosting
and account type. This personal GitHub repository does not claim queue coverage.
GitLab merge trains solve a similar integration problem with their own setup.

**Teach back:** why is a passing feature head weaker evidence than a passing
queued integration revision?

Source: [GitHub merge queue configuration and eligibility](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue).

## 9. Gerrit and other enterprise variations

Gerrit reviews changes through patch sets and special review refs, rather than
ordinary branch PRs alone. Its Change-Id footer and jj's internal change ID are
not interchangeable identifiers. Use Gerrit's configured submission policy and
jj's pinned Gerrit integration only in a Gerrit-specific rehearsal. This lab
has no Gerrit server, so no end-to-end Gerrit claim is made. Start with
[the Gerrit user guide](https://gerrit-review.googlesource.com/Documentation/intro-user.html).

A centralized direct-to-main workflow exists, but does not meet this repository's
protected-main policy. Monorepo versus many repositories is a separate layout
choice; ownership rules, path-filtered tests and cross-service release dependency
management still matter. Signing, regulated approvals, and segregation of duties
are also independent policies, not features jj silently provides.

## Verify the command lanes

```sh
# Run on the host after rebuilding; execute exactly the blocks printed in both guides.
docker compose run --rm -T --entrypoint python lab scripts/verify-enterprise.py
```

The verifier checks both lanes against the pinned runtime, including selective
refs, descendant ancestry, backport contents, hotfix propagation, and reverts.
The existing Forgejo experiment verifies real PR creation/rebase/review/merge.
Queue, Gerrit, deployment controller, and multi-environment governance examples
are researched guidance, not live integrations. This separation is the adoption
checklist: choose the policies you actually use and validate those host boundaries.
