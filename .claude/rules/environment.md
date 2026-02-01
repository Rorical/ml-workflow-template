# Environment Variables

## Secret / per-user variables

Store in `.claude/settings.local.json` (gitignored, never committed):

```json
{
  "env": {
    "KAGGLE_USERNAME": "...",
    "KAGGLE_KEY": "...",
    "HF_TOKEN": "...",
    "WANDB_API_KEY": "..."
  }
}
```

Claude Code loads these automatically into the environment for all tool calls.

## Non-secret project defaults

Store in `.claude/settings.json` (committed, shared with team):

```json
{
  "env": {
    "WANDB_ENTITY": "<entity>",
    "WANDB_PROJECT": "<project-name>",
    "WANDB_QUEUE": "<queue-name>"
  }
}
```

## Rules

- **Never** commit secrets to git. All tokens, keys, and credentials go in `settings.local.json`.
- Project-wide non-secret config (entity, project name, queue) goes in `settings.json`.
- `.claude/settings.local.json` must be in `.gitignore`.
- Scripts should read from environment variables (e.g., `os.environ["KAGGLE_KEY"]`), not hardcoded values.

## Validation

Before any commit, verify secrets are not at risk of being committed:

```bash
# Check that settings.local.json is gitignored
git check-ignore .claude/settings.local.json
```

If the check fails (exit code 1), add `.claude/settings.local.json` to `.gitignore` before committing. The `/init-project` skill creates this `.gitignore` entry automatically.
