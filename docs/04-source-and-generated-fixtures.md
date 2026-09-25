# Source and generated fixtures

## There is no generated application under test

The lab does not generate a separate product repository. It generates small,
disposable Git/jj repositories from Python fixtures, then runs real `git` and
`jj` binaries against them. The source of truth is this checkout; the generated
repositories are runtime data under `/lab`.

## Code path from command to experiment

```text
./lab scenario run rebase
  → Compose starts the image
  → pyproject.toml maps `lab` to jj_lab.cli:main
  → cli.py resolves the scenario registry
  → scenarios/registry.py imports fundamentals, interoperability, conflicts
  → scenarios/base.py executes ARRANGE → ACT → OBSERVE → ASSERT → REPORT
  → repos/factory.py creates the disposable topology
  → vcs/adapters.py invokes real Git/jj subprocesses
  → inspect/snapshot.py reads the resulting state
  → evidence/recorder.py writes the run artifacts
```

The entry point is declared in [`pyproject.toml`](../pyproject.toml). The
container copies the checkout with `COPY . .` in [`Dockerfile`](../Dockerfile),
then uses the locked virtual environment with `uv run --locked lab`.

## How repositories are generated

[`repos/factory.py`](../src/jj_lab/repos/factory.py) creates a unique path such
as:

```text
/lab/runs/rebase/20260925T...Z/
├── origin.git/   # local bare Git repository
├── alice/        # colocated jj + .git workspace
├── bob/          # Git-only clone
├── carol/        # Git-only clone
└── .lab-owned    # deletion safety marker
```

The seed files and initial commit are defined in the factory. A scenario then
edits files through the `Actor` methods and invokes the real VCS commands.
Scenario definitions live in [`scenarios/fundamentals.py`](../src/jj_lab/scenarios/fundamentals.py),
[`scenarios/interoperability.py`](../src/jj_lab/scenarios/interoperability.py),
and [`scenarios/conflicts.py`](../src/jj_lab/scenarios/conflicts.py).

## How evidence is generated

[`evidence/recorder.py`](../src/jj_lab/evidence/recorder.py) writes each run's
`metadata.json`, `commands.jsonl`, `before.json`, `after.json`,
`assertions.json`, checkpoints, normalized text views, `compare.txt`,
`xray.txt`, and `summary.md`. Reports in `/lab/research` are derived from the
latest recorded evidence by [`evidence/reporting.py`](../src/jj_lab/evidence/reporting.py).

The generated reports checked into this repository under `research/` are
snapshots of recorded lab runs, not hand-authored runtime behavior.

## How Forgejo users and repositories are generated

[`containers/forgejo-init.sh`](../containers/forgejo-init.sh) runs on Forgejo
startup. It migrates the database and idempotently creates `alice` and `bob`
with the disposable lab password. The hosted scenario then creates a fresh
`lab-*` repository through [`forge/client.py`](../src/jj_lab/forge/client.py)
and drives its PR through [`forge/scenario.py`](../src/jj_lab/forge/scenario.py).
