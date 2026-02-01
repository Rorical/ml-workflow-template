---
name: manage-datasets
description: Upload, download, list, and version datasets as WandB artifacts for reproducibility
disable-model-invocation: true
allowed-tools: Bash(python *)
argument-hint: [upload|download|list|info]
---

# Manage Datasets

Manage WandB dataset artifacts for full reproducibility.

## Commands

### Upload a dataset

```bash
python .claude/skills/manage-datasets/manage_datasets.py --project <project> upload \
  --name <artifact-name> --path <local-path> \
  [--description "..."] [--metadata '{"num_samples": 10000}'] [--alias "train-v1"]
```

### Download a dataset

```bash
python .claude/skills/manage-datasets/manage_datasets.py --project <project> download \
  --artifact <name:version> [--output ./data/]
```

### List all datasets

```bash
python .claude/skills/manage-datasets/manage_datasets.py --project <project> list
```

### Show artifact info

```bash
python .claude/skills/manage-datasets/manage_datasets.py --project <project> info \
  --artifact <name:version>
```

## When to use

- Before starting experiments: upload training data for reproducibility
- In `misc/` scripts: fetch external data, process it, upload as artifact
- In `main.py` / `src/`: download artifact to use during training
- To audit which dataset version was used for a run

$ARGUMENTS
