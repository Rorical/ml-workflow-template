"""Dataset loading template.

Handles both WandB artifact datasets and local datasets.
"""

import os

import wandb


def load_dataset(config, run):
    """Load dataset, optionally from a WandB artifact.

    Args:
        config: wandb.config with dataset settings.
        run: Active wandb.Run for artifact tracking.

    Returns:
        Dict with dataset splits, e.g.:
        {"train": train_data, "val": val_data, "test": test_data}
    """
    dataset_artifact = config.get("dataset_artifact")

    if dataset_artifact:
        # Download dataset from WandB artifact
        print(f"Loading dataset artifact: {dataset_artifact}")
        artifact = run.use_artifact(dataset_artifact)
        data_dir = artifact.download()
        print(f"Dataset downloaded to: {data_dir}")
    else:
        # Default: load from local data/ directory
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        print(f"Loading local dataset from: {data_dir}")

    # TODO: Load actual data from data_dir
    # Example:
    #   train_data = load_from_dir(os.path.join(data_dir, "train"))
    #   val_data = load_from_dir(os.path.join(data_dir, "val"))

    return {
        "train": None,  # TODO: Replace with actual data
        "val": None,
        "test": None,
        "data_dir": data_dir,
    }
