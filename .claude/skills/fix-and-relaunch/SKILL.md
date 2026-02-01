---
name: fix-and-relaunch
description: Diagnose a failed experiment run, fix the code, and re-launch
disable-model-invocation: true
allowed-tools: Bash(git *, gh *, python *), Read, Edit, Write, Glob, Grep
argument-hint: [branch-name]
---

# Fix and Relaunch

Error recovery workflow: diagnose a failed/crashed WandB run, fix the issue on the branch, and re-launch.

## Input

Branch name: $ARGUMENTS

## Workflow

### Phase 1: Diagnose

1. **Navigate to the worktree**
   - `cd .worktrees/<branch-name>`
   - If the worktree doesn't exist (was cleaned up), recreate it:
     ```bash
     git worktree add .worktrees/<branch-name> <branch-name>
     ```
   - Pull latest: `git pull`

2. **Run diagnosis** (from main repo or worktree)
   ```bash
   python .claude/skills/check-results/check_results.py diagnose --branch <branch-name>
   ```
   This shows:
   - Run config and summary
   - Last logged history steps (where it stopped)
   - Log tail from `output.log` (error messages, tracebacks)

3. **Analyze the failure**
   - Identify the root cause from the log tail
   - Common issues:
     - Import errors → missing dependency in `requirements.txt`
     - OOM → reduce batch size or model size
     - NaN loss → learning rate too high, data issue
     - Dataset not found → artifact name mismatch
     - Config key error → missing default in `DEFAULTS` dict

### Phase 2: Fix

4. **Make the fix**
   - Edit files inside `.worktrees/<branch-name>/` (`src/`, `main.py`, etc.)
   - Keep the fix minimal — only address the diagnosed issue

5. **Update branch documentation**
   - Add a "Fixes" section to `.worktrees/<branch-name>/docs/<branch-name>.md` noting what failed and what was fixed

6. **Commit and push** (from inside the worktree)
   ```bash
   cd .worktrees/<branch-name>
   git add -A
   git commit -m "Fix: <description of fix>"
   git push
   ```

7. **Comment on PR**
   - Post a comment on the branch's PR noting the failure and fix:
     ```bash
     gh pr comment --body "**Fix applied:** <description>\n\nDiagnosis: <root cause>\nRe-launching job."
     ```

### Phase 3: Re-launch

8. **Re-launch the job**
   ```bash
   python .claude/skills/launch-job/launch_job.py --branch <branch-name>
   ```

9. **Monitor**
   - Check that the new run starts:
     ```bash
     python .claude/skills/manage-queue/manage_queue.py running
     ```
   - Optionally clean up the old failed run:
     ```bash
     python .claude/skills/manage-runs/manage_runs.py delete --branch <branch-name>
     ```
     (This deletes only the latest failed run; the new run will take its place)

### Phase 4: Verify

10. **Check early metrics**
   - After the run has logged a few steps, verify it's progressing:
     ```bash
     python .claude/skills/check-results/check_results.py history --branch <branch-name> --rows 10
     ```
   - If it fails again, repeat from Phase 1

## Rules

- Always diagnose before fixing — don't guess
- Keep fixes minimal and focused on the error
- Document every fix in the branch doc
- Always commit and push before re-launching
- Clean up failed runs to avoid confusion in results
