---
name: manage-artifacts
description: Download models/checkpoints, query artifact collections, link to model registry
disable-model-invocation: true
allowed-tools: Bash(python *)
argument-hint: [download|list|info|link|search]
---

# Manage Artifacts

Manage WandB artifacts — models, checkpoints, and other outputs.

## Commands

### Download artifact

```bash
python .claude/skills/manage-artifacts/manage_artifacts.py --project <project> download \
  --artifact <name:version> [--output ./artifacts/]
```

### List artifacts by type

```bash
python .claude/skills/manage-artifacts/manage_artifacts.py --project <project> list \
  [--type model]
```

Types: `model`, `dataset`, `checkpoint`, or any custom type.

### Show artifact info

```bash
python .claude/skills/manage-artifacts/manage_artifacts.py --project <project> info \
  --artifact <name:version>
```

Shows files, metadata, size, aliases, and which run/branch produced it.

### Link to model registry

```bash
python .claude/skills/manage-artifacts/manage_artifacts.py --project <project> link \
  --artifact <name:version> --target wandb-registry-model/my-model [--aliases "production,best"]
```

### Search artifacts

```bash
python .claude/skills/manage-artifacts/manage_artifacts.py --project <project> search \
  --pattern "resnet" [--type model]
```

## When to use

- Download winning model checkpoints after merge decisions
- Inspect what artifacts a branch's run produced
- Link best models to the registry for deployment
- Search for specific models/checkpoints across experiments

$ARGUMENTS
