---
name: launch-job
description: Launch a WandB job for a specific git branch experiment
---

# Launch Job

Push a WandB Launch job for a branch to a queue for execution on GPU agents.

## Usage

```bash
python .claude/skills/launch-job/launch_job.py \
  --branch <branch-name> \
  --queue <queue-name> \
  --project <wandb-project> \
  [--entity <wandb-entity>] \
  [--config '{"learning_rate": 0.001}'] \
  [--entry-point main.py] \
  [--resource kubernetes] \
  [--docker-image <image>] \
  [--priority 1] \
  [--dry-run]
```

## When to use

Use this skill when:
- A branch has been implemented and is ready for training/evaluation
- You need to queue an experiment on a GPU agent
- Re-launching a job after fixing bugs on a branch

## Notes

- The branch must exist locally and be pushed to the remote
- Branch name and commit hash are automatically injected into `wandb.config`
- Jobs are temporary and not reusable (per project convention)
- Use `--dry-run` to verify config before launching
- The `--config` flag accepts a JSON string or path to a JSON file

## Arguments

$ARGUMENTS
