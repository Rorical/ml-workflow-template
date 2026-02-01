---
name: new-experiment
description: Create a new experiment branch in a worktree with implementation and documentation
disable-model-invocation: true
allowed-tools: Bash(git *, gh *), Read, Edit, Write, Glob, Grep
argument-hint: [idea description]
---

# New Experiment

Create a new experiment branch in a git worktree, implement the idea, and prepare for launch. Using worktrees allows multiple experiments to be developed in parallel without switching branches.

## Input

The user provides an idea: $ARGUMENTS

## Workflow

1. **Ensure main is up to date**
   - From the main repo directory: `git checkout main && git pull`

2. **Create branch and worktree**
   - Derive a clear branch name from the idea using `-` concatenated words (e.g., `increase-learning-rate`, `add-dropout-layer`)
   - Create branch and worktree in one step:
     ```bash
     git worktree add .worktrees/<branch-name> -b <branch-name>
     ```
   - All subsequent work happens inside `.worktrees/<branch-name>/`

3. **Implement the change**
   - Work inside `.worktrees/<branch-name>/`
   - Make the atomic code change in `src/` or `main.py` as needed
   - Keep changes minimal and focused on the single idea
   - Ensure `wandb.config` will capture any new hyperparameters

4. **Write branch documentation**
   - Create `.worktrees/<branch-name>/docs/<branch-name>.md` with:
     - **Hypothesis**: What we expect this change to achieve
     - **Changes**: What was modified and why
     - **Metrics to watch**: Which metrics should improve/change
     - **Rollback risk**: Any concerns about merging this later

5. **Commit and push**
   - From inside the worktree:
     ```bash
     cd .worktrees/<branch-name>
     git add -A
     git commit -m "<description>"
     git push -u origin <branch-name>
     ```

6. **Create draft PR**
   - From inside the worktree:
     ```bash
     gh pr create --draft --title "<branch-name>" --body "$(cat docs/<branch-name>.md)"
     ```
   - If this experiment originated from a GitHub issue, add `Closes #<issue-number>` to the PR body
   - Add label: `gh pr edit --add-label "experiment"`

7. **Report**
   - Summarize what was done
   - Print the PR URL
   - Print the worktree path: `.worktrees/<branch-name>/`
   - Suggest the launch command: `python .claude/skills/launch-job/launch_job.py --branch <branch-name>`

## Rules

- One idea = one branch = one worktree = one atomic change
- Never modify unrelated code
- Branch name must be descriptive and use `-` separators
- Always write `docs/<branch-name>.md` inside the worktree
- Always push before suggesting launch
- Always create a draft PR after pushing
- If from an issue, link with `Closes #<number>`
- The main repo directory always stays on `main` — never switch it to an experiment branch
