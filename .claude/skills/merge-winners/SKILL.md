---
name: merge-winners
description: Merge winning experiment branches into main via PRs and clean up all branches
disable-model-invocation: true
allowed-tools: Bash(git *, gh *, python *), Read, Edit, Write, Glob, Grep
argument-hint: [branch1,branch2,...] or "auto" to use check-results report
---

# Merge Winners

Merge winning branches into `main` via GitHub PRs, then clean up all experiment branches.

## Input

Winner branches: $ARGUMENTS

If "auto" is passed, first run the report to determine winners:

```bash
python .claude/skills/check-results/check_results.py report
```

## Workflow

### Phase 1: Validate

1. **Confirm winners**
   - List the winning branches and their key metrics
   - List the losing branches that will be discarded
   - Ask user for confirmation before proceeding

2. **Pre-merge checks**
   - Ensure `main` is up to date: `git checkout main && git pull`
   - For each winner branch, verify it has a finished WandB run
   - Check for merge conflicts between winners: attempt `git merge --no-commit --no-ff <branch>` then `git merge --abort` for each

### Phase 2: Code Review Gate

3. **Review each winner branch**
   - Spawn `code-reviewer` agent per winner branch (parallel via Task tool with `run_in_background: true`)
   - Each agent diffs the branch against `main`, reads modified files, and checks for bugs, security issues, breaking changes, and missing docs
   - Collect all review results
   - If any review has **blocker** severity issues: stop and ask the user whether to proceed, fix, or discard the branch
   - Only branches that pass review proceed to merge

### Phase 3: Merge via PRs

4. **Post final results to all PRs**
   - For each branch (winner and loser):
     ```bash
     python .claude/skills/check-results/check_results.py post-pr --branch <branch-name>
     ```

5. **Mark winning PRs as ready**
   - For each winner:
     ```bash
     gh pr ready <pr-number>
     gh pr edit <pr-number> --add-label "experiment:winner"
     ```

6. **Merge winning PRs one by one**
   - For each winning branch (in order):
     ```bash
     gh pr merge <pr-number> --merge --subject "Merge <branch-name>: <short description>"
     ```
   - If conflicts occur, Claude must **manually resolve them**:
     - `git checkout main && git pull`
     - `git merge <branch-name>`
     - Read both versions of the conflicting file
     - Understand the intent of each branch's change
     - Combine both changes logically (both features should work together)
     - If two branches modify the same function/block, integrate both modifications
     - If changes are fundamentally incompatible, stop and ask the user which to prioritize
     - After resolving: `git add <files>` and `git commit` and `git push`
   - Pull main after each merge: `git pull origin main`

7. **Verify merged baseline**
   - `git checkout main && git pull`
   - Run `python -c "from src.train import train; from src.data import load_dataset; print('OK')"` to check imports
   - Check that `main.py` entry point is intact
   - If verification fails, fix the issue and commit before continuing

### Phase 4: Close losers

8. **Close losing PRs**
   - For each losing branch:
     ```bash
     gh pr close <pr-number> --comment "Experiment did not outperform baseline or other branches. Closing."
     gh pr edit <pr-number> --add-label "experiment:loser"
     ```

### Phase 5: Cleanup

9. **Remove all worktrees and branches**
   - Remove all experiment worktrees:
     ```bash
     git worktree remove .worktrees/<branch-name> --force
     ```
     Repeat for every experiment branch (winners and losers).
   - Winners' remote branches are already deleted by PR merge
   - Delete remaining local branches: `git branch -d <branch>` for each
   - Delete remaining remote branches: `git push origin --delete <branch>` for each
   - Prune stale worktree references: `git worktree prune`

10. **Archive results**
   - Update `docs/baseline-history.md` (create if needed) with:
     - Date of merge
     - Which branches were merged (winners) with PR links
     - Which branches were discarded (losers) with PR links
     - Key metrics of the new baseline
   - Commit and push this doc

### Phase 6: Report

11. **Summary**
    - Print the new baseline state
    - List merged branches and their contributions
    - List discarded branches
    - Confirm ready for next experiment cycle

## Rules

- Always ask for user confirmation before merging
- Never force-push to main
- Merge via `gh pr merge` — keeps PR history clean
- Close losing PRs with explanation comment
- Delete ALL experiment branches after merge (clean slate)
- Document everything in baseline history with PR links
- If merge conflicts are complex or fundamentally incompatible, stop and ask the user
- Claude must resolve conflicts manually by reading and integrating both sides — never blindly accept one side
- After all merges, run `/run-baseline` to establish new baseline metrics
