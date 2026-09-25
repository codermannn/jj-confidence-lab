# jj-confidence-lab knowledge base

This is a repository map for understanding the lab as a running system. It is
written in a DeepWiki-like style: start with the map, then follow the links to
the runtime, storage, and source pages.

## Read in this order

1. [System map](01-system-map.md) — the components and their boundaries.
2. [Runtime lifecycle](02-runtime-lifecycle.md) — what runs, and when.
3. [Storage and volumes](03-storage-and-volumes.md) — what survives a container
   exit and where Docker stores it.
4. [Source and generated fixtures](04-source-and-generated-fixtures.md) — where
   the code comes from and how repositories/evidence are produced.
5. [Operations and troubleshooting](05-operations.md) — safe inspection,
   reset, export, and recovery commands.
6. [VisualJJ scenario map](06-visualjj-scenario-map.md) — which VisualJJ-style
   workflows this lab covers and where the boundaries are.
7. [Command coverage](07-command-coverage.md) — the complete inventory of
   covered, experimental, and intentionally deferred jj commands.
8. [Deployment workflow](08-deployment-workflow.md) — how jj history becomes a
   reviewed, tested, promoted, and reversible release.

9. [Selective push](09-selective-push.md) — publish a ready payment change while keeping unfinished work local.

The Phase 2 tutorial alternates the **developer** and **release engineer**
roles so the same graph is understood from creation through rollback.

The learner-facing material remains in [PHASE-2-TUTORIAL.md](../PHASE-2-TUTORIAL.md).
The experimental evidence report is [PHASE-1-REPORT.md](../PHASE-1-REPORT.md).

## Editor, VisualJJ, and CI boundaries

- The lab does not require or configure VS Code. The checkout contains an
  [`.editorconfig`](../.editorconfig), and the container sets `EDITOR=true` so
  jj commands do not pause for an interactive editor. Use VS Code, Vim, or any
  editor you prefer on the host.
- [VisualJJ](https://www.visualjj.com/learn) is useful as an optional visual
  explanation of jj, stacked pull requests, interdiffs, and workspaces. Its
  guides target VisualJJ/GitHub workflows; this repository does not integrate
  or test the VisualJJ application against local Forgejo.
- CI is not required for local jj operations, rebases, conflicts, workspaces,
  or the local PR exercise. CI is useful when a team wants repeatable checks.
  This repository already has GitHub Actions jobs for quality, harness,
  scenario, and Forgejo tests in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

## One-minute model

```text
./lab (host wrapper)
  ├─ compose.yaml → lab container → uv run lab → src/jj_lab/cli.py
  │                                      ├─ creates fixtures in /lab/runs
  │                                      ├─ runs jj/Git commands
  │                                      └─ records evidence in /lab/artifacts
  └─ compose.forgejo.yaml → Forgejo container → /var/lib/gitea
                              └─ local PR API/UI at http://localhost:3080
```

The lab container has `network_mode: none`; only the separate Forgejo network
allows the hosted experiment to reach the Forgejo service. The application
code is copied into the image at build time, while experiment state is mounted
from named volumes at run time.

## Fast inspection commands

Run these from the repository root:

```sh
# Use the readable Make facade for common workflows.
make start
make list
make state
# The ./lab wrapper remains the canonical interface.
./lab state
./lab scenario list
./lab forge status
docker compose -f compose.yaml -f compose.forgejo.yaml ps
docker volume inspect jj-git_lab-data
docker volume inspect jj-git_forge-data
```

If Compose chose a different project name, discover the exact volume names with:

```sh
# Inspect or export container state.
docker compose -f compose.yaml -f compose.forgejo.yaml config --volumes
docker volume ls
```
