# Jujutsu from first principles

This is a compact path through the lab. Run each example in a disposable clone. The point is to predict what Jujutsu will do before running the command.

The two reference tutorials describe the command surface; this guide supplies the order and the mental model. The lab can verify the examples with `./lab scenario run <name>`.

## 1. One idea first: your checkout is already a commit

Git makes you think in two things: a commit, plus an uncommitted working tree. Jujutsu starts with one thing: the working copy is a revision named `@`. Files on disk are its current snapshot.

```sh
# Start the disposable lab and enter Alice's generated workspace.
./lab start

./lab shell

cd "$(cat /lab/active)/alice"

jj status

jj log -r '@ | @-'
```

`@` is the revision you are editing. `@-` is its parent. A revision has a stable **change ID** and a content-derived **commit ID**. Editing files or the description rewrites the commit ID while the change ID stays recognizable.

Try this: edit `README`, run `jj status`, then `jj describe -m "Explain setup"`, and run `jj log`. There is no `git add`, and there is no half-committed working tree to lose.

## 2. Finish one change by moving to another

`jj new` creates a child revision and moves `@` there:

```sh
# Create a new child change, then another change on top of it.
jj new -m "Add validation"

# work, test, and revise

jj new -m "Add documentation"
```

The earlier change remains editable. If the documentation was started too early, use `jj edit <change-id>` to return to it. If a small follow-up belongs in its parent, use `jj squash`.

The useful question is no longer “Have I committed?” It is “Which change should receive my next edit?”

## 3. The everyday Git stash problem disappears

Suppose you are halfway through payment validation and a login bug arrives. In Git you might stash, switch, work, pop, and resolve stash conflicts. In jj:

```sh
# Keep payment work in its change while fixing an urgent login issue.
jj new -m "Fix login redirect"

# fix and test the login bug

jj new

jj edit <payment-change-id>
```

The payment change stayed in the graph while you worked on the login change. The lab’s `context-switch` experiment verifies that the unfinished work survives without `git stash`.

Existing Git stashes are still ordinary Git objects. Jujutsu does not automatically turn them into jj changes. Inspect or apply them with Git when needed:

```sh
# Inspect an existing Git stash before importing it into jj.
git stash list

git stash show -p stash@{0}

git stash apply stash@{0}

jj status
```

After applying one, jj snapshots the resulting files into `@`; then describe, squash, or move to a new change. Treat a stash as an import from an older workflow, not as the normal jj parking mechanism.

## 4. Think in a graph, not a branch pointer

Use `jj log` to see the graph and revsets to ask precise questions:

```sh
# Ask the graph precise questions about the current change.
jj log -r '::@'

jj log -r 'bookmarks()'

jj diff -r <change-id>
```

A bookmark is a movable name for a revision and is the Git-facing publication point. Your local work can be anonymous until you are ready to publish it.

## 5. Make history clean after the fact

Because changes are rewritable, you can develop in the order that is convenient and arrange the final stack later:

```sh
# Shape the stack after the work is understood.
jj rebase -s <change> -o <new-parent>

jj squash

jj split <file> -r <change> -m "Focused part"

jj absorb

# Use a configured diff editor for a careful touch-up.
jj diffedit -r <change>

jj describe -m "Precise explanation"
```

If an ancestor changes, descendants are rewritten with it. Their change IDs remain the same, so you can keep referring to the same logical work while commit IDs change. This is the core reason stacked work feels less fragile in jj.

## 6. Sync has two separate verbs: fetch, then rebase

Fetching imports remote objects and bookmarks. It does not silently move your work:

```sh
# Import remote movement, inspect it, then choose a new ancestry.
jj git fetch

jj log -r 'trunk() | @ | ancestors(@)'

jj rebase -s <your-change> -d trunk()
```

This separation lets you inspect upstream first, then choose the exact ancestry change. A stale push is rejected rather than overwriting a remote update; fetch, inspect, rebase, test, and push again.

## 7. Conflicts are data you can carry

Rebase may succeed while producing a conflicted revision. That is deliberate: the graph remains inspectable and descendants remain present.

```sh
# Inspect and resolve a conflict that remains attached to a revision.
jj status

jj resolve --list

# edit the files or use jj resolve

jj squash
```

Resolve the parent conflict, squash the resolution into that change, and inspect descendants. A conflict is a property of a revision, not a command that left the repository in an unknowable temporary mode. The lab covers two-sided, partial, stacked, rename, add/add, and three-sided conflicts.

## 8. Publish a reviewable change

Create or move a bookmark at the change you want reviewers to see, then push it:

```sh
# Publish the logical change through a Git-facing bookmark.
jj bookmark create feature -r <change-id>

jj git push --bookmark feature
```

The Git commit hash may move after review feedback, but the jj change identity remains the same. A Forgejo pull request therefore keeps its review conversation while its head commit is rebased and repushed. In the lab, Alice publishes, Bob pushes an urgent `main` update, Alice fetches/rebases/repushes, Bob approves, and Forgejo merges the PR.

## 9. Maintenance: recover, inspect, and keep work moving

Use the operation log when a command did something you did not intend:

```sh
# Inspect and undo local repository operations.
jj op log

jj undo

jj op restore <operation-id>

jj evolog -r <change-id>
```

The operation log answers “what did the repository do?” The evolution log answers “how did this change become this revision?” Keep descriptions useful, push bookmarks deliberately, and periodically inspect `jj log -r 'trunk()..@'` before syncing.

## 10. Workspaces: related, but not a replacement for changes

`jj workspace add` gives another working directory backed by the same repository history. Use it when two directories must be active at once: for example, one for a release check and one for feature work.

```sh
# Create and inspect a second working directory on the same graph.
jj workspace add ../project-release -r trunk()

jj workspace list
```

Context switching (`jj edit`/`jj new`) changes which revision one directory is showing. A workspace gives you a second directory at the same time. They overlap in reducing “stash this before I do something else,” but solve different problems: changes organize history; workspaces organize simultaneous filesystem views.

## The jj mindset

Before every command, ask three questions:

1. Which revision is `@`, and which change should receive my next edit?
2. Which graph relationship am I changing: content, parentage, bookmark, or remote state?
3. If this goes wrong, can I inspect or undo the operation?

That is the practical switch from Git thinking. Work is continuously captured, history is deliberately shaped, and sharing is an explicit boundary.

## Suggested lab order

`working-copy` → `evolving-change` → `new-vs-edit` → `split` → `squash` → `absorb` → `diffedit` → `context-switch` → `operation-history` → `bisect` → `remote-update` → `rebase` → `push-safety` → `stacked` → `partial-resolution` → `workspace` → `review-evolution` → optional `forgejo-pr`.

Reference reading: [Steve Klabnik’s tutorial](https://steveklabnik.github.io/jujutsu-tutorial/) and the [official Jujutsu tutorial](https://docs.jj-vcs.dev/latest/tutorial/).
