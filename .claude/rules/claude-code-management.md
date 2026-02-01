# Claude Code Management

Claude Code drives the entire development loop. The only human input is **ideas** (via GitHub Issues or chat). Claude Code handles:

1. **Pick issue**: Read experiment idea from a GitHub Issue (`/pick-issue`)
2. **Branch creation**: Create branches from `main` based on the idea
3. **Implementation**: Write/modify code for the atomic feature
4. **Documentation**: Create `docs/<branch-name>.md` for each branch
5. **Commit and push**: After all edits, always `git add`, `git commit`, and `git push` before moving on
6. **Create draft PR**: Open a draft PR linking to the originating issue
7. **Job launch**: Set up and launch WandB jobs for each branch
8. **Incremental results handling**: As each branch finishes, immediately record metrics in `docs/<branch-name>.md` and post to the PR. If clearly worse than baseline, close the PR with a comment and discard early — don't wait for other branches.
9. **Batch winner selection**: Once all branches from the same baseline round have either completed or been discarded, compare surviving branches and select winners.
10. **Code review gate**: Review winner branches before merging. Block merge if blockers found.
11. **Merging**: Merge winning PRs into `main`, close losing PRs
12. **Release**: Create a GitHub Release for the new baseline
13. **Cleanup**: Delete all branches and prepare for the next cycle

The human provides ideas (via GitHub Issues); Claude Code executes the full loop from implementation through evaluation and integration.

## When unsure, ask

If Claude Code is uncertain about any decision — implementation approach, hyperparameter choice, architecture, metric interpretation, which branches to merge, or anything else — **always use the AskUserQuestion tool** to ask the user before proceeding. After receiving the answer, record the decision in the corresponding file:

- Project-level decisions → `CLAUDE.md`
- Branch-specific decisions → `docs/<branch-name>.md`
- Workflow/convention decisions → `.claude/rules/` (relevant rule file)
- Config/env decisions → `.claude/settings.json` or `settings.local.json`

Never guess when the answer matters. Ask, then document.

## Parallel Execution with Agents

When handling multiple experiments simultaneously, use sub-agents (`.claude/agents/`) for parallelism. All agents have web access (WebFetch, WebSearch) and MCP access (Context7) for researching libraries, debugging errors, and verifying best practices.

### How to invoke agents

Use the **Task tool** with `subagent_type` matching the agent name. Run agents in background with `run_in_background: true` for parallelism. Example:

```
Task(subagent_type="experiment-implementer", run_in_background=true,
     prompt="Implement issue #42: increase learning rate to 0.01")
```

Collect results from all background agents before proceeding to the next phase. Report a summary table to the user after each parallel phase.

### Orchestration loop

The main Claude Code session orchestrates the full cycle. Agents handle individual branches; the main session handles sequencing and decisions.

1. **Implement** — Spawn `experiment-implementer` per issue/idea (background). Each works in its own worktree. Wait for all to finish.
2. **Monitor & analyze incrementally** — As each branch's WandB run finishes, spawn `results-analyzer` for that branch. It records metrics to the PR and branch doc via `check-results post-pr`. If worse than baseline, the orchestrator closes the PR early (`gh pr close`) — don't wait for other branches.
3. **Fix failures** — For any branch whose WandB run failed/crashed, spawn `fix-implementer` (background). Each diagnoses, fixes, and relaunches independently. Re-enter step 2 when the relaunch finishes.
4. **Batch winner selection** — Once all branches from the same baseline round have either completed or been discarded, compare surviving branches and select winners.
5. **Code review gate** — Spawn `code-reviewer` per winner branch (parallel). If any blocker issues are found, ask the user before proceeding. Only merge branches that pass review.
6. **Merge** — Run `/merge-winners` with the approved winner list.
7. **Baseline & release** — Run `/run-baseline`, then cleanup.
