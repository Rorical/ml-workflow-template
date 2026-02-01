---
name: manage-runs
description: Tag, delete, cancel, and clean up WandB runs
disable-model-invocation: true
allowed-tools: Bash(python *)
argument-hint: [tag|note|delete|cleanup|cancel]
---

# Manage Runs

Manage WandB runs — tag winners/losers, add notes, delete, bulk cleanup, cancel.

## Commands

### Tag a run (mark winner/loser)

```bash
python .claude/skills/manage-runs/manage_runs.py --project <project> tag \
  --branch <name> --add "winner,merge-candidate"

python .claude/skills/manage-runs/manage_runs.py --project <project> tag \
  --branch <name> --remove "winner"
```

### Add notes to a run

```bash
python .claude/skills/manage-runs/manage_runs.py --project <project> note \
  --branch <name> --text "Best accuracy so far, candidate for merge" [--append]
```

### Delete a run

```bash
python .claude/skills/manage-runs/manage_runs.py --project <project> delete \
  --branch <name> [--delete-artifacts] [--force]
```

### Bulk cleanup crashed/failed runs

```bash
python .claude/skills/manage-runs/manage_runs.py --project <project> cleanup \
  [--states crashed,failed] [--delete-artifacts] [--dry-run] [--force]
```

### Cancel running runs

```bash
python .claude/skills/manage-runs/manage_runs.py --project <project> cancel \
  --branch <name>

python .claude/skills/manage-runs/manage_runs.py --project <project> cancel \
  --all-running
```

## When to use

- After `check-results report`: tag winners and losers
- Before `merge-winners`: mark branches with tags for selection
- After failed experiments: cleanup crashed runs to reduce clutter
- When a run is stuck: cancel it and re-launch after fixes
- To annotate runs with retrospective notes

All commands accept `--run-id` or `--branch` to target runs.

$ARGUMENTS
