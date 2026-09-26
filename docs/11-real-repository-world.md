# The jj world, rehearsed on real repositories

The synthetic payment repository teaches one idea at a time. This optional lab
imports pinned histories from three public projects—Flask (Python), bat (Rust), and
GitHub CLI (Go)—then runs the same jj workflows against their real graphs and
files.

The original GitHub URL is used once to fetch the history reachable from a
pinned commit.
It is never stored as a Git remote. Each working clone has exactly one remote:
an `origin` owned by Alice on local Forgejo. The source URL remains only as
provenance in `real-repos.toml` and `.real-repos/provenance/`. This design makes an
accidental push upstream impossible through the clone's configured remotes.

The imported directories live in `.real-repos/`, are ignored by Git and Docker,
and are not uploaded with the course repository. They consume disk and local
Forgejo volume space. The public projects keep their original licenses and
history; this lab does not claim or republish them on GitHub.

## Prepare the three histories

Run on the host with internet access:

```sh
# Start Forgejo, fetch each pinned history, push it to our server, then add jj.
make real-prepare

# Confirm every clone points only to localhost Forgejo.
make real-list
```

Expected properties in `inventory.json`:

- `origin` starts with `http://localhost:3080/alice/real-`;
- `source_remote_present` is `false`;
- `head` equals the SHA pinned in `real-repos.toml`;
- the complete history reachable from the pinned commit is available.

Preparation is idempotent. Existing imports are reused only when their origin
still matches the expected local Forgejo URL. An unexpected remote stops the
script instead of rewriting it.

## Run the real-history scenarios

```sh
# Run three workflows on all three projects: nine isolated runs.
make real-run

# Or focus on one history and one idea.
python3 scripts/real_repos.py run --repo flask --scenario stacked
python3 scripts/real_repos.py run --repo bat --scenario megamerge
python3 scripts/real_repos.py run --repo github-cli --scenario workspace
```

Every run clones from local Forgejo into `.real-repos/runs/`, initializes a
colocated jj repository, and leaves the result for inspection. It never mutates
the pristine imported clone.

### Stacked changes

The scenario creates validation and receipt changes in a real README, rewrites
validation, and proves three separate facts:

1. receipt's commit ID changes because its parent changed;
2. receipt's change ID remains stable inside that jj repository;
3. receipt's new parent equals validation's new commit.

This is the accurate meaning of automatic descendant rebasing. Older versions
are replacement history, not extra commits to merge.

### Multi-parent integration change

The `megamerge` scenario creates independent Linux and Windows experiments,
then makes an integration change with both as parents. This is useful for a
temporary CI or compatibility workspace: test several heads together before
deciding how they should land. Git can make the same merge topology; jj makes
multi-parent working copies and later graph editing unusually direct.

Do not publish such an integration change merely because it builds. Its two
parents still need review and a deliberate host merge policy.

### Parallel workspaces

The workspace scenario creates a second directory backed by the same jj repo.
Each directory has its own working-copy commit, while both see the same graph
and operation history. This is especially useful for a developer plus an agent,
two agents, or a release investigation alongside feature work.

Git worktrees provide multiple directories too. jj's additional possibility is
that unfinished work in each directory is already represented as a change, so
the graph, automatic descendant rebasing, and operation log apply across the
shared repository.

## What actually changes if you switch

Some gains are new native combinations rather than mathematically impossible
Git workflows:

- **Continuously editable stacks.** Rewrite a lower change and jj rebases local
  descendants automatically. This makes “reviewable now, editable later” a
  practical default. You still repush affected bookmarks and rerun review/CI.
- **Repository-wide undo.** `jj op log` records local repository operations;
  `jj undo` and `jj op restore` can recover graph edits that would otherwise
  require reflog expertise. They cannot undo a remote push or deployment.
- **Conflicts as committed state.** A conflicted revision can exist in the
  graph, so unrelated work can continue and resolution can happen in another
  change or workspace. CI and Git tools may not understand that state safely.
- **Integration workspaces.** A working-copy commit can have several parents,
  making local merge queues, compatibility matrices, and speculative batch
  integration easier to create and discard.
- **Graph queries as workflow language.** Revsets can select mutable stacks,
  descendants, bookmarks, authors, or changes missing from trunk. Teams can
  turn those queries into review and maintenance tools.
- **Git-host compatibility.** Forgejo and GitHub still receive Git commits and
  branches. jj bookmarks are the publication boundary; server policy, CI,
  approvals, releases, and deployments remain host responsibilities.

The biggest strategic shift is delaying irreversible organization. Start work
as visible changes, reshape it after learning more, publish only selected
bookmarks, and recover through the operation log. Git can approximate much of
this through staging, interactive rebases, reflogs, worktrees, and scripts. jj
makes the mutable graph the normal interface.

## Limits this lab does not hide

- A jj change ID is useful within the jj repository's evolution history. The
  Git host reviews commit IDs and branch refs; do not treat the change ID as a
  universal cross-host review identifier.
- Rewriting a published stack changes Git commit IDs and can invalidate reviews,
  signatures, attestations, and cached CI results.
- Real build systems are intentionally not installed for Flask, bat, or GitHub
  CLI. These scenarios validate version-control behavior, not upstream tests.
- Tags and branches outside the pinned commit's reachable history are not
  mirrored; this is a reproducible working history rather than an archive.
- Submodules, LFS, signed commits, sparse monorepos, and host merge queues need
  separate representative repositories and validation before team adoption.

The project list and SHAs are data, not code. Add another `[[repository]]` to
`real-repos.toml`, choose a tracked text file, then rerun preparation to extend
the matrix without changing the scenario engine.

Sources: [official jj tutorial](https://docs.jj-vcs.dev/latest/tutorial/),
[working-copy model](https://docs.jj-vcs.dev/latest/working-copy/), and the
public repositories [Flask](https://github.com/pallets/flask),
[bat](https://github.com/sharkdp/bat), and
[GitHub CLI](https://github.com/cli/cli).
