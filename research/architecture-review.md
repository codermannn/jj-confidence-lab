# Phase 1 architecture review

Reviewed the finished layers and observed failures, then corrected the issues below.

- One VCS subprocess runner uses argv arrays, a closed environment, timeouts, and typed results. Quality tooling is the only separate subprocess boundary; it runs project checks, not scenario VCS operations.
- Adapters own VCS transport; actor fixtures own mutations; inspectors use JSON templates and plumbing. Assertions and comparison are independent of Rich. Presentation contains no repository write logic.
- Revision, bookmark, file, ref and operation values are frozen dataclasses with tuple relationships. Change IDs and commit IDs are separate types. Divergent successors are retained as multiple revisions.
- Observation is explicitly a snapshot/import boundary. Optional destructive conflict probes are labelled and restored; their intermediate states remain in checkpoints.json.
- Path guards resolve symlinks and reject the lab root or escaping paths for deletion. Deletion requires ownership markers. File scanners never follow links. Native process environments do not inherit credentials or Git/jj overrides.
- Bare transport validates both fetch and push URLs. Hosted transport validates the exact local Forgejo URL and fixture ownership registration; redirects and inherited HTTP proxies are disabled. Ordinary actors reject alternate transport names.
- Failing commands, assertions, missing executables and fixture failures retain machine evidence. Raw records preserve IDs/timestamps; human views normalize them. Fixed a missing-toolchain recording failure path.
- Fixed a comparison heuristic so a changed parent alone is not labelled automatic: it must map to the replacement commit of the same parent change.
- Fixed a baseline-export key mismatch; added a pure regression test so recorded booleans and side counts survive compact export.
- Replaced a separate build backend with pinned uv's bundled backend to eliminate a floating build dependency graph. Runtime uses the baked locked environment without package installs per scenario.
- Corrected the CLI's direct reset invocation to pass a real boolean rather than a Typer option descriptor.
- Forgejo is opt-in, rootless and uses a separate data volume. The core has no service/network dependency; the hosted job has explicit local accounts and an internal runner network.

Limits: no adversarial sandbox for arbitrary user-authored Python scenarios; the container is the outer boundary. No concurrent mutation of a single fixture. No claim of ARM64/Podman validation. Server bridge routing enables localhost publishing; offline execution is a dependency property, not a firewall guarantee for the optional server.

The architecture remains small: no plugin framework, dependency-injection container,
database for harness state, background worker, tutorial engine or LLM at runtime.

Final evidence review also separated checkpoint inspection from the action phase.
A normal detached-HEAD `git symbolic-ref` exit code had incorrectly made the
aggregate operation-success field false in compound experiments. Checkpoints now
have their own phase labels, and an integration regression test covers this boundary.

Hosted review verification was tightened after inspecting the returned API state:
Forgejo requires `APPROVED`, and an unknown event can create a pending review.
The harness now asserts actual approval before merge. Merge retries are limited
to Forgejo's documented-in-source pre-mutation 405 readiness response; the expected
head commit is supplied on every attempt, and the final merged flag is polled.
