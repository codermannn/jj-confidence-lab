# Phase 1 execution record

1. Researched stable jj, binary help, official documentation, upstream templates/tests and current tooling.
2. Recorded decisions and the initial assumptions/questions before application code.
3. Bootstrapped Python src layout and uv.lock.
4. Built pinned OCI inputs; corrected the release archive's `./jj` extraction path.
5. Implemented the isolated argv command runner and typed command results.
6. Implemented owned local-remote fixtures and Alice/Bob/Carol actors.
7. Implemented structured jj/Git/filesystem/remote inspection.
8. Implemented rendering-independent semantic assertions.
9. Implemented the explicit scenario lifecycle and checkpoints.
10. Implemented the Typer/Rich CLI and doctor.
11. Implemented raw and normalized evidence retention, including failures.
12. Implemented fundamental experiments.
13. Implemented Git interoperability experiments.
14. Implemented negative controls and the conflict laboratory.
15. Implemented unit, real-repository integration and scenario tests.
16. Implemented container-based GitHub Actions quality/harness/scenario jobs.
17. Ran baseline experiments and generated behavior findings, invariants, limitations and matrix.
18. Reviewed boundaries and corrected defects in offline packaging, immutable operation models, CLI reset invocation, compact export keys and checkpoint/action exit-code separation.

The user then requested and authorized the optional Forgejo PR extension. Researched
and pinned Forgejo, added the separate local profile and hosted adapter, verified
real PR publication/rebase/review/merge, added an optional CI job, and regenerated
the same Phase 1 reports. The API approval value and asynchronous merge-readiness
boundary are checked explicitly; no GitHub-equivalence assumption is encoded.

19. Stop after the verified harness, evidence, architecture review and PHASE-1-REPORT.md.
No curriculum implementation, lessons, cheatsheets or syllabus were started.
