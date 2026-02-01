---
name: manage-queue
description: Check WandB Launch queue status, list pending and running jobs, view history
disable-model-invocation: true
allowed-tools: Bash(python *)
argument-hint: [status|pending|running|history]
---

# Manage Queue

Monitor WandB Launch queue — check status, view pending/running jobs, review history.

## Commands

### Queue status overview

```bash
python .claude/skills/manage-queue/manage_queue.py --project <project> --queue <queue> status
```

Shows run counts by state and lists currently running jobs.

### List pending jobs

```bash
python .claude/skills/manage-queue/manage_queue.py --project <project> pending
```

### List running jobs

```bash
python .claude/skills/manage-queue/manage_queue.py --project <project> running
```

Shows current training step for each running job.

### Job history

```bash
python .claude/skills/manage-queue/manage_queue.py --project <project> history [--limit 20]
```

Shows recent jobs with their final states.

## When to use

- Before launching new jobs: check if queue is busy
- After launching: verify jobs are picked up and running
- Monitoring: check progress of running experiments
- Debugging: see if jobs are crashing immediately

$ARGUMENTS
