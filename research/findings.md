# Generated findings

Only PASS assertions below are reproduced observations. Exploratory fixture observations are not universal invariants.

## add-add — PASS / EXPLORATORY

Evidence: [artifacts/evidence/add-add/20260925T131938.861348Z](../artifacts/evidence/add-add/20260925T131938.861348Z/summary.md)

- rebase command completed
- conflict encoded in jj-specific Git headers
- undo restores conflicted source
- change ID remains stable
- parent relationship

## bookmark — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/bookmark/20260925T132001.379895Z](../artifacts/evidence/bookmark/20260925T132001.379895Z/summary.md)

- conflicted bookmark push rejected
- explicit target resolves bookmark
- main bookmark conflicted
- file conflict state

## context-switch — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/context-switch/20260925T131905.290911Z](../artifacts/evidence/context-switch/20260925T131905.290911Z/summary.md)

- parent relationship
- independent logical changes
- payment Git object exists
- no Git stash
- change remains locatable
- file payment.txt
- Git HEAD detached

## coworker — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/coworker/20260925T131912.403988Z](../artifacts/evidence/coworker/20260925T131912.403988Z/summary.md)

- Bob receives ordinary commit
- bookmark feature
- remote ref refs/heads/feature
- local Git ref

## descendant-rewrite — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/descendant-rewrite/20260925T131907.494541Z](../artifacts/evidence/descendant-rewrite/20260925T131907.494541Z/summary.md)

- change ID remains stable
- Git commit ID rewritten
- change ID remains stable
- Git commit ID rewritten
- change ID remains stable
- Git commit ID rewritten
- parent relationship
- parent relationship

## describe — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/describe/20260925T131900.773043Z](../artifacts/evidence/describe/20260925T131900.773043Z/summary.md)

- change ID remains stable
- Git commit ID rewritten

## detached-head — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/detached-head/20260925T131915.552847Z](../artifacts/evidence/detached-head/20260925T131915.552847Z/summary.md)

- Git HEAD detached
- HEAD is parent

## divergent — PASS / VERSION_SENSITIVE

Evidence: [artifacts/evidence/divergent/20260925T132002.971600Z](../artifacts/evidence/divergent/20260925T132002.971600Z/summary.md)

- fixture converges
- two visible successors

## empty-clone — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/empty-clone/20260925T131854.595174Z](../artifacts/evidence/empty-clone/20260925T131854.595174Z/summary.md)

- .jj exists
- .git exists
- Git repository
- working-copy revision

## evolving-change — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/evolving-change/20260925T131857.097406Z](../artifacts/evidence/evolving-change/20260925T131857.097406Z/summary.md)

- change ID remains stable
- Git commit ID rewritten
- change ID remains stable

## file-directory — PASS / EXPLORATORY

Evidence: [artifacts/evidence/file-directory/20260925T131945.932073Z](../artifacts/evidence/file-directory/20260925T131945.932073Z/summary.md)

- rebase command completed
- conflict encoded in jj-specific Git headers
- undo restores conflicted source
- change ID remains stable
- parent relationship

## file-symlink — PASS / EXPLORATORY

Evidence: [artifacts/evidence/file-symlink/20260925T131948.542555Z](../artifacts/evidence/file-symlink/20260925T131948.542555Z/summary.md)

- rebase command completed
- conflict encoded in jj-specific Git headers
- undo restores conflicted source
- change ID remains stable
- parent relationship

## forgejo-pr — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/forgejo-pr/20260925T132039.627828Z](../artifacts/evidence/forgejo-pr/20260925T132039.627828Z/summary.md)

- PR points at published jj commit
- fetch alone preserves feature ancestry
- change ID remains stable
- Git commit ID rewritten
- parent relationship
- same PR updated
- PR head follows rewrite
- Forgejo branch matches PR
- Bob approval submitted
- PR merged
- Bob receives merged payment
- Bob receives urgent fix
- working change remains locatable

## git-index — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/git-index/20260925T131916.505148Z](../artifacts/evidence/git-index/20260925T131916.505148Z/summary.md)

- file app.conf
- change ID remains stable
- staging was observed

## git-underneath — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/git-underneath/20260925T131917.504442Z](../artifacts/evidence/git-underneath/20260925T131917.504442Z/summary.md)

- change ID remains stable
- Git commit ID rewritten
- object parent matches

## identical-edit — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/identical-edit/20260925T131922.431179Z](../artifacts/evidence/identical-edit/20260925T131922.431179Z/summary.md)

- rebase command completed
- change ID remains stable
- parent relationship
- file conflict state

## many-sided — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/many-sided/20260925T131957.555714Z](../artifacts/evidence/many-sided/20260925T131957.555714Z/summary.md)

- conflict encoded in jj-specific Git headers
- undo restores conflicted source
- file conflict state
- three sides

## mixed-mutation — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/mixed-mutation/20260925T131914.640622Z](../artifacts/evidence/mixed-mutation/20260925T131914.640622Z/summary.md)

- parent relationship
- operation recorded
- file git.txt

## mixed-pending-merge — PASS / VERSION_SENSITIVE

Evidence: [artifacts/evidence/mixed-pending-merge/20260925T131918.518167Z](../artifacts/evidence/mixed-pending-merge/20260925T131918.518167Z/summary.md)

- Git merge unresolved
- Git MERGE_HEAD cleared by import
- file conflict state
- Git text markers remain ordinary content

## modify-delete — PASS / EXPLORATORY

Evidence: [artifacts/evidence/modify-delete/20260925T131935.848848Z](../artifacts/evidence/modify-delete/20260925T131935.848848Z/summary.md)

- rebase command completed
- conflict encoded in jj-specific Git headers
- undo restores conflicted source
- change ID remains stable
- parent relationship

## multiple-files — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/multiple-files/20260925T131929.666358Z](../artifacts/evidence/multiple-files/20260925T131929.666358Z/summary.md)

- rebase command completed
- conflict encoded in jj-specific Git headers
- undo restores conflicted source
- change ID remains stable
- parent relationship
- file conflict state

## multiple-hunks — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/multiple-hunks/20260925T131926.512325Z](../artifacts/evidence/multiple-hunks/20260925T131926.512325Z/summary.md)

- rebase command completed
- conflict encoded in jj-specific Git headers
- undo restores conflicted source
- change ID remains stable
- parent relationship
- file conflict state

## negative-control — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/negative-control/20260925T131919.572585Z](../artifacts/evidence/negative-control/20260925T131919.572585Z/summary.md)

- rebase command completed
- change ID remains stable
- parent relationship
- file conflict state

## new — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/new/20260925T131858.538731Z](../artifacts/evidence/new/20260925T131858.538731Z/summary.md)

- parent relationship
- new logical identity

## new-vs-edit — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/new-vs-edit/20260925T131859.610003Z](../artifacts/evidence/new-vs-edit/20260925T131859.610003Z/summary.md)

- existing identity selected
- file payment.txt

## operation-history — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/operation-history/20260925T131904.290194Z](../artifacts/evidence/operation-history/20260925T131904.290194Z/summary.md)

- operation recorded
- operation description

## partial-resolution — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/partial-resolution/20260925T131932.692892Z](../artifacts/evidence/partial-resolution/20260925T131932.692892Z/summary.md)

- rebase command completed
- conflict encoded in jj-specific Git headers
- undo restores conflicted source
- file conflict state
- resolved hunk retained
- change ID remains stable
- parent relationship
- file conflict state

## push-safety — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/push-safety/20260925T131913.528701Z](../artifacts/evidence/push-safety/20260925T131913.528701Z/summary.md)

- stale push rejected
- remote unchanged after rejection

## rebase — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/rebase/20260925T131910.999842Z](../artifacts/evidence/rebase/20260925T131910.999842Z/summary.md)

- change ID remains stable
- Git commit ID rewritten
- parent relationship
- remote unchanged

## remote-update — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/remote-update/20260925T131909.710583Z](../artifacts/evidence/remote-update/20260925T131909.710583Z/summary.md)

- local ancestry unchanged
- remote changed
- main moved

## rename-modify — PASS / EXPLORATORY

Evidence: [artifacts/evidence/rename-modify/20260925T131941.556453Z](../artifacts/evidence/rename-modify/20260925T131941.556453Z/summary.md)

- rebase command completed
- conflict encoded in jj-specific Git headers
- undo restores conflicted source
- change ID remains stable
- parent relationship

## rename-rename — PASS / EXPLORATORY

Evidence: [artifacts/evidence/rename-rename/20260925T131944.565195Z](../artifacts/evidence/rename-rename/20260925T131944.565195Z/summary.md)

- rebase command completed
- change ID remains stable
- parent relationship

## separate-hunks — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/separate-hunks/20260925T131921.047448Z](../artifacts/evidence/separate-hunks/20260925T131921.047448Z/summary.md)

- rebase command completed
- change ID remains stable
- parent relationship
- file conflict state

## squash — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/squash/20260925T131901.963430Z](../artifacts/evidence/squash/20260925T131901.963430Z/summary.md)

- file parent.txt
- file child.txt
- parent rewritten

## stacked — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/stacked/20260925T131951.327234Z](../artifacts/evidence/stacked/20260925T131951.327234Z/summary.md)

- rebase command completed
- conflict encoded in jj-specific Git headers
- ancestor resolution clears descendant conflicts
- change ID remains stable
- Git commit ID rewritten
- change ID remains stable
- Git commit ID rewritten
- undo restores conflicted source
- change ID remains stable
- parent relationship
- file conflict state

## text-same-line — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/text-same-line/20260925T131923.767745Z](../artifacts/evidence/text-same-line/20260925T131923.767745Z/summary.md)

- rebase command completed
- conflict encoded in jj-specific Git headers
- undo restores conflicted source
- change ID remains stable
- parent relationship
- file conflict state

## undo — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/undo/20260925T131903.087418Z](../artifacts/evidence/undo/20260925T131903.087418Z/summary.md)

- commit restored
- operation recorded

## unresolved-rebase — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/unresolved-rebase/20260925T131954.646047Z](../artifacts/evidence/unresolved-rebase/20260925T131954.646047Z/summary.md)

- rebase command completed
- conflict encoded in jj-specific Git headers
- file conflict state
- logical conflict retains two sides after rebase
- undo restores conflicted source
- change ID remains stable
- parent relationship
- file conflict state

## working-copy — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/working-copy/20260925T131856.117331Z](../artifacts/evidence/working-copy/20260925T131856.117331Z/summary.md)

- change ID remains stable
- Git commit ID rewritten
- file app.conf

## workspace — PASS / DOCUMENTED_AND_REPRODUCED

Evidence: [artifacts/evidence/workspace/20260925T131908.742717Z](../artifacts/evidence/workspace/20260925T131908.742717Z/summary.md)

- second workspace created
- two working copies

