"""Entry point for WandB Launch jobs.

This script is invoked by WandB Launch agents. It:
1. Initializes WandB with config from the launch job
2. Downloads dataset artifacts if configured
3. Runs training via src/train.py
4. Logs final artifacts and summary
"""

import os

import wandb

from src.data import load_dataset
from src.train import train


# Default hyperparameters. Overridden by wandb.config from Launch jobs.
DEFAULTS = {
    # ── Data ──
    "dataset_artifact": None,  # e.g., "my-dataset:latest"
    # ── Training ──
    "epochs": 10,
    "batch_size": 32,
    "learning_rate": 1e-3,
    # ── Model ──
    "model_name": "default",
}


def main():
    run = wandb.init(config=DEFAULTS)
    config = wandb.config

    # Log branch metadata (injected by launch-job skill)
    branch = config.get("branch", "unknown")
    commit = config.get("commit", "unknown")
    print(f"Branch: {branch} | Commit: {commit}")

    # ── Load dataset ──
    dataset = load_dataset(config, run)

    # ── Train ──
    model, results = train(config, dataset, run)

    # ── Log final model artifact ──
    if model is not None:
        model_artifact = wandb.Artifact(
            name=f"model-{branch}",
            type="model",
            description=f"Model from branch {branch} ({commit[:8]})",
            metadata={"branch": branch, "commit": commit},
        )
        # TODO: Save model to file and add to artifact
        # model_artifact.add_file("model.pt")
        # run.log_artifact(model_artifact)

    # ── Log final summary ──
    if results:
        for key, value in results.items():
            run.summary[key] = value

    run.summary["branch"] = branch
    run.summary["commit"] = commit

    wandb.finish()


if __name__ == "__main__":
    main()
