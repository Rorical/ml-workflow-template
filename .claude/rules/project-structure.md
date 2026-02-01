# Project Structure

Python project managed by `pip` with a local virtual environment.

```text
project-root/
├── CLAUDE.md            # Project-specific instructions and context
├── requirements.txt     # Dependencies (used by local env and WandB Launch agents)
├── main.py              # Entry point for WandB Launch jobs
├── src/                 # Core ML code (models, training, data loaders, etc.)
├── misc/                # Utility scripts for local-only tasks (not run on agents)
│                        #   e.g., fetch/upload datasets to WandB, preprocessing
├── docs/                # Branch documentation (docs/<branch-name>.md)
└── README.md
```

## Details

- **main.py**: Entry point invoked by WandB Launch agents. Contains general template code for initializing WandB, loading config, and dispatching training.
- **src/**: All core ML code lives here — models, training loops, data loading, evaluation.
- **misc/**: Project-specific utility scripts that run locally (not on agents). Used for tasks like fetching datasets, uploading to WandB, and preprocessing. These interact with WandB but are not part of the training job.
- **requirements.txt**: Defines all dependencies. Used both for local development and by WandB Launch agents to set up the environment. **All dependencies must be pinned to exact versions** (e.g., `wandb==0.24.1`, not `wandb`). This ensures reproducibility across runs and environments.

## Requirements Pinning

- Always pin exact versions with `==` in `requirements.txt`.
- Never use unpinned (`wandb`), loose (`wandb>=0.24.1`), or range (`wandb~=0.24.1`) specifiers.
- When adding a new dependency, pin it to the current latest version.
- When upgrading, update the version explicitly and test before committing.
- This applies to all dependencies — direct and indirect where necessary.

## Standard Document Formats

### `docs/baseline-history.md`

Each baseline entry follows this format:

```markdown
## Baseline YYYY-MM-DD

- **Release**: `baseline-YYYYMMDD` ([link])
- **Run ID**: `<wandb-run-id>`
- **Merged branches**:
  - `<branch-name>` — PR #<number>: <short description>
- **Discarded branches**:
  - `<branch-name>` — PR #<number>: <reason>
- **Key metrics**:
  | Metric | Value | Delta vs Previous |
  |--------|-------|-------------------|
  | ...    | ...   | ...               |
```

### `CLAUDE.md` — "Current Baseline" section

```markdown
## Current Baseline

| Metric | Value |
|--------|-------|
| ...    | ...   |

- **Run ID**: `<wandb-run-id>`
- **Date**: YYYY-MM-DD
- **Release**: `baseline-YYYYMMDD`
```
