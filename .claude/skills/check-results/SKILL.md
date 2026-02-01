---
name: check-results
description: Fetch and analyze WandB run results for branch evaluation and winner selection
---

# Check Results

Comprehensive tool for fetching, analyzing, and comparing WandB experiment results across branches. This is the primary tool for evaluating experiments and selecting winners.

## Subcommands

### status — Run status overview

```bash
python .claude/skills/check-results/check_results.py --project <project> status [--branch <name>]
```

Shows state (running, finished, crashed, etc.) for all branches or a specific one.

### summary — Summary metrics

```bash
python .claude/skills/check-results/check_results.py --project <project> summary [--metrics loss,accuracy]
```

Fetches final summary metrics for all finished runs. Auto-detects numeric metrics if none specified.

### history — Full metric history

```bash
python .claude/skills/check-results/check_results.py --project <project> history --branch <name> [--metrics loss,accuracy] [--rows 40]
```

Fetches complete step-by-step metric history for a branch's latest run. Useful for analyzing training curves.

### compare — Side-by-side comparison

```bash
python .claude/skills/check-results/check_results.py --project <project> compare [--branches a,b,c] [--metrics loss,accuracy]
```

Compares branches on each metric, identifies the best per metric (auto-detects if lower/higher is better), and shows win counts.

### artifacts — List logged artifacts

```bash
python .claude/skills/check-results/check_results.py --project <project> artifacts --branch <name>
```

Lists all artifacts (models, checkpoints, outputs) logged by a branch's run.

### diagnose — Debug failed runs

```bash
python .claude/skills/check-results/check_results.py --project <project> diagnose [--branch <name>] [--limit 5]
```

For crashed/failed runs: shows config, summary, last history steps, and log tail. Essential for fixing branch bugs before re-launching.

### report — Full winner selection report

```bash
python .claude/skills/check-results/check_results.py --project <project> report [--metrics loss,accuracy]
```

Comprehensive report covering all branches: status overview, metric comparison, hyperparameter diff, problematic runs, and winner recommendations.

### post-pr — Post results to GitHub PR

```bash
python .claude/skills/check-results/check_results.py --project <project> post-pr --branch <name>
```

Finds the PR for a branch, posts a comment with metrics table, comparison vs baseline, and updates PR labels (`experiment:finished`, `experiment:crashed`, `experiment:running`).

## Global Options

- `--project` (required): WandB project name
- `--entity`: WandB entity (team/user)
- `--json`: Output structured JSON (useful for programmatic analysis)

## When to use

- **status**: Check if runs are done before analyzing
- **summary/compare**: Evaluate finished runs to pick winners
- **history**: Deep-dive into training dynamics of a specific branch
- **diagnose**: Debug crashed/failed runs to fix and re-launch
- **report**: End-of-cycle full evaluation for merge decisions
- **artifacts**: Inspect what a run produced (models, checkpoints)
- **post-pr**: Post results to the branch's GitHub PR with metrics and baseline comparison

## Metric direction heuristic

Metrics containing "loss", "error", "perplexity", "mse", "mae", "rmse" are treated as lower-is-better. All others are higher-is-better. Override by specifying `--metrics` explicitly.

$ARGUMENTS
