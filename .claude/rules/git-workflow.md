# Git Workflow

The `main` branch is always the current baseline. The baseline improves over time through an iterative branching process:

1. **Ideas via GitHub Issues or chat**: Experiment ideas are tracked as GitHub Issues (`/pick-issue`) or provided directly in chat (`/new-experiment`). Issues are preferred for traceability but not required.
2. **Branching from main**: All experiment branches are created from the current `main` (newest baseline). Each branch is an atomic feature addition — one logical change (hyperparameter tweak, new layer, data augmentation method, loss function swap, etc.). If two changes are independent, they go on separate branches.
3. **Branch naming**: Use clear, descriptive names with `-` concatenated words. If from an issue, prefix with `issue-<number>-` (e.g., `issue-42-increase-learning-rate`).
4. **Worktrees**: Each experiment branch gets its own git worktree in `.worktrees/<branch-name>/`. This allows multiple experiments to be developed in parallel without switching branches. The main repo directory always stays on `main`.
5. **Atomic commits**: Each branch develops exactly one atomic feature. Multiple commits within a branch should only be the initial implementation and subsequent bug fixes. After all code edits are done, always commit and push.
6. **Branch documentation**: Every branch requires a descriptive document at `docs/<branch-name>.md` (inside the worktree) providing a complete review of the change for future reference.
7. **Draft PR**: After pushing a branch, always create a draft PR via `gh pr create --draft`. Link to the originating issue with `Closes #<number>`.
8. **Commit and push**: At the end of any work on a branch (implementation, bug fixes, doc updates), always `git add`, `git commit`, and `git push` from inside the worktree. The remote must be up to date before launching jobs or switching context.
9. **Incremental evaluation**: As each branch's WandB run finishes, post results to the PR via `check-results post-pr` and record metrics in `docs/<branch-name>.md`. If a branch is clearly worse than baseline, close the PR immediately with a comment and discard — don't wait for the full batch.
10. **Batch winner selection**: Once all branches from the same baseline round have either completed or been discarded, compare surviving branches and select winners. Winners are merged via `gh pr merge`. Losing PRs are closed with a comment. All winning branches merge into `main` to form a new baseline.
11. **Issue labels**: Issues get `experiment:in-progress` when picked (`/pick-issue`). After the cycle completes (merge or close), update to `experiment:done`.
12. **Release**: After merging, create a GitHub Release for the new baseline via `gh release create`.
13. **Reset**: After merging, all worktrees are removed (`git worktree remove`), all branches are deleted, and `git worktree prune` is run. The cycle repeats for further refinement.
