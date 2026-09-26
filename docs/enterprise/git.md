# Payment service: GIT command lane

Run sections in order in one **lab shell**. Start a separate shell for the
other lane. These are local Git transport rehearsals, not hosted PR approvals.
Each lane creates its own sandbox and keeps it for inspection.

## 0. Prepare the payment service

```sh
# Create a fresh sandbox; both remotes are local bare Git repositories.
ROOT=$(mktemp -d)
git init --bare --initial-branch=main "$ROOT/origin.git"
git init --bare --initial-branch=main "$ROOT/forgejo.git"
git init --initial-branch=main "$ROOT/payment"
cd "$ROOT/payment"
git config user.name Alice
git config user.email alice@example.test
printf 'amount=10
' > payment.txt
git add payment.txt
git commit -m 'feat: seed payment service'
git remote add origin "$ROOT/origin.git"
git remote add forgejo "$ROOT/forgejo.git"
git push -u origin main
BASE=$(git rev-parse HEAD)
```

## 1. Small PRs: feature branches and trunk-based delivery

```sh
# A short branch keeps the review small; ship behavior behind a flag.
git switch -c payment-flag main
printf 'enabled=false
' > feature-flag.txt
git add feature-flag.txt
git commit -m 'feat(payment): add disabled rollout flag'
git push origin payment-flag
# Local integration rehearsal only: a real protected main uses an approved PR.
git switch main
git merge --ff-only payment-flag
git push origin main
test "$(cat feature-flag.txt)" = 'enabled=false'
```

## 2. Stacked reviews and automatic descendant rebasing

```sh
# Payment validation is the base review; receipt depends on it.
git switch -c validation main
printf 'reject_zero=true
' > validation.txt
git add validation.txt
git commit -m 'fix(payment): reject zero'
OLD=$(git rev-parse HEAD)
git switch -c receipt
printf 'receipt=true
' > receipt.txt
git add receipt.txt
git commit -m 'feat(receipt): add receipt'
git switch validation
printf 'reject_negative=true
' >> validation.txt
git add validation.txt
git commit --amend --no-edit
# Move only the child commits from the old base to its replacement.
git switch receipt
git rebase --onto validation "$OLD"
git push origin validation receipt
test "$(git rev-parse HEAD^)" = "$(git rev-parse validation)"
```

## 3. Release branches, hotfixes and backports

```sh
# Cut a maintenance line before unrelated work lands on main.
git branch release-1 main
git switch main
printf 'next=true
' > next-version.txt
git add next-version.txt
git commit -m 'feat: begin next version'
printf 'rounding=safe
' > rounding.txt
git add rounding.txt
git commit -m 'fix(payment): correct rounding'
FIX=$(git rev-parse HEAD)
git switch -c backport release-1
git cherry-pick "$FIX"
# Verify the fix without accidentally bringing in the next-version feature.
test -f rounding.txt
test ! -f next-version.txt
git push origin main backport
```

## 4. GitFlow: develop, release, main and hotfix propagation

```sh
# Start this policy demonstration at the known baseline.
git switch -c develop "$BASE"
git switch -c checkout-feature
printf 'checkout=v2
' > checkout.txt
git add checkout.txt
git commit -m 'feat: checkout v2'
git switch develop
git merge --no-ff checkout-feature -m 'merge: checkout into develop'
git switch -c release-2
printf 'version=2.0
' > version.txt
git add version.txt
git commit -m 'chore: stabilize release 2'
# A separate production ref models GitFlow main for this exercise.
git switch -c production "$BASE"
git merge --no-ff release-2 -m 'release: 2.0'
git switch develop
git merge --no-ff release-2 -m 'merge: release fixes into develop'
git switch -c hotfix production
printf 'security=fixed
' > security.txt
git add security.txt
git commit -m 'fix: production security issue'
git switch production
git merge --no-ff hotfix -m 'release: hotfix'
git switch develop
git merge --no-ff hotfix -m 'merge: hotfix into develop'
test "$(git show production:security.txt)" = 'security=fixed'
test "$(git show develop:security.txt)" = 'security=fixed'
```

## 5. Forks and selective publication to two remotes

```sh
# Treat origin as upstream and forgejo as the writable contribution destination.
git switch -c contribution main
printf 'timeout=30
' > timeout.txt
git add timeout.txt
git commit -m 'fix: payment timeout'
git push forgejo contribution
# Publication to forgejo must not create the branch on origin.
test -z "$(git ls-remote --heads origin contribution)"
test -n "$(git ls-remote --heads forgejo contribution)"
```

## 6. Environment promotion and GitOps-style desired state

```sh
# A fake artifact identifier models a build digest; no deployment is performed.
git switch -c promotion main
mkdir -p environments/staging environments/production
printf 'payment-build-001
' > environments/staging/artifact.txt
cp environments/staging/artifact.txt environments/production/artifact.txt
git add environments
git commit -m 'deploy: promote tested payment artifact'
PROMOTION=$(git rev-parse HEAD)
# A forward revert preserves an audit trail, instead of moving a release tag.
git revert --no-edit "$PROMOTION"
test ! -e environments/production/artifact.txt
```

```sh
# Inspect the final history; exit returns to the host.
git log --all --graph --oneline
exit
```
