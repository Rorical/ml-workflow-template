---
name: pick-issue
description: Pick a GitHub issue as an experiment idea and start the experiment workflow
disable-model-invocation: true
allowed-tools: Bash(gh *, git *, python *), Read, Edit, Write, Glob, Grep
argument-hint: [issue-number]
---

# Pick Issue

Read a GitHub issue, extract the experiment idea, and start the full experiment workflow.

## Input

Issue number: $ARGUMENTS

## Workflow

1. **Read the issue**
   ```bash
   gh issue view <issue-number>
   ```
   Extract:
   - Title (used for branch name)
   - Body (the experiment idea/description)
   - Labels (for context)

2. **Derive branch name**
   - Format: `issue-<number>-<short-description>`
   - Example: `issue-42-increase-learning-rate`
   - Keep it concise, use `-` separators

3. **Comment on the issue**
   ```bash
   gh issue comment <issue-number> --body "Starting experiment on branch \`<branch-name>\`"
   ```

4. **Add label to issue**
   ```bash
   gh issue edit <issue-number> --add-label "experiment:in-progress"
   ```

5. **Run the /new-experiment workflow**
   - Use the issue body as the idea
   - Use the derived branch name
   - Follow all steps in `/new-experiment`:
     - Ensure `main` is up to date (`git checkout main && git pull`)
     - Create branch and worktree from `main` via `git worktree add .worktrees/<branch-name> -b <branch-name>`
     - Implement inside `.worktrees/<branch-name>/`
     - Write docs, commit, push, create draft PR
   - In the draft PR, include `Closes #<issue-number>` to link the issue

6. **Update issue comment**
   ```bash
   gh issue comment <issue-number> --body "Draft PR created: <pr-url>\nBranch: \`<branch-name>\`\nWorktree: \`.worktrees/<branch-name>/\`\nReady to launch with \`/launch-job\`"
   ```

## Rules

- Always link the PR to the issue with `Closes #<number>`
- Always comment on the issue with progress updates
- Branch name must include the issue number for traceability
- Branches are always created from the current `main` (newest baseline)
- If the issue is unclear, use AskUserQuestion to clarify before implementing
