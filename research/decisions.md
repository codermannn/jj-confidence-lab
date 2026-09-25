# Architecture decisions

## 1. Python

Decision: Python

Context: Small local filesystem/subprocess harness

Options considered: Python, shell, Rust

Choice: Python 3.13

Why: Typed standard library is sufficient

Consequences: No heavy application framework

## 2. uv

Decision: uv

Context: Rebuildable dependency graph

Options considered: uv, pip plus manual locks

Choice: uv locked sync/run

Why: Fast maintained FOSS tool with lockfile

Consequences: Commit uv.lock

## 3. Typer + Rich

Decision: Typer + Rich

Context: Readable CLI without a TUI

Options considered: argparse, Typer/Rich

Choice: Typer + Rich

Why: Typed CLI and restrained semantic presentation

Consequences: Only two direct runtime dependencies

## 4. pytest

Decision: pytest

Context: Real VCS behavior is the test subject

Options considered: unittest, pytest

Choice: pytest

Why: Independent tmp_path fixtures and parametrization

Consequences: No mocked scenario VCS

## 5. Ruff

Decision: Ruff

Context: Keep quality tooling small

Options considered: separate formatter/linter, Ruff

Choice: Ruff

Why: One maintained formatter/linter

Consequences: Check both formatting and lint

## 6. OCI boundary

Decision: OCI boundary

Context: No host credentials or work repositories

Options considered: host execution, Docker/Podman

Choice: OCI with named volume and no runtime network

Why: Disposable offline runtime

Consequences: Image build requires network; no host mounts

## 7. Local bare remote

Decision: Local bare remote

Context: Multi-actor reproducibility

Options considered: GitHub, HTTP server, filesystem

Choice: Bare Git origin under lab root

Why: No SaaS, credentials or daemons

Consequences: Does not model hosting protections

## 8. Colocation

Decision: Colocation

Context: Expose actual Git objects and refs

Options considered: separate backend, colocated

Choice: Explicit --colocate

Why: Both tools inspect same real state

Consequences: jj inspection may import Git changes

## 9. Semantic assertions

Decision: Semantic assertions

Context: Hashes and timing vary

Options considered: terminal snapshots, domain assertions

Choice: Immutable dataclasses and JSON templates

Why: Identity and graph relationships survive metadata variation

Consequences: Raw output retained separately

## 10. Dependency direction

Decision: Dependency direction

Context: Avoid cyclic scenario/evidence/UI coupling

Options considered: plugin framework, small modules

Choice: Runner → adapters → fixtures/inspectors → assertions/engine → evidence/UI

Why: Explicit inputs, no global mutable registry

Consequences: Registry is constructed on demand

## 11. Pinning

Decision: Pinning

Context: Rebuild same toolchain

Options considered: floating packages, pinned snapshots

Choice: OCI digests; Debian snapshot; release SHA-256; uv.lock

Why: Immutable inputs

Consequences: Upgrades are intentional and require all experiments

## 12. Build backend and runtime sync

Decision: Use the uv 0.11.3 bundled `uv_build` backend, pinned exactly.

Context: A separate Python build backend introduced an otherwise unlocked build-time dependency graph. An offline startup also exposed redundant editable-package rebuilding.

Options considered: pin every backend transitive dependency; use bundled uv backend.

Choice: `uv_build==0.11.3`; locked image sync followed by `UV_NO_SYNC=1` at runtime.

Why: This pure Python package requires no custom build hooks. The already pinned uv binary includes the matching backend. Runtime commands use baked dependencies, verified by doctor.

Consequences: Development still uses `uv sync --locked`; source edits require image refresh. No per-scenario installs. See https://docs.astral.sh/uv/concepts/build-backend/.

## 13. Optional Forgejo PR laboratory (user-requested scope extension)

Decision: Add a separate, opt-in Forgejo container for PR lifecycle experiments.

Context: After the bare-remote harness passed, the user requested a container to mimic PRs, remote sync and rebase, then asked to continue. This supersedes the original no-HTTP-server restriction for this optional subsystem.

Options considered: bare remote only; GitHub SaaS; local Forgejo.

Choice: Forgejo 16.0.5 rootless, pinned by OCI digest, SQLite in a dedicated volume; separate internal Compose network, UI bound to 127.0.0.1:3080. Keep ordinary `lab` network disabled. A separate `forgejo` remote is visible alongside the original local `origin`.

Why: Real PR identities, reviews, merge state and Git HTTP transport can be measured without personal credentials, a hosted account, runners or an external database. Forgejo is GPL-3.0-or-later.

Consequences: `./lab forge start/run/stop` explicitly manage this optional service. Only the fixed Forgejo hostname and harness-created repository path are allowed by the hosted adapter. Alice/Bob credentials are disposable public test values. Forgejo is not claimed to duplicate GitHub policy or UI. Base scenarios and tests do not require the server.

Sources checked 2026-09-25: https://forgejo.org/releases/, https://forgejo.org/docs/latest/admin/installation/docker/, https://forgejo.org/docs/latest/user/api/usage/, upstream v16.0.5 Dockerfile.rootless and templates/swagger/v1_json.tmpl.

Measured networking adjustment: Docker 29.7.2 did not publish the configured host
port for a service attached only to an internal network. Forgejo now also joins
a UI bridge; the test runner stays internal-only. The UI is bound to localhost.
The server has ordinary bridge routing, but external integrations are disabled;
no experiment requires an external request after images are built. See
https://docs.docker.com/engine/network/port-publishing/.
