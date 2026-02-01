# misc/

Local-only utility scripts. These run on your machine, **not** on WandB Launch agents.

## Structure

```text
misc/
├── README.md
├── upload_dataset.py      # Fetch/process data and upload as WandB artifact
├── download_dataset.py    # Download a WandB dataset artifact locally
├── explore_data.py        # Quick data exploration and stats
└── export_results.py      # Export WandB results to CSV/local files
```

## Usage

All scripts read `WANDB_PROJECT` and `WANDB_ENTITY` from environment.

```bash
source .venv/bin/activate
python misc/upload_dataset.py --help
```
