# Phase 1 report

## Toolchain

Verified on Linux amd64 under Docker Engine 29.7.2:

- jj **0.45.1**, commit `7c41cdeb16b6b321c64e789a966b6adf723816a5`; stable release checked against upstream on 2026-09-25.
- Git **2.47.3**, Python **3.13.12**, uv and bundled uv_build **0.11.3**.
- Typer **0.27.2**, Rich **14.3.4**, pytest **9.1.1**, Ruff **0.16.9**.
- Optional Forgejo **16.0.5** rootless; API string `16.0.5+gitea-1.22.0`.

Python/uv/Forgejo images use immutable OCI digests; jj archives are checksum-verified;
Debian packages come from a dated snapshot; Python dependencies use `uv.lock`.
The small FOSS toolchain supports typed subprocess orchestration, terminal output,
real-repository tests and offline execution after building the images.
Exact pins, sources and licenses: [verified versions](research/verified-versions.md)
and [decisions](research/decisions.md).

## Architecture

```text
./lab → OCI transport → Typer/Rich CLI
                         │
                   scenario lifecycle
                         │
          assertions ← semantic snapshots → evidence/reporting
                         │
              actor fixtures + Git/jj adapters
                         │
                   command runner
                         │
               real files, Git and jj

Optional hosted adapter → internal network → Forgejo API + Git HTTP
                                             └→ localhost PR UI
```

Immutable values distinguish change IDs, commit IDs, ancestry, local/remote
bookmarks, Git refs/index, file conflicts, reference conflicts, divergence and
operation history. The UI contains no repository mutation logic. Snapshots
explicitly integrate jj's working copy first. Conflict probes have separate
checkpoints and restore the primary after-state. Raw commands and failures
remain inspectable. The [architecture review](research/architecture-review.md)
records corrections and boundaries.

## Running it

```sh
# Start or rebuild the isolated lab and its services.
./lab start
./lab scenario list
./lab scenario run working-copy
./lab xray
./lab reset
./lab check
```

Optional real local PR workflow:

```sh
# Inspect or run the local Forgejo-backed workflow.
./lab forge start
./lab forge run
./lab forge stop
```

UI: [localhost:3080](http://localhost:3080). Disposable accounts: `alice` and `bob`,
password `Lab-only-password-2026!`. The base lab has no network; the hosted runner
has only an internal network. Forgejo also has a UI bridge for localhost publishing.
External integrations are disabled.

The actual container passed start, doctor and the aggregate quality check:
Ruff format/lint, ShellCheck, **10 unit + 9 integration + 44 scenario tests**.
The separate Forgejo end-to-end experiment also passed. GitHub Actions jobs are
provided for quality, harness, scenarios and Forgejo; hosted CI execution has not
been observed from this local workspace.

## Scenarios implemented

Statuses below come from the generated baseline. PASS means the fixture's explicit
assertions held; it does not promote exploratory results to universal behavior.
No required conflict experiment is represented by a fake skip.

| Scenario | Result | Finding classification |
|---|---|---|
| add-add | PASS | EXPLORATORY |
| bookmark | PASS | DOCUMENTED_AND_REPRODUCED |
| bisect | PASS | DOCUMENTED_AND_REPRODUCED |
| context-switch | PASS | DOCUMENTED_AND_REPRODUCED |
| coworker | PASS | DOCUMENTED_AND_REPRODUCED |
| descendant-rewrite | PASS | DOCUMENTED_AND_REPRODUCED |
| describe | PASS | DOCUMENTED_AND_REPRODUCED |
| detached-head | PASS | DOCUMENTED_AND_REPRODUCED |
| divergent | PASS | VERSION_SENSITIVE |
| diffedit | PASS | DOCUMENTED_AND_REPRODUCED |
| empty-clone | PASS | DOCUMENTED_AND_REPRODUCED |
| evolving-change | PASS | DOCUMENTED_AND_REPRODUCED |
| file-directory | PASS | EXPLORATORY |
| file-symlink | PASS | EXPLORATORY |
| forgejo-pr | PASS | DOCUMENTED_AND_REPRODUCED |
| git-index | PASS | DOCUMENTED_AND_REPRODUCED |
| git-underneath | PASS | DOCUMENTED_AND_REPRODUCED |
| identical-edit | PASS | DOCUMENTED_AND_REPRODUCED |
| many-sided | PASS | DOCUMENTED_AND_REPRODUCED |
| mixed-mutation | PASS | DOCUMENTED_AND_REPRODUCED |
| mixed-pending-merge | PASS | VERSION_SENSITIVE |
| modify-delete | PASS | EXPLORATORY |
| multiple-files | PASS | DOCUMENTED_AND_REPRODUCED |
| multiple-hunks | PASS | DOCUMENTED_AND_REPRODUCED |
| negative-control | PASS | DOCUMENTED_AND_REPRODUCED |
| new | PASS | DOCUMENTED_AND_REPRODUCED |
| new-vs-edit | PASS | DOCUMENTED_AND_REPRODUCED |
| operation-history | PASS | DOCUMENTED_AND_REPRODUCED |
| partial-resolution | PASS | DOCUMENTED_AND_REPRODUCED |
| push-safety | PASS | DOCUMENTED_AND_REPRODUCED |
| rebase | PASS | DOCUMENTED_AND_REPRODUCED |
| remote-update | PASS | DOCUMENTED_AND_REPRODUCED |
| review-evolution | PASS | DOCUMENTED_AND_REPRODUCED |
| rename-modify | PASS | EXPLORATORY |
| rename-rename | PASS | EXPLORATORY |
| separate-hunks | PASS | DOCUMENTED_AND_REPRODUCED |
| squash | PASS | DOCUMENTED_AND_REPRODUCED |
| stacked | PASS | DOCUMENTED_AND_REPRODUCED |
| text-same-line | PASS | DOCUMENTED_AND_REPRODUCED |
| undo | PASS | DOCUMENTED_AND_REPRODUCED |
| unresolved-rebase | PASS | DOCUMENTED_AND_REPRODUCED |
| working-copy | PASS | DOCUMENTED_AND_REPRODUCED |
| workspace | PASS | DOCUMENTED_AND_REPRODUCED |
| split | PASS | DOCUMENTED_AND_REPRODUCED |
| absorb | PASS | DOCUMENTED_AND_REPRODUCED |

## Jujutsu findings

- Successive working-copy snapshots retained change identity and rewrote Git commit identity.
- `new` created a child; `edit` selected an existing revision and restored its files.
- Unfinished payment work survived switching to independent login work without Git stash.
- Rewriting the ancestor of A → B → C retained each change identity while rewriting descendant commits and parent relationships.
- Three successive review checkpoints rewrote one payment commit while retaining its jj change identity, providing evidence for an interdiff-style review history.
- Undo recovered the earlier revision. Operation history recorded mutations separately from commit history.
- The revived predecessor fixture converged to one successor with `jj converge --no-interactive`; this remains version-sensitive.

Exact assertions and evidence: [findings](research/findings.md),
[invariants](research/invariants.md), [command contracts](research/command-contracts.md).

## Git interoperability findings

- Clean jj revisions were Git commit objects readable with `cat-file` and `ls-tree`.
- Ordinary colocated states had detached Git HEAD at the jj working-copy parent.
- Fetch observed Bob's update without rebasing Alice's ancestry; explicit rebase was a separate graph change.
- Publishing aligned the jj bookmark, local Git branch, bare remote and Bob's fetched commit.
- A stale incompatible push was rejected without altering the remote.
- jj imported an ordinary Git switch/commit. Staging did not define the subsequent jj snapshot's content.
- During the unfinished Git merge fixture, jj cleared `MERGE_HEAD` while retaining Git conflict markers as ordinary text, without a jj logical conflict.
- On Forgejo, rebasing and pushing updated the same PR's head; Bob approved and merged it, and his Git clone received both changes.

Verified local PR: [payment validation experiment](http://localhost:3080/alice/lab-20260925t132039-627828z/pulls/1).
Forgejo establishes this local PR lifecycle, not GitHub-specific guarantees.

## Conflict findings

The generated [behavior matrix](research/behavior-matrix.md) records command
success, logical conflict creation and sides, postponement, transformation,
built-in resolution, manual editing, descendants and evidence links.

Negative controls remained clean. Same-line, multi-hunk and multi-file edits
created logical conflicts after successful rebase. Partial resolution left the
remaining hunk conflicted. Ancestor resolution propagated through the tested stack.
Rebase of unresolved work retained a two-sided logical conflict; a multi-parent
merge produced three sides. Bookmark conflicts and divergence remained distinct
from file conflicts. Git objects carried jj-specific conflict headers.

Text replacement and `:ours` have narrower capabilities than arbitrary tree
restructuring; matrix negatives describe the tested probe.

## Known limitations

- Docker/Linux amd64 were exercised; Podman Compose and ARM64 were not.
- Path, symlink and rename results are fixture-scoped exploratory observations.
- Ordinary Git trees/index do not interpret jj's logical conflicts.
- Pending Git rebase/cherry-pick, stale workspaces, LFS, submodules, attributes, hooks, signing and shallow/partial clones are not experimentally covered.
- Core resets preserve evidence and Forgejo's PR-history volume; `forge stop` preserves server data.
- The optional server's UI bridge has normal routing; no experiment depends on outbound access, and external integrations are disabled. The hosted runner stays internal-only.
- Scenario code is trusted Python. Guards and the container are not a sandbox for arbitrary hostile plugins.

See [generated limitations](research/limitations.md) for fixture details.

## Questions remaining

Validate Podman/ARM64 parity; explore richer tree-resolution choices, external
merge tools, pending Git rebase state, stale workspace recovery and convergence
cases requiring human choices. Compare versioned baselines before upgrades.
Hosting-specific policy needs separate evidence.

## Recommended curriculum primitives

The experiments support considering: `@` as a revision; filesystem snapshot
boundaries; logical versus Git commit identity; explicit ancestry; `new` versus
`edit`; operation recovery; bookmarks and remote tracking; fetch versus rebase;
publication boundaries; first-class file conflicts; separate bookmark conflicts
and divergence; Git's authority limits; and PR identity versus its moving head.

These are evidence-derived primitives. The concise first-principles guide built from
them is [Jujutsu from first principles](JJ-MENTAL-MODEL.md); it is intentionally
separate from the experimental evidence and does not change scenario results.
