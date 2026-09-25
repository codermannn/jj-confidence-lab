# Verified fixture invariants

Documentation-linked assertions that passed; scope is the named fixture on the pinned toolchain.

- **bookmark**: conflicted bookmark push rejected; explicit target resolves bookmark; main bookmark conflicted; file conflict state.
- **context-switch**: parent relationship; independent logical changes; payment Git object exists; no Git stash; change remains locatable; file payment.txt; Git HEAD detached.
- **coworker**: Bob receives ordinary commit; bookmark feature; remote ref refs/heads/feature; local Git ref.
- **descendant-rewrite**: change ID remains stable; Git commit ID rewritten; change ID remains stable; Git commit ID rewritten; change ID remains stable; Git commit ID rewritten; parent relationship; parent relationship.
- **describe**: change ID remains stable; Git commit ID rewritten.
- **detached-head**: Git HEAD detached; HEAD is parent.
- **empty-clone**: .jj exists; .git exists; Git repository; working-copy revision.
- **evolving-change**: change ID remains stable; Git commit ID rewritten; change ID remains stable.
- **forgejo-pr**: PR points at published jj commit; fetch alone preserves feature ancestry; change ID remains stable; Git commit ID rewritten; parent relationship; same PR updated; PR head follows rewrite; Forgejo branch matches PR; Bob approval submitted; PR merged; Bob receives merged payment; Bob receives urgent fix; working change remains locatable.
- **git-index**: file app.conf; change ID remains stable; staging was observed.
- **git-underneath**: change ID remains stable; Git commit ID rewritten; object parent matches.
- **identical-edit**: rebase command completed; change ID remains stable; parent relationship; file conflict state.
- **many-sided**: conflict encoded in jj-specific Git headers; undo restores conflicted source; file conflict state; three sides.
- **mixed-mutation**: parent relationship; operation recorded; file git.txt.
- **multiple-files**: rebase command completed; conflict encoded in jj-specific Git headers; undo restores conflicted source; change ID remains stable; parent relationship; file conflict state.
- **multiple-hunks**: rebase command completed; conflict encoded in jj-specific Git headers; undo restores conflicted source; change ID remains stable; parent relationship; file conflict state.
- **negative-control**: rebase command completed; change ID remains stable; parent relationship; file conflict state.
- **new**: parent relationship; new logical identity.
- **new-vs-edit**: existing identity selected; file payment.txt.
- **operation-history**: operation recorded; operation description.
- **partial-resolution**: rebase command completed; conflict encoded in jj-specific Git headers; undo restores conflicted source; file conflict state; resolved hunk retained; change ID remains stable; parent relationship; file conflict state.
- **push-safety**: stale push rejected; remote unchanged after rejection.
- **rebase**: change ID remains stable; Git commit ID rewritten; parent relationship; remote unchanged.
- **remote-update**: local ancestry unchanged; remote changed; main moved.
- **separate-hunks**: rebase command completed; change ID remains stable; parent relationship; file conflict state.
- **squash**: file parent.txt; file child.txt; parent rewritten.
- **stacked**: rebase command completed; conflict encoded in jj-specific Git headers; ancestor resolution clears descendant conflicts; change ID remains stable; Git commit ID rewritten; change ID remains stable; Git commit ID rewritten; undo restores conflicted source; change ID remains stable; parent relationship; file conflict state.
- **text-same-line**: rebase command completed; conflict encoded in jj-specific Git headers; undo restores conflicted source; change ID remains stable; parent relationship; file conflict state.
- **undo**: commit restored; operation recorded.
- **unresolved-rebase**: rebase command completed; conflict encoded in jj-specific Git headers; file conflict state; logical conflict retains two sides after rebase; undo restores conflicted source; change ID remains stable; parent relationship; file conflict state.
- **working-copy**: change ID remains stable; Git commit ID rewritten; file app.conf.
- **workspace**: second workspace created; two working copies.
