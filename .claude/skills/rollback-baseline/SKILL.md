---
name: rollback-baseline
description: Revert main to a previous baseline when the current one regresses
disable-model-invocation: true
allowed-tools: Bash(git *, gh *, python *), Read, Edit, Write, Glob, Grep, AskUserQuestion
argument-hint: [previous-release-tag] or "auto" to detect regression
---

# Rollback Baseline

Revert `main` to a previous baseline when the newly merged baseline shows regression in key metrics.

## Input

$ARGUMENTS

- Pass a release tag (e.g., `baseline-20260131`) to revert to that specific baseline.
- Pass `auto` to compare the current baseline against the previous one and revert if regression is detected.

## When to use

- After `/run-baseline` shows worse metrics than the previous baseline
- When a merge introduced a bug that degrades performance
- When the user notices regression and wants to undo the last merge cycle

## Workflow

### Phase 1: Detect Regression

1. **Get current and previous baseline metrics**
   - List releases to find the two most recent baselines:
     ```bash
     gh release list --limit 5
     ```
   - Fetch the current baseline run (tagged "baseline" on `main`):
     ```bash
     python .claude/skills/check-results/check_results.py summary
     ```
   - Read previous baseline metrics from the prior release notes or `docs/baseline-history.md`

2. **Compare metrics**
   - For each key metric, check if the new baseline is worse:
     - Loss-like metrics (loss, error, mse, etc.): regression if **increased**
     - Accuracy-like metrics: regression if **decreased**
   - Print comparison table showing old vs new vs delta

3. **Confirm with user**
   - Show the regression summary
   - Ask user to confirm rollback
   - If not regressed or user declines, abort

### Phase 2: Revert

4. **Identify the target commit**
   - Get the commit hash of the previous release tag:
     ```bash
     git rev-list -n 1 <previous-release-tag>
     ```

5. **Create a revert**
   - Do NOT use `git reset --hard` (destructive)
   - Instead, create a revert commit that undoes the merge:
     ```bash
     git checkout main && git pull
     git revert --no-commit HEAD...<previous-tag>
     git commit -m "Revert to <previous-tag>: baseline regression detected"
     ```
   - If the revert is complex (multiple merge commits), revert each merge individually in reverse order:
     ```bash
     git revert -m 1 <merge-commit-hash>
     ```

6. **Push reverted main**
   - `git push origin main`

### Phase 3: Document

7. **Create a GitHub Issue**
   ```bash
   gh issue create \
     --title "Baseline regression: reverted to <previous-tag>" \
     --body "## Regression Detected

   The baseline after merging showed regression in key metrics.

   ### Metrics Comparison
   | Metric | Previous Baseline | New Baseline | Delta |
   |--------|------------------|--------------|-------|
   | ... | ... | ... | ... |

   ### Action Taken
   - Reverted main to \`<previous-tag>\`
   - All changes from the last merge cycle have been undone

   ### Branches That Were Merged
   - (list from baseline-history.md)

   ### Next Steps
   - Investigate which merged branch caused the regression
   - Re-run experiments individually to isolate the problem
   - Consider merging winners one at a time with baseline runs between each
   " --label "regression,baseline"
   ```

8. **Update baseline history**
   - Add a rollback entry to `docs/baseline-history.md`:
     - Date of rollback
     - Which baseline was reverted from/to
     - Regression metrics
     - Link to the GitHub Issue
   - Commit and push

9. **Re-tag baseline**
   - Tag the current baseline run on the reverted main:
     ```bash
     python .claude/skills/manage-runs/manage_runs.py tag --branch main --add "baseline,reverted"
     ```

### Phase 4: Report

10. **Summary**
    - Print what was reverted and why
    - Link to the GitHub Issue
    - Suggest next steps:
      - Re-run each previously merged branch individually
      - Use `/run-baseline` between each merge to catch regressions early
      - Consider merging one winner at a time in future cycles

## Rules

- Never use `git reset --hard` on main — always use `git revert` to preserve history
- Always ask user confirmation before reverting
- Always create a GitHub Issue documenting the regression
- Always update baseline history with the rollback
- After rollback, the previous baseline metrics become the current baseline again
