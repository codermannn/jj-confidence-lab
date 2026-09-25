# jj command coverage

This matrix is the course checklist for pinned jj `0.45.1`. It separates the
commands a learner needs for the everyday mental model from advanced or
host-specific commands that belong in a later appendix.

## The experienced-developer daily loop

The high-frequency workflow is deliberately covered end to end. A senior
developer usually repeats this small loop many times a day:

1. `jj status`, `jj log`, `jj diff`, and `jj show` answer “what is true now?”
2. Edit files, then use `jj describe`, `jj new`, or `jj edit` to name and move
   between logical changes.
3. Use `jj split`, `jj squash`, `jj absorb`, or `jj diffedit` to make the
   change reviewable without staging-area gymnastics.
4. Use `jj op log`, `jj undo`, `jj op restore`, and `jj evolog` when history or
   metadata needs inspection or recovery.
5. Fetch, rebase, resolve, and publish with `jj git fetch`, `jj rebase`,
   `jj resolve`, `jj bookmark`, and `jj git push`.

The lab also exercises regression hunting with `jj bisect` and parallel local
work with `jj workspace`. These are less frequent, high-value tasks that tend
to matter most when a change is difficult.

## Covered in the guided course

| Command | Where | What the learner learns |
| --- | --- | --- |
| `status`, `log`, `diff`, `show` | Phase 2, working copy and evidence | Read the current revision and its content |
| `new`, `edit`, `describe` | Phase 2, change evolution | Move between logical changes |
| `split`, `squash`, `absorb`, `diffedit` | Phase 2, change shaping | Make history reviewable |
| `bisect` | Phase 2, regression search | Find the first bad revision with a test |
| `op log`, `op show`, `undo`, `op restore` | Phase 2, maintenance | Inspect and recover local operations |
| `rebase`, `git fetch`, `git push` | Phase 2 and Forgejo | Separate import, ancestry changes, and publication |
| `resolve` | Conflict scenarios | Treat conflicts as revision data |
| `workspace` | Phase 2 and workspace scenario | Keep multiple directories on one graph |
| `bookmark` | Forgejo and Git interoperability | Publish through Git-facing names |
| `evolog` | Mental model guide | Follow one change through rewrites |
| `tag` | Deployment workflow appendix | Name a release revision |

## Covered by experiments but not yet a teaching chapter

These commands already exist in the harness or its evidence, but need a
dedicated learner-facing explanation if a team depends on them:

| Command | Current evidence | Why it is separate |
| --- | --- | --- |
| `converge` | `divergent` scenario | Version-sensitive divergence recovery |
| `git` import/colocation plumbing | interoperability scenarios | Git backend behavior rather than a daily jj decision |
| `operation` templates and `at-op` inspection | operation-log docs | Useful recovery detail, not first-day material |

## Not yet covered by the lab

These are the actual remaining gaps, not hidden requirements:

| Command or area | Why it matters | Recommended treatment |
| --- | --- | --- |
| `interdiff` | Show what changed between two revisions of a review | Add a review-evolution experiment and chapter |
| `abandon`, `revert` | Discard or replay content intentionally | Add a cleanup/recovery chapter |
| `duplicate`, `parallelize`, `simplify-parents` | Copy and reshape graph topology | Advanced graph chapter |
| `next`, `prev`, `commit` | Navigation and Git-like convenience aliases | Short reference section |
| `fix`, `run` | Apply formatters or commands across revisions | Tooling/automation chapter |
| `file`, `sparse` | File-level and partial checkout workflows | Large-repository chapter |
| `config`, `metaedit` | Repository policy and metadata-only edits | Configuration appendix |
| `sign`, `unsign` | Commit signing and trust | Security/release appendix |
| `arrange` | Interactive graph arrangement | Advanced interactive tooling; not headless-tested |
| `gerrit` | Gerrit-specific review integration | Separate hosting adapter, outside Forgejo scope |
| `util` | Shell completions and maintenance utilities | Reference only |

## What “complete” means here

The core course is complete when a learner can edit, split, combine, park,
debug, recover, sync, resolve, publish, review, and work in parallel without
falling back to Git’s branch-and-stash mental model. It does not need to teach
every command in the binary to achieve that goal.

The next additions should be made in batches from the “Not yet covered” table,
with one scenario, one explanation, and one verified command path per batch.
