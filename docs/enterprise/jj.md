# Payment service: JJ command lane

Run sections in order in one **lab shell**. Start a separate shell for the
other lane. These are local Git transport rehearsals, not hosted PR approvals.
Each lane creates its own sandbox and keeps it for inspection.

## 0. Prepare the payment service

```sh
# Same application and remote topology, in a separate disposable sandbox.
ROOT=$(mktemp -d)
git init --bare --initial-branch=main "$ROOT/origin.git"
git init --bare --initial-branch=main "$ROOT/forgejo.git"
jj git init "$ROOT/payment"
cd "$ROOT/payment"
printf 'amount=10
' > payment.txt
jj describe -m 'feat: seed payment service'
jj bookmark create main -r @
jj git remote add origin "$ROOT/origin.git"
jj git remote add forgejo "$ROOT/forgejo.git"
jj git push --remote origin --bookmark main
BASE=$(jj log -r main --no-graph -T commit_id)
```

## 1. Small PRs: feature branches and trunk-based delivery

```sh
# Work first; add a bookmark only when this change is ready for review.
jj new main -m 'feat(payment): add disabled rollout flag'
printf 'enabled=false
' > feature-flag.txt
jj bookmark create payment-flag -r @
jj git push --remote origin --bookmark payment-flag
# Rehearse a fast-forward locally; production main still requires its PR gates.
jj bookmark set main -r payment-flag
jj git push --remote origin --bookmark main
test "$(cat feature-flag.txt)" = 'enabled=false'
```

## 2. Stacked reviews and automatic descendant rebasing

```sh
# Two changes form a stack; each gets its own review bookmark.
jj new main -m 'fix(payment): reject zero'
printf 'reject_zero=true
' > validation.txt
jj bookmark create validation -r @
jj new -m 'feat(receipt): add receipt'
printf 'receipt=true
' > receipt.txt
jj bookmark create receipt -r @
# Rewrite the parent: jj automatically rebases its local child.
jj edit validation
printf 'reject_negative=true
' >> validation.txt
jj status
jj edit receipt
jj git push --remote origin --bookmark validation --bookmark receipt
test "$(jj log -r 'receipt-' --no-graph -T commit_id)" = "$(jj log -r validation --no-graph -T commit_id)"
```

## 3. Release branches, hotfixes and backports

```sh
# Keep a stable release bookmark, then evolve main separately.
jj bookmark create release-1 -r main
jj new main -m 'feat: begin next version'
printf 'next=true
' > next-version.txt
jj new -m 'fix(payment): correct rounding'
printf 'rounding=safe
' > rounding.txt
jj bookmark create rounding-fix -r @
jj bookmark set main -r @
# Duplicate the patch onto the release base; it gets a new change ID.
jj duplicate rounding-fix -o release-1
jj bookmark create backport -r 'description(substring:"correct rounding") & children(release-1)'
jj edit backport
test -f rounding.txt
test ! -f next-version.txt
test "$(jj log -r backport --no-graph -T change_id)" != "$(jj log -r rounding-fix --no-graph -T change_id)"
jj git push --remote origin --bookmark main --bookmark backport
```

## 4. GitFlow: develop, release, main and hotfix propagation

```sh
# Same branch roles; bookmarks name the integration endpoints.
jj bookmark create develop -r "$BASE"
jj new develop -m 'feat: checkout v2'
printf 'checkout=v2
' > checkout.txt
jj bookmark create checkout-feature -r @
# Multiple parents create an explicit merge commit in jj.
jj new develop checkout-feature -m 'merge: checkout into develop'
jj bookmark set develop -r @
jj new develop -m 'chore: stabilize release 2'
printf 'version=2.0
' > version.txt
jj bookmark create release-2 -r @
jj new "$BASE" release-2 -m 'release: 2.0'
jj bookmark create production -r @
jj new develop release-2 -m 'merge: release fixes into develop'
jj bookmark set develop -r @
jj new production -m 'fix: production security issue'
printf 'security=fixed
' > security.txt
jj bookmark create hotfix -r @
jj new production hotfix -m 'release: hotfix'
jj bookmark set production -r @
jj new develop hotfix -m 'merge: hotfix into develop'
jj bookmark set develop -r @
test "$(jj file show -r production security.txt)" = 'security=fixed'
test "$(jj file show -r develop security.txt)" = 'security=fixed'
```

## 5. Forks and selective publication to two remotes

```sh
# Fetch canonical history explicitly, then publish only to the second host.
jj git fetch --remote origin
jj new main@origin -m 'fix: payment timeout'
printf 'timeout=30
' > timeout.txt
jj bookmark create contribution -r @
jj git push --remote forgejo --bookmark contribution --dry-run
jj git push --remote forgejo --bookmark contribution
test -z "$(git ls-remote --heads origin contribution)"
test -n "$(git ls-remote --heads forgejo contribution)"
```

## 6. Environment promotion and GitOps-style desired state

```sh
# Source history and deployed artifact identity are different things.
jj new main -m 'deploy: promote tested payment artifact'
mkdir -p environments/staging environments/production
printf 'payment-build-001
' > environments/staging/artifact.txt
cp environments/staging/artifact.txt environments/production/artifact.txt
jj bookmark create promotion -r @
# Revert creates a new change; it does not erase deployment history.
jj revert -r promotion -o promotion
jj edit 'children(promotion)'
test ! -e environments/production/artifact.txt
```

```sh
# Inspect the final history; exit returns to the host.
jj log -r 'all()'
exit
```
