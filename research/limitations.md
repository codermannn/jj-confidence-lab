# Generated limitations

- **add-add** (EXPLORATORY): Git cannot interpret jj logical conflicts
- **bookmark** (DOCUMENTED_AND_REPRODUCED): Reference conflict, not a file conflict
- **divergent** (VERSION_SENSITIVE): Experimental converge heuristics; exit success alone does not prove convergence
- **file-directory** (EXPLORATORY): Git cannot interpret jj logical conflicts
- **file-symlink** (EXPLORATORY): Git cannot interpret jj logical conflicts
- **forgejo-pr** (DOCUMENTED_AND_REPRODUCED): Forgejo models PR lifecycle, not GitHub-specific policy or UI.
- **many-sided** (DOCUMENTED_AND_REPRODUCED): Git cannot interpret jj logical conflicts
- **mixed-pending-merge** (VERSION_SENSITIVE): jj import clears pending Git merge state in this fixture but snapshots Git conflict markers as ordinary content, without a jj logical conflict.
- **modify-delete** (EXPLORATORY): Git cannot interpret jj logical conflicts
- **multiple-files** (DOCUMENTED_AND_REPRODUCED): Git cannot interpret jj logical conflicts
- **multiple-hunks** (DOCUMENTED_AND_REPRODUCED): Git cannot interpret jj logical conflicts
- **partial-resolution** (DOCUMENTED_AND_REPRODUCED): Git cannot interpret jj logical conflicts
- **rename-modify** (EXPLORATORY): Git cannot interpret jj logical conflicts
- **stacked** (DOCUMENTED_AND_REPRODUCED): Git cannot interpret jj logical conflicts
- **text-same-line** (DOCUMENTED_AND_REPRODUCED): Git cannot interpret jj logical conflicts
- **unresolved-rebase** (DOCUMENTED_AND_REPRODUCED): Git cannot interpret jj logical conflicts

## Documented boundaries (DOCUMENTED)

Git attributes, hooks, LFS and partial clones are unsupported or incomplete; submodules are not materialized; native jj workspaces differ from git-worktree. See https://docs.jj-vcs.dev/latest/git-compatibility/. These features are not experimentally covered by this harness.

Runtime tests establish only the platform actually recorded. GitHub policies and authentication are outside local bare-remote transport. Simultaneous mutations of one fixture are unsupported; independent tests use independent roots.
