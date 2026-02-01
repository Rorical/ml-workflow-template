# ML Workflow Template

A template for running ML experiments end-to-end with [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [WandB](https://wandb.ai). You provide ideas — Claude Code handles implementation, training, evaluation, and integration.

## How It Works

```
You: "Try learning rate 0.01"
 │
 ▼
Claude Code creates branch → implements change → launches WandB job
 │
 ▼
GPU agent trains the model → WandB tracks metrics
 │
 ▼
Run finishes → Claude Code analyzes results → posts to PR
 │
 ▼
Winners merge into main → new baseline established → repeat
```

### The Experiment Loop

1. **You provide ideas** — as GitHub Issues or chat messages
2. **Claude Code implements** — creates a branch, writes code, opens a draft PR
3. **WandB trains** — job is launched to a GPU agent via WandB Launch
4. **Results are analyzed** — automatically when the run finishes, or on-demand
5. **Winners merge** — branches that beat the baseline merge into `main`
6. **Baseline updates** — new baseline is tagged and released
7. **Repeat** — next round of experiments starts from the improved baseline

Multiple experiments run in parallel. Each gets its own branch, worktree, and WandB run.

## Prerequisites

- **Python 3.10+**
- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** — installed and authenticated
- **[WandB](https://wandb.ai) account** — with a project and a Launch queue configured
- **GPU environment** — running a WandB Launch agent (cloud or on-prem). For private repos, the agent must have git credentials to clone the repo (deploy key, `GITHUB_TOKEN`, or credential helper)
- **GitHub CLI (`gh`)** — installed and authenticated
- **Git** — with push access to the repo

## Quick Start

### 1. Create your repo from this template

Click **"Use this template"** on GitHub, or:

```bash
gh repo create my-ml-project --template <this-repo-url> --clone
cd my-ml-project
```

### 2. Initialize the project

Open Claude Code and run:

```
/init-project my-project "Short description of what you're training"
```

This sets up:
- Python virtual environment with dependencies
- WandB connection (entity, project, queue)
- Local secrets in `.claude/settings.local.json`
- Project config in `CLAUDE.md`
- Initial baseline documentation

### 3. Set up automation (optional but recommended)

```
/setup-automation
```

This configures:
- GitHub Secrets and Variables for CI
- GitHub labels for experiment tracking
- WandB Automation webhook for automatic result analysis
- Tests the full pipeline end-to-end

After this, WandB runs that finish will **automatically** trigger Claude Code to analyze results and post to the PR — no manual polling needed.

### 4. Start experimenting

```
/new-experiment "increase learning rate to 0.01"
```

Or from a GitHub Issue:

```
/pick-issue 42
```

Then launch the training job:

```
/launch-job
```

## Project Structure

```
├── CLAUDE.md              # Project config and current baseline metrics
├── main.py                # Entry point for WandB Launch jobs
├── src/                   # Core ML code (models, training, data loaders)
├── misc/                  # Local utility scripts (dataset upload, preprocessing)
├── docs/                  # Branch docs and baseline history
├── requirements.txt       # Pinned dependencies
├── .claude/
│   ├── rules/             # Workflow rules (git, wandb, environment, etc.)
│   ├── skills/            # Slash commands (/new-experiment, /launch-job, etc.)
│   ├── agents/            # Sub-agents for parallel execution
│   ├── settings.json      # Shared project config (committed)
│   └── settings.local.json # Local secrets (gitignored)
└── .github/
    └── workflows/         # Auto-analysis on WandB run completion
```

## Available Commands

| Command | Description |
|---------|-------------|
| `/init-project` | Initialize a new project from the template |
| `/setup-automation` | Set up GitHub Actions + WandB webhook pipeline |
| `/new-experiment` | Create a new experiment branch from an idea |
| `/pick-issue` | Start an experiment from a GitHub Issue |
| `/launch-job` | Launch a WandB training job for a branch |
| `/check-results` | Fetch and analyze WandB run results |
| `/fix-and-relaunch` | Diagnose a failed run, fix, and relaunch |
| `/merge-winners` | Merge winning branches into main |
| `/run-baseline` | Run main as the baseline for comparison |
| `/rollback-baseline` | Revert to previous baseline if regression detected |
| `/manage-queue` | Monitor WandB Launch queue status |
| `/manage-runs` | Tag, annotate, or cancel WandB runs |
| `/manage-datasets` | Upload/download datasets as WandB artifacts |
| `/manage-artifacts` | Manage model checkpoints and other artifacts |

## Configuration

### Local secrets (`.claude/settings.local.json` — never committed)

```json
{
  "env": {
    "WANDB_API_KEY": "...",
    "KAGGLE_USERNAME": "...",
    "KAGGLE_KEY": "...",
    "HF_TOKEN": "..."
  }
}
```

### Project defaults (`.claude/settings.json` — committed)

```json
{
  "env": {
    "WANDB_ENTITY": "your-entity",
    "WANDB_PROJECT": "your-project",
    "WANDB_QUEUE": "your-queue"
  }
}
```

### GitHub (for auto-analysis pipeline)

| Type | Name | Description |
|------|------|-------------|
| Secret | `ANTHROPIC_API_KEY` | Claude API key |
| Secret | `WANDB_API_KEY` | WandB API key |
| Variable | `WANDB_ENTITY` | WandB entity/team |
| Variable | `WANDB_PROJECT` | WandB project name |

## Customization

This is a **template** — adapt it to your ML project:

- **`main.py`** — Wire up your model, dataset, and training loop
- **`src/`** — Add your model architecture, data loaders, and training logic
- **`misc/`** — Add scripts for dataset preparation, preprocessing, etc.
- **`requirements.txt`** — Add your dependencies (pin exact versions with `==`)
- **`CLAUDE.md`** — Add project-specific notes and context

The workflow infrastructure (`.claude/`, `.github/`) works out of the box.

## How the Automation Works

```
WandB run finishes
       │
       ▼
WandB Automation fires webhook
       │
       ▼
GitHub Actions receives repository_dispatch
       │
       ▼
Claude Code (--print) analyzes results
       │
       ▼
Posts metrics + comparison to the PR
```

- **Successful runs**: Metrics are compared against baseline, posted to PR
- **Failed/crashed runs**: Failure is diagnosed, summary + fix suggestion posted to PR

This is set up by `/setup-automation` and runs via `.github/workflows/wandb-run-finished.yml`.

## License

MIT
