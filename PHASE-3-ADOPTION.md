# Phase 3 — Adoption validation

Phase 3 is a repeatable confidence check for a team considering jj alongside
Git hosting. It does not claim that Forgejo behavior is identical to GitHub.

## 1. Reproduce the supported environment

```sh
# Start or rebuild the isolated lab and its services.
./lab start
./lab doctor
./lab forge doctor
```

Record the versions printed by the commands. Do not compare results across jj
versions without a new baseline.

## 2. Validate the team workflows

```sh
# Run the named experiment and record its evidence.
./lab scenario run context-switch
./lab scenario run remote-update
./lab scenario run rebase
./lab scenario run push-safety
./lab conflict run text-same-line
./lab conflict run unresolved-rebase
./lab scenario run workspace
./lab forge run
```

These cover the adoption risks that matter most: replacing stash habits,
separating fetch from rebase, refusing stale publication, carrying conflicts,
keeping stacked work understandable, using multiple directories, and updating a
review while its commit ID changes.

## 3. Review evidence, not impressions

```sh
# Generate or compare behavior reports.
./lab behavior report
./lab evidence list
./lab forge status
```

For a release or jj upgrade, export the evidence and compare it with a prior
baseline:

```sh
# Inspect or export container state.
docker compose run --rm -T --entrypoint tar lab -C /lab -czf - artifacts research > artifacts/lab-evidence.tar.gz
./lab behavior diff OLD.json NEW.json
```

A failed assertion is a reason to inspect the raw command log and snapshots. Do
not replace a baseline merely because a command exited successfully.

## Supported boundary

The validated path is Docker/Linux amd64 with the pinned toolchain and the
local Forgejo service. Podman, ARM64, stale workspaces, submodules, LFS,
shallow/partial clones, signing, hooks, and hosting-specific policy remain
follow-up validation work.
