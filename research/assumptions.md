# Assumptions and scope

The initial identity, ancestry, fetch/push, conflict and convergence hypotheses now
have executable experiments and generated results. See findings.md for the exact
passing assertions; path outcomes remain EXPLORATORY, and convergence and unfinished
Git merge import remain VERSION_SENSITIVE.

Not yet experimentally verified:

- Podman Compose behavior and Linux ARM64 execution (the transport/pins support them).
- Windows filesystem behavior, including symlinks and case collisions.
- Arbitrary rename detection: the fixture uses filesystem moves and records actual results.
- Every external merge tool or possible manual tree-resolution strategy.
- Git rebase/cherry-pick in progress, stale workspace recovery, submodules, LFS,
  hooks, attributes, shallow/partial clones, tags and signing behavior.
- GitHub hosting policy, authentication, branch protection, PR UI or review workflows.

No fixture result is promoted to a universal invariant. Unknown matrix cells
mean unmeasured or inapplicable, never an inferred false result.
