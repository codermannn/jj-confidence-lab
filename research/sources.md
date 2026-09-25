# Research sources

Checked 2026-09-25 before application implementation. Latest release API and release page both select v0.45.1. Binary SHA-256 checked against GitHub release asset digest.

- https://docs.jj-vcs.dev/latest/install-and-setup/ — Release binaries; Git >=2.41 requirement; identity configuration.
- https://docs.jj-vcs.dev/latest/tutorial/ — Working copy is a revision; change identity differs from commit identity.
- https://docs.jj-vcs.dev/latest/working-copy/ — Inspection can snapshot files; observation is not always read-only.
- https://docs.jj-vcs.dev/latest/git-compatibility/ — Colocation, automatic import/export, index and unsupported Git features.
- https://docs.jj-vcs.dev/latest/git-comparison/ — Different working-copy and history models; no command equivalence assumed.
- https://docs.jj-vcs.dev/latest/git-experts/ — Detached HEAD and local high-level jj interpretation.
- https://docs.jj-vcs.dev/latest/bookmarks/ — Local/remote tracking and conflicted bookmark targets.
- https://docs.jj-vcs.dev/latest/conflicts/ — Logical conflicts may persist after a successful operation.
- https://docs.jj-vcs.dev/latest/technical/conflicts/ — Algebraic merge terms, not nested stored text markers.
- https://docs.jj-vcs.dev/latest/revsets/ — Graph selection, ancestry, conflicts and visible revisions.
- https://docs.jj-vcs.dev/latest/guides/divergence/ — Multiple visible revisions per change; experimental converge.
- https://docs.jj-vcs.dev/latest/github/ — Bookmark publishing; local bare remote models transport, not GitHub policy.
- https://docs.jj-vcs.dev/latest/cli-reference/ — Command/flag contracts including workspace add/list/update-stale.
- https://docs.jj-vcs.dev/latest/operation-log/ — Repository operations and undo; remote side effects are separate.

- https://api.github.com/repos/jj-vcs/jj/releases/latest — release selection and asset digests.
- https://github.com/jj-vcs/jj/releases/tag/v0.45.1 — selected immutable release.
- https://github.com/jj-vcs/jj/blob/v0.45.1/docs/templates.md — JSON templates, conflicted_files and conflict_side_count.
- https://github.com/jj-vcs/jj/blob/v0.45.1/cli/tests/test_converge_command.rs — upstream convergence fixtures.
- `jj 0.45.1 help`, `git clone/push`, `bookmark list`, `resolve`, `converge`, `workspace`, `undo`, `op restore`, `rebase --help` — inspected selected binary contracts.
- Workspace documentation lives in CLI reference; /workspaces/ is not a valid current documentation page.
- https://docs.astral.sh/uv/concepts/projects/sync/ — locked sync/run.
- https://typer.tiangolo.com/ — typed command interface (MIT).
- https://rich.readthedocs.io/en/stable/console.html — terminal rendering and NO_COLOR (MIT).
- https://docs.pytest.org/en/stable/ — test isolation (MIT).
- https://docs.astral.sh/ruff/ — formatter/linter (MIT).

Python is PSF licensed; uv and jj are MIT/Apache-2.0; Git is GPL-2.0. Runtime additions are limited to Typer and Rich and their locked dependencies.

## Optional Forgejo extension, requested during implementation

- https://forgejo.org/releases/ — stable release 16.0.5, published 2026-09-17.
- https://forgejo.org/docs/latest/admin/installation/docker/ — official rootless container, environment configuration and volumes.
- https://forgejo.org/docs/latest/user/api/usage/ — local API authentication and repository operations.
- https://codeberg.org/forgejo/forgejo/src/tag/v16.0.5/templates/swagger/v1_json.tmpl — exact create PR, review and merge request fields.
- https://codeberg.org/forgejo/forgejo/src/tag/v16.0.5/Dockerfile.rootless — entrypoint, UID 1000, volume and GPL-3.0-or-later license.
- Official rootless 16.0.5 image index: `sha256:5effb7305584aca479b29fde6f9631a6dbe86ae798ae02eeea33a3666f0c0bf8`.
- https://codeberg.org/forgejo/forgejo/src/tag/v16.0.5/modules/structs/pull_review.go — approval event is `APPROVED`; other unknown values can become pending reviews.
- https://codeberg.org/forgejo/forgejo/src/tag/v16.0.5/routers/api/v1/repo/pull.go — exact pre-mutation 405 “Please try again later” response during mergeability checks; bounded retry records every response.
