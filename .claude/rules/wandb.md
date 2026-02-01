# WandB Integration

Everything related to running and evaluating experiments is managed through WandB.

## Running (WandB Launch)

- **Launch queues**: Jobs are dispatched to agents via WandB Launch queues.
- **Agents**: Run in GPU environments, pulling jobs from queues.
- **Job creation**: Each job is based on the current git repo at a specific branch (one experiment per branch).
- **Jobs are temporary**: Jobs should not be reused. Errors are expected and require active development on the branch before re-launching.
- **Private repos**: WandB Launch agents must be able to clone the repo. For private repos, configure git credentials on the agent environment (e.g., `GIT_TERMINAL_PROMPT=0` with a credential helper, deploy key, or `GITHUB_TOKEN`). See WandB Launch docs for details.

## Experiment Tracking

All training scripts must initialize and use WandB for:

- **Metrics**: Log all training/validation metrics
- **Logging**: Full training logs
- **Final artifacts**: Save model checkpoints and outputs as WandB artifacts
- **Branch description**: Record which branch/experiment the run belongs to
- **Hyperparameters**: Log all hyperparameters via `wandb.config`
- **Validation**: Log validation results during and after training
- **Sample predictions**: Log example predictions for qualitative review
- **Diagnostics**: Gradient norms, learning rate schedules, resource usage, etc.

## Datasets

When possible, store datasets as WandB artifacts and reference them in code for full reproducibility.

## Results

Each WandB job corresponds to a branch. The final metrics and logs from each job are used to determine winner branches, completing the experiment loop.

## Automatic Analysis Pipeline

When a WandB run finishes, Claude Code can automatically analyze results and post to the PR. This uses WandB Automations → GitHub Actions → Claude Code CLI.

### Setup

1. **GitHub Secrets & Variables** — add to the repo's Settings → Secrets and Variables → Actions:
   - Secret: `ANTHROPIC_API_KEY` — Claude API key
   - Secret: `WANDB_API_KEY` — WandB API key
   - Variable: `WANDB_ENTITY` — WandB entity/team name
   - Variable: `WANDB_PROJECT` — WandB project name

2. **WandB Automation** — create in the WandB project settings:
   - **Trigger**: Run state changes to `finished`, `failed`, or `crashed`
   - **Action**: Webhook → GitHub repository dispatch
   - **Webhook URL**: `https://api.github.com/repos/<owner>/<repo>/dispatches`
   - **Auth**: `Bearer <GITHUB_PAT>` (a GitHub PAT with `repo` scope)
   - **Payload**: use the template in `misc/wandb_webhook_payload.json`
   - The payload passes the branch name, run ID, and run state from `wandb.config`

3. **GitHub Actions workflow** — already provided at `.github/workflows/wandb-run-finished.yml`. It:
   - Receives the `wandb_run_finished` dispatch event
   - Installs deps and Claude Code
   - Runs `claude --print` with a prompt to analyze results or diagnose failures
   - Posts findings to the branch's PR

### Requirements

- Training scripts must log `branch` in `wandb.config` (already done by `launch_job.py`)
- The GitHub PAT used for the webhook must have `repo` scope
- `ANTHROPIC_API_KEY` must be set in GitHub Secrets

### What it does

- **Run succeeded**: Fetches summary, compares vs baseline, posts metrics to PR, flags if worse than baseline
- **Run failed/crashed**: Diagnoses failure, posts failure summary and suggested fix to PR

This replaces manual polling. The orchestration loop in an active Claude Code session can still override or supplement these automated actions.

## Comparisons

- `check-results compare` compares experiment branches against the latest baseline (`main`) run by default.
- For head-to-head comparison between two experiment branches, fetch each branch's summary via `check-results summary --branch <name>` and compare metrics manually.
