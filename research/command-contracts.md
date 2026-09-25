# Command contracts

Authority: selected jj 0.45.1 binary help; official versioned templates and docs in sources.md.

- `jj git clone --colocate`: explicit colocated clone.
- `jj log --no-graph -T`: semantic JSON templates, not graph scraping.
- `jj resolve --list`: lists conflict paths; not proof a tool can resolve them.
- `jj resolve --tool :ours`: built-in side selection; 3-way limitations must be measured.
- `jj converge --no-interactive`: may exit successfully without resolving; assert divergence count separately.
- `jj --at-operation`: historical operations imply ignoring working copy.
- `jj undo`: inverse repository operation, not rollback of published remote state.

Experiment-linked contracts are appended after baseline execution.

## Experiment-linked contracts (jj 0.45.1)

These contracts apply to the named fixtures, not arbitrary repositories. Generated
results and assertions are the empirical authority; documentation is in sources.md.

- `jj git init` / `jj git clone --colocate`: creates colocated `.jj` and `.git`; even an empty origin has a jj working-copy revision (`empty-clone`, doctor).
- `jj status`: snapshots changed working-copy content, retaining its change ID and replacing its commit ID (`working-copy`, `evolving-change`). It also imports external Git state (`mixed-mutation`). This is a mutation boundary, not an inert observer.
- `jj log --no-graph -r … -T …`: JSON serialization supplies change/commit IDs, parents, conflict and divergence booleans. `conflicted_files().conflict_side_count()` supplies logical sides, not marker counts (all inspectors).
- `jj new`: selects a new child revision; multi-parent `new` can create a three-sided conflict (`new`, `many-sided`).
- `jj edit`: selects an existing mutable logical change and restores its files (`new-vs-edit`, `context-switch`).
- `jj describe`: metadata rewrite preserves logical identity; descendants are rewritten onto replacement parents (`describe`, `descendant-rewrite`).
- `jj squash -m`: moves child content into the parent and preserves the parent's change identity (`squash`).
- `jj undo`: restores the pre-operation revision in the tested description rewrite and preserves previously recorded logical conflicts (`undo`, file conflict probes).
- `jj op log --no-graph -T 'json(self)'`: records operation ID, parents, description and snapshot flag. Inspector models immutable operation values; raw command JSON retains additional metadata (`operation-history`).
- `jj op restore <operation>`: restores primary state between independent conflict probes. It does not reverse external remote changes; probes do not publish.
- `jj workspace add`: creates a second working copy referencing shared history (`workspace`). Stale-workspace recovery is documented but not reproduced here.
- `jj rebase -s … -d …`: preserves selected change identity with changed commit identity and ancestry (`rebase`). Successful exit can coexist with logical conflicts (file conflict experiments).
- `jj bookmark create/set`: names an explicit revision; setting a conflicted bookmark to one target resolves that reference conflict (`coworker`, `bookmark`).
- `jj bookmark list --all-remotes -T …`: exposes added/removed targets, conflict and tracking states. Local bookmarks, `@git` mirrors and `@origin` observations remain distinct in snapshots.
- `jj git fetch`: observes the remote; in the tested configuration it moves tracked `main`, without rebasing unrelated local work (`remote-update`). Incompatible movement creates a bookmark conflict (`bookmark`).
- `jj git push --bookmark …`: publishes selected clean revisions as ordinary Git commits; rejects a stale incompatible remote or conflicted bookmark (`coworker`, `push-safety`, `bookmark`). Failure evidence preserves stderr and remote refs.
- `jj resolve --list`: lists conflicts but does not establish tool applicability. `--tool :ours` resolves tested text and modify/delete cases; tested tree/symlink and three-sided cases expose limitations. Consult the generated matrix for exact outcomes.
- Manual editing can resolve one hunk while leaving another conflicted (`partial-resolution`). An ancestor's resolution propagates to the tested descendants (`stacked`).
- `jj converge --no-interactive`: resolves this reproducibly revived predecessor fixture. Success exit alone is insufficient: the harness checks successor count. This command is experimental and version-sensitive (`divergent`).
- Git `switch`, `commit`, `add`, `merge`, `cat-file`, `ls-tree`, `for-each-ref`, `symbolic-ref`, `rev-parse`, and `status --porcelain=v2` inspect or mutate actual Git state. No pretty graph is parsed for assertions (`mixed-mutation`, `git-index`, `git-underneath`, `detached-head`).
- **VERSION_SENSITIVE**: during the tested unfinished Git merge, the next jj import clears `MERGE_HEAD` and snapshots textual Git conflict markers as ordinary file content, without a jj logical conflict (`mixed-pending-merge`).

## Optional Forgejo 16.0.5 contract (REPRODUCED)

`forgejo-pr` created a repository and PR through the version-pinned API, then
compared PR `head.sha` with the actual jj commit and hosted branch. After Bob
advanced `main`, Alice's fetch did not change local ancestry. Rebase retained
change identity and rewrote commit identity; pushing changed the head of the
same PR. Bob approved and merged it, and ordinary Git fetched both feature and
urgent-fix contents. All HTTP requests/responses and transport commands are
recorded alongside checkpoints. Forgejo PR semantics are not GitHub guarantees.
