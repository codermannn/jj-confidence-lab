# jj-confidence-lab

A disposable experimental environment for understanding Jujutsu and
its Git backend.

Prerequisite: Docker or Podman with a Compose provider. Forgejo is part of the
standard lab setup; it supplies the disposable remote and pull-request server.

The optional `Makefile` provides readable shortcuts. The underlying `./lab`
wrapper remains the canonical interface and works without `make`.

## Guided path: follow this in order

If you are learning the lab for the first time, use this path and do not skip
ahead. Run one block at a time. Commands labelled **host** are run from this
repository directory. Commands labelled **lab shell** run inside the disposable
container.

### 1. Start the environment — host

```sh
# Build the pinned images, start Forgejo, and create the interactive fixture.
./lab start
```

You should see the tool versions, Forgejo health check, and confirmation that
the interactive fixture is available. On a first run it is created; later runs
reuse it. If this fails, stop here and use
[Operations and troubleshooting](docs/05-operations.md).

### 2. See what you can run — host

```sh
# List the experiments, then inspect the active fixture.
./lab scenario list
./lab state
```

You should see Alice’s colocated jj workspace and the Git-only Bob and Carol
clones. At this point you are ready to learn jj.

### 3. Follow the learning sequence

Open [Phase 2 — Learn jj by running the lab](PHASE-2-TUTORIAL.md) and follow
sections 0 through 8 in order. That guide tells you when to enter
`./lab shell`, when to type `exit`, and which commands must run on the host.

The first section is a safe checkpoint:

```sh
# Reset only disposable repositories, run the first experiment, and inspect it.
./lab reset --all
./lab scenario run working-copy
./lab xray
./lab compare
```

### 4. Finish the hosted PR exercise — host

Do this after the Phase 2 sections. Forgejo is already started by `./lab start`.

```sh
# Verify the disposable Forgejo users, then run and inspect the real PR flow.
./lab forge doctor
./lab forge run
./lab forge status
```

Open the resulting local PR at [http://localhost:3080](http://localhost:3080)
if you want to see the same workflow in the browser.

Continue with [Enterprise workflows](docs/enterprise/README.md) for paired Git/jj
lessons on trunk-based delivery, stacked reviews, release branches, GitFlow,
two remotes, and deployment promotion.

### 5. Confirm the complete lab — host

```sh
# Run every core scenario and the complete quality gate.
./lab scenario verify
./lab check
```

The expected result is 44 core scenarios passing. The Forgejo experiment is
separate and is verified by `./lab forge run`.

### If you get lost

Return to the repository root and run:

```sh
# Re-enter the standard starting point without deleting evidence.
./lab start
./lab state
```

Use [the knowledge base](docs/README.md) when you want to understand what a
container, volume, generated repository, or evidence file is doing. Use
[Operations and troubleshooting](docs/05-operations.md) when a command fails.

VS Code is optional; the lab does not assume a particular editor. VisualJJ is
also optional and is useful for visual jj explanations, stacked PRs, and
interdiffs, but it is not integrated with or tested against this local
Forgejo setup. CI is only needed when you want these checks to run
automatically for a team; local jj work and the Forgejo exercise run without
CI.

Lint is CI-first: run `docker compose run --rm -T --entrypoint uv lab run
--locked ruff check .` for an optional local check, while the push/PR workflow
enforces the same command without requiring pre-commit hooks.

## Quick reference

    # Build the pinned images, start Forgejo, and create the lab fixture.
    ./lab start

Or, using the shortcut facade:

    # Run the same startup workflow through Make.
    make start

This builds the pinned lab image, starts Forgejo, creates the disposable `alice`
and `bob` accounts, and verifies the Forgejo API. Then:

    # List available experiments and inspect the active fixture.
    ./lab scenario list
    ./lab state

Run the complete quality gate and hosted workflow:

    # Run local tests, scenarios, and doctor checks.
    ./lab check
    # Run the real Forgejo PR lifecycle.
    ./lab forge run

Open the local Forgejo UI at http://localhost:3080. `./lab forge status` shows
the latest hosted evidence. Stop only the server with `./lab forge stop`; the
next `./lab start` brings it back. `./lab reset --all` resets lab repositories
while preserving evidence and Forgejo history.

Nothing in the lab accesses your real Git repositories,
credentials or configuration. Runtime networking is disabled. The image runs its already locked environment
without re-syncing dependencies per command. Only a named
lab volume is mounted. Use `LAB_RUNTIME=podman ./lab start` to select Podman.

## Architecture

Python command runner → Git/jj adapters → actor fixtures → semantic snapshots
and assertions → scenario engine → evidence and Typer/Rich presentation.
Each experiment creates a local bare origin, Alice's colocated jj workspace,
and Git-only Bob and Carol clones. Snapshots explicitly run `jj status` first:
inspection can snapshot files and import Git state.

## Development

The supported learner interface is `./lab`. `./lab shell` gives a shell inside
the same isolated volume. Run `lab state` to inspect the active experiment;
its path is recorded in `/lab/active`. Use `cd "$(cat /lab/active)/alice"` for
raw commands. `lab reset` replaces interactive state; `lab reset --all` also
removes experiment repositories. Evidence is retained by both commands.

For native harness development only: install pinned jj 0.45.1, Git >=2.41,
uv 0.11.3, then `uv sync --locked`. Set `LAB_ROOT` to a dedicated disposable
directory before `uv run --locked lab ...`. Normal use needs none of these
host installations. Run `./lab start` after source edits to refresh the image.

## Testing

    # Run formatting, linting, tests, scenarios, and doctor checks.
    ./lab check

Runs Ruff formatting/lint, ShellCheck, unit tests, real-repository integration
tests, every core scenario, and doctor. The Forgejo service is started by
`./lab start`; run `./lab forge run` for the hosted PR experiment. Tests have
independent roots. CI builds and tests the actual container. No VCS is mocked in
scenario tests.

## Evidence

    ./lab scenario run working-copy
    ./lab xray
    ./lab compare
    ./lab why
    ./lab coworker-view
    ./lab conflict run text-same-line
    ./lab scenario verify
    ./lab behavior report

Evidence lives in `/lab/artifacts/evidence/<scenario>/<run>/` in the named volume.
Each run includes command JSONL, snapshots, assertion results, intermediate
checkpoints, normalized text views, and a summary. Conflict experiments also
record separately labelled probes for postponement, transformation, resolution
and recovery, then restore the primary after-state. `--json` gives machine output;
`--verbose` exposes fixture commands. Reports are generated in `/lab/research`.
`NO_COLOR=1 ./lab state` disables colour. `--debug` exposes unexpected tracebacks.

Export evidence without mounting host directories:

    # Stream evidence and reports from the named volume into a host archive.
    docker compose run --rm -T --entrypoint tar lab -C /lab -czf - artifacts research > artifacts/lab-evidence.tar.gz

For Podman, replace `docker` with `podman`. See [research](research/sources.md),
[the behavior matrix](research/behavior-matrix.md), and [the Phase 1 report](PHASE-1-REPORT.md).

## Upgrading jj

1. Verify the stable release and asset SHA-256 values against upstream.
2. Update `JJ_VERSION` and architecture checksums in `Dockerfile`, the doctor pin,
   and version expectations in tests. Update the research ledger.
3. Rebuild with `./lab start`; run `./lab doctor` and `./lab check`.
4. Run `./lab scenario verify` and `./lab behavior report`.
5. Export reports; compare compact baselines with `lab behavior diff OLD NEW`.
6. Investigate semantic changes, then update command contracts. Never replace a
   failing baseline merely because a command exited successfully.

## Project phases

The original specification defines Phase 1 and deliberately does not prescribe a
final phase count. The practical three-phase plan is:

1. **Phase 1 — Experimental harness:** the container, real Git/jj/Forgejo
   fixtures, semantic assertions, evidence, reports, and CI in this repository.
2. **Phase 2 — Learning path:** the concise [first-principles guide](JJ-MENTAL-MODEL.md)
   built from verified Phase 1 behavior.
3. **Phase 3 — Adoption validation:** optional team workflows, hosting policy,
   platform parity, and maintenance checks after the learning path is stable.

Only Phase 1 is a completed experimental deliverable. The guide is intentionally
short and evidence-derived; Phase 3 is a future validation phase, not a claim of
universal GitHub or Forgejo behavior.

The copy-and-run Phase 2 path is [PHASE-2-TUTORIAL.md](PHASE-2-TUTORIAL.md).
The repeatable Phase 3 adoption gate is [PHASE-3-ADOPTION.md](PHASE-3-ADOPTION.md).

## Knowledge docs

The [knowledge base](docs/README.md) explains the system in DeepWiki-style
pages, with Mermaid diagrams for the component map, scenario lifecycle, and
storage boundaries. It also documents where generated fixtures and evidence
come from, how to find Docker volume mountpoints, and which reset commands
preserve or delete state.

## Forgejo-backed pull requests

    # Run, inspect, then stop the local Forgejo PR server.
    ./lab forge run
    ./lab forge status
    ./lab forge stop

Forgejo 16.0.5 runs in a separate rootless container with SQLite and a named
volume. Open [the local forge](http://localhost:3080). Public disposable accounts
are `alice` and `bob`, both with password `Lab-only-password-2026!`. No personal
credentials are used. The experiment creates a fresh repository and actual PR,
pushes an update to `main`, fetches, rebases the jj feature, updates the same PR,
records Bob's approval, merges, and verifies what Git-only Bob receives.

The hosted remote is named `forgejo`; the local bare `origin` stays visible.
API requests, responses and Git/jj commands use the same evidence recorder.
`./lab behavior report` includes the hosted result after it has run.
The core `./lab check` needs no Forgejo service; CI has a separate hosted experiment job.

Only `127.0.0.1:3080` is published. The harness joins an internal-only network;
Forgejo also has a bridge network for the localhost UI. Server integrations,
mail, avatars, federation, Actions and update checking are disabled. Forgejo
is a local PR model, not a claim of GitHub UI/policy equivalence.
`forge stop` preserves PR history. Core resets retain Forgejo's separate volume.
