# VisualJJ scenario map

VisualJJ’s learning pages emphasize jj’s mental model, stacked PRs, PR
evolution/interdiffs, and multiple workspaces for parallel agents. The lab can
exercise the underlying jj and Git mechanics, but it does not reproduce
VisualJJ’s editor UI or GitHub-specific automation.

| Scenario VisualJJ discusses | Covered here | Run this | Boundary |
| --- | --- | --- | --- |
| Working-copy changes without staging | Yes | `./lab scenario run working-copy` | CLI and evidence only |
| Stable change identity across rewrites | Yes | `./lab scenario run descendant-rewrite` | Verifies jj identity, not VisualJJ UI |
| Split a broad change into reviewable pieces | Yes | `./lab scenario run split` | File-based split; interactive hunk selection is not automated |
| Fold a child fix into its parent | Yes | `./lab scenario run squash` | Local graph and file assertions |
| Touch up one revision with a diff editor | Yes | `./lab scenario run diffedit` | Uses a no-op editor in the headless container |
| Absorb a focused follow-up into an ancestor | Yes | `./lab scenario run absorb` | Non-interactive whole-file fixture |
| Find the first bad revision by binary search | Yes | `./lab scenario run bisect` | Deterministic shell test over a local history |
| Stacked changes and descendant rebasing | Yes | `./lab conflict run stacked` | Local graph; no automatic PR stack metadata |
| Edit a lower stack layer and carry descendants | Yes | `./lab scenario run descendant-rewrite` | One local graph; publishing policy is separate |
| Multiple directories/workspaces | Yes | `./lab scenario run workspace` | No agent launcher or editor integration |
| Rebase after remote `main` moves | Yes | `./lab scenario run remote-update` and `rebase` | Local bare remote plus Forgejo workflow |
| Safe publication after a rewrite | Yes | `./lab scenario run push-safety` | Harness guardrails, not VisualJJ push UI |
| Real PR updated after jj rebase | Yes | `./lab forge run` | Local Forgejo PR, not GitHub native stacked PRs |
| Reviewer sees only what changed since last review | Partly | `./lab scenario run review-evolution` and `./lab forge run` | Evidence has three review checkpoints; no interdiff panel |
| Automatic PR retargeting and stack grouping | No | — | VisualJJ/GitHub-specific behavior |
| Parallel AI agents shown in one control tree | Partly | `./lab scenario run workspace` | Workspaces are covered; agent lifecycle is not |

## What “covered” means

The lab creates real repositories, runs real Git/jj commands, records command
output and snapshots, and asserts semantic invariants. A passing scenario is
evidence for the named fixture and pinned toolchain. It is not evidence that a
VisualJJ UI feature, GitHub policy, or Forgejo policy behaves identically.

## Suggested learning order

```sh
# Learn the graph and rewrite behavior first.
./lab scenario run working-copy
./lab scenario run descendant-rewrite
./lab conflict run stacked
./lab scenario run split
./lab scenario run squash
./lab scenario run absorb
./lab scenario run diffedit

# Add remote movement, safe publication, and multiple workspaces.
./lab scenario run remote-update
./lab scenario run rebase
./lab scenario run push-safety
./lab scenario run workspace

# Finish with the hosted PR lifecycle.
./lab forge run
```

VisualJJ’s own material describes stacked PR maintenance, PR evolution, and
parallel workspaces in more detail:

- [Jujutsu in 5 minutes](https://www.visualjj.com/learn/jj-in-5)
- [Stacked PRs without cascading rebases](https://www.visualjj.com/learn/stacked-prs-with-jujutsu)
- [Re-review without re-reading](https://www.visualjj.com/learn/re-review-without-re-reading)
- [Multiple AI Agents, One Repo](https://www.visualjj.com/learn/parallel-ai-agents)
