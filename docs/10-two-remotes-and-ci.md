# Two remotes, one local graph

Alice's local graph contains all her work. GitHub (`origin`) and local Forgejo
(`forgejo`) each receive only the bookmarks she explicitly publishes. A remote
is an address, not a separate workspace. GitHub remains the canonical main;
Forgejo is the rehearsal destination. The course checkout currently has only
`origin`; the generated lab fixtures have their own Forgejo remote. Do not add
an unrelated generated fixture as a remote of the course checkout.

## Connect the same project to two hosts

For your own application, create an empty repository in local Forgejo. Run
these commands in your application's jj workspace on the host with jj installed.
Replace the URL with the clone URL shown by Forgejo; credentials are requested
by your configured Git credential helper. Inside containers, localhost means
that container, so use the Forgejo service URL instead.

```sh
# Inspect existing addresses before adding the second destination.
jj git remote list
jj git remote add forgejo http://localhost:3080/alice/YOUR-APPLICATION.git

# Fetch the canonical source and make the default push destination explicit.
jj git fetch --remote origin
jj config set --repo git.push origin
jj config set --repo 'revset-aliases."trunk()"' main@origin
```

**Predict:** will a push to Forgejo also update GitHub? No: each push is a
separate publication. These commands are a template; substitute a real ready
change ID from `jj log`.

```sh
# Name one reviewable change, then preview and publish it to the local server.
jj bookmark create payment-ready -r YOUR-READY-CHANGE-ID
jj git push --remote forgejo --bookmark payment-ready --dry-run
jj git push --remote forgejo --bookmark payment-ready

# Publish the same change to GitHub only when you explicitly choose to.
jj git push --remote origin --bookmark payment-ready --dry-run
jj git push --remote origin --bookmark payment-ready
```

The selected revision and its ancestors travel together. Descendants stay local.
If destinations need different content, give separate changes separate bookmark
names. Rewriting a shared change moves its local bookmarks, even if the names
were intended for different hosts; independent remote branches do not make
independent local changes. Inspect every dry run.

## What auto-rebase does

Editing an ancestor automatically rebases its local descendants. That behavior
is independent of how many remotes exist. It neither picks a remote's main for
you nor pushes rewritten commits to either server.

For ordinary advancement of GitHub main, fetch, inspect, then deliberately
rebase your stack onto `main@origin`:

```sh
# Update remote observations and inspect both histories.
jj git fetch --remote origin
jj git fetch --remote forgejo
jj bookmark list --all-remotes
jj log -r 'main@origin | main@forgejo | mutable()'

# Substitute the bottom change of your stack; descendants move with it.
jj rebase -s YOUR-STACK-ROOT -d main@origin
jj status
jj diff -r payment-ready

# Update just the local rehearsal server after resolving any conflicts.
jj git push --remote forgejo --bookmark payment-ready --dry-run
jj git push --remote forgejo --bookmark payment-ready
```

Use the log expression only once Forgejo has a main branch. Fetch can also
import remote rewrites and abandon commits no longer reachable remotely; that
can affect descendants. It is not an unconditional "leave my graph untouched"
operation. Inspect the output and `jj op log` after unexpected remote changes.

If Forgejo main diverges from GitHub main, choose the intended integration base
explicitly. Do not track both remote mains as one local main unless you want
that coupling: independent movement can produce a conflicted bookmark. Prefer
tracking canonical `main@origin` only. Fetching an untracked `main@forgejo`
still lets you inspect it and explicitly rebase onto it.

**Teach back:** “Rewriting a parent updates local children. Publishing updates
one selected remote. Fetching two mains does not choose my integration policy.”

## CI and protected main

GitHub Actions is YAML, while jj handles revision inspection within each job.
The shared `jj-checkout` action uses the pinned lab jj binary to initialize a
colocated workspace and verifies its parent equals GitHub's exact event SHA.
For PRs, this is the synthetic merge revision supplied by GitHub, so tests
exercise the proposed integration. Bootstrap download uses `actions/checkout`
with credential persistence disabled. CI never rebases or pushes reviewed work.

Main requires a PR, an up-to-date branch, resolved conversations, and all four
checks: quality, harness-tests, scenario-tests, and forgejo-tests. Admins are
subject to these rules; force pushes and deletion are blocked. Review approvals
are set to zero so a solo maintainer can merge their own passing PR. This is
GitHub protection; local jj immutability and Forgejo branch protection are
separate controls. The generated Forgejo repositories remain disposable labs.

Sources: [jj multiple remotes](https://docs.jj-vcs.dev/latest/guides/multiple-remotes/)
and [fetch semantics](https://docs.jj-vcs.dev/latest/cli-reference/#jj-git-fetch).
