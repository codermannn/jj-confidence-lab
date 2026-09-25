# Publish only the ready payment change

Alice has a ready payment fix and an unfinished receipt experiment. Riley wants
only the payment fix in Forgejo. A bookmark points to the last change to publish:
its ancestors travel with it; descendants and unrelated bookmarks do not.
Selecting a bookmark cannot exclude an unwanted ancestor. Split or rearrange
that history first, then inspect the resulting diff.

## 1. Prepare the hosted fixture — host terminal

```sh
# Create a fresh disposable Forgejo repository and finish its baseline PR.
./lab start
./lab forge run

# Open a shell with access to Forgejo; the ordinary lab shell has no network.
docker compose -f compose.yaml -f compose.forgejo.yaml run --rm --entrypoint bash forge-lab
```

## 2. Create ready and unfinished work — inside that shell

**Predict:** will publishing the parent also publish the unfinished child?

```sh
# Enter the most recently generated fixture; forge run sets /lab/active.
cd "$(cat /lab/active)/alice"

# Enable HTTP only in this disposable shell and use its seeded Alice account.
export GIT_ALLOW_PROTOCOL=file:http
AUTH=$(python -c 'from jj_lab.forge.client import authorization; print(authorization("alice"))')
git config http.http://forgejo:3000/.extraHeader "Authorization: $AUTH"
unset AUTH

# Start an independent follow-up from the merged remote main.
jj git fetch --remote forgejo
jj new main@forgejo -m 'fix(payment): reject zero amounts'
printf 'reject_zero=true\n' > payment-policy.txt
jj status
READY=$(jj log -r @ --no-graph -T 'change_id')
jj bookmark create payment-ready -r "$READY"

# Leave an unfinished child above the ready fix.
jj new -m 'feat(receipt): experiment with layout'
printf 'unfinished layout\n' > receipt-draft.txt
jj bookmark create receipt-wip -r @
jj log -r 'main@forgejo::@'
```

## 3. Preview, publish, and prove the boundary

```sh
# Review exactly what the selected change adds to the remote baseline.
jj diff --from main@forgejo --to payment-ready
jj git push --remote forgejo --bookmark payment-ready --dry-run

# Publish only this named bookmark; leave receipt-wip local.
jj git push --remote forgejo --bookmark payment-ready

# Remote output should contain payment-ready and no receipt-wip branch.
git ls-remote --heads forgejo payment-ready receipt-wip
jj bookmark list --all-remotes
```

Open the repository in Forgejo and create a PR from `payment-ready` to `main`.
The PR includes the payment policy; it excludes the receipt draft. An existing
PR follows subsequent pushes of its same bookmark.

**Teach back:** “I selected a bookmark and a remote. That published the change
and its ancestors, while my unfinished child stayed local.”

## 4. Publish the receipt later

```sh
# Finish the receipt, then explicitly choose its separate review branch.
printf 'layout ready\n' > receipt-draft.txt
jj status
jj git push --remote forgejo --bookmark receipt-wip --dry-run
jj git push --remote forgejo --bookmark receipt-wip
exit
```

Until the payment fix merges, a receipt PR targeting `main` includes both
changes. Target `payment-ready` for a stacked PR, or wait for it to merge and
rebase the receipt onto the updated `main@forgejo` before publishing.

For a repository with both GitHub and Forgejo remotes, always name the intended
remote: `--remote forgejo --bookmark payment-ready` versus
`--remote origin --bookmark main`. Avoid `--all` when publishing selectively.
The GitHub course repository and these generated Forgejo exercises are separate
repositories; publishing the course does not upload the exercise volume.
