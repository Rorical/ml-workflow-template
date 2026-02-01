---
name: run-baseline
description: Run the current main branch as the baseline for experiment comparison
disable-model-invocation: true
allowed-tools: Bash(git *, gh *, python *), Read, Write, Edit
argument-hint: [queue-name]
---

# Run Baseline

Run the `main` branch as the baseline so experiment branches have a reference to compare against.

## Input

$ARGUMENTS

## When to use

- After `/init-project`: establish the first baseline metrics
- After `/merge-winners`: establish the new baseline metrics after merging
- Whenever baseline metrics are missing or stale

## Workflow

1. **Ensure on main and clean**
   - `git checkout main && git pull`
   - Abort if uncommitted changes

2. **Launch baseline job**
   - Read `WANDB_PROJECT`, `WANDB_ENTITY`, `WANDB_QUEUE` from environment
   - Run:
     ```bash
     python .claude/skills/launch-job/launch_job.py \
       --branch main \
       --queue <queue> \
       --project <project> \
       --entity <entity>
     ```

3. **Wait and check**
   - Use `/manage-queue running` to monitor
   - Once finished, use `/check-results summary` to see baseline metrics

4. **Tag the baseline run**
   - Tag with "baseline":
     ```bash
     python .claude/skills/manage-runs/manage_runs.py \
       --project <project> tag --branch main --add "baseline"
     ```

5. **Update CLAUDE.md**
   - Record the baseline metrics in the "Current Baseline" section of `CLAUDE.md`
   - Update `docs/baseline-history.md` with the new baseline entry

6. **Commit and push**
   - `git add -A && git commit -m "Update baseline metrics" && git push`

7. **Create GitHub Release**
   - Tag and release the new baseline:
     ```bash
     gh release create baseline-$(date +%Y%m%d) \
       --title "Baseline $(date +%Y-%m-%d)" \
       --notes-file docs/baseline-history.md \
       --target main
     ```
   - The release provides a permanent reference point for this baseline

8. **Check for regression**
   - Compare new baseline metrics against the previous baseline (from prior release or baseline-history.md)
   - If any key metrics regressed, warn the user and suggest `/rollback-baseline`

## Notes

- Baseline runs use the `main` branch with default hyperparameters from `main.py`
- The `check-results compare` and `report` commands compare experiment branches against the latest `main` run
- Re-run baseline after every merge cycle to keep metrics current
- If regression is detected, use `/rollback-baseline` to revert to the previous baseline

## Failure Handling

If the baseline run crashes or fails:

1. Diagnose with `check-results diagnose --branch main`
2. Fix the issue directly on `main` (this is the only case where `main` is edited directly)
3. `git add`, `git commit`, `git push`
4. Relaunch the baseline job (repeat step 2 of the workflow above)
5. Do **not** proceed with experiments until a successful baseline is established
