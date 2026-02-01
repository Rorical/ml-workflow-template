"""Training loop template.

Modify this file for your specific model and training procedure.
All metrics should be logged to wandb for experiment tracking.
"""

import wandb


def train(config, dataset, run):
    """Run training loop.

    Args:
        config: wandb.config object with hyperparameters.
        dataset: Dataset dict returned by src.data.load_dataset.
        run: Active wandb.Run for logging.

    Returns:
        Tuple of (model, results_dict).
        - model: Trained model object (or None).
        - results_dict: Final metrics dict to write to run.summary.
    """
    epochs = config.get("epochs", 10)
    learning_rate = config.get("learning_rate", 1e-3)
    batch_size = config.get("batch_size", 32)

    # TODO: Initialize model
    model = None

    # TODO: Initialize optimizer, loss, scheduler

    for epoch in range(epochs):
        # TODO: Training step
        train_loss = 0.0
        train_acc = 0.0

        # TODO: Validation step
        val_loss = 0.0
        val_acc = 0.0

        # ── Log metrics per epoch ──
        wandb.log({
            "epoch": epoch,
            "train/loss": train_loss,
            "train/accuracy": train_acc,
            "val/loss": val_loss,
            "val/accuracy": val_acc,
            "learning_rate": learning_rate,
        })

        # ── Log sample predictions periodically ──
        if (epoch + 1) % max(1, epochs // 5) == 0:
            # TODO: Log sample predictions
            # e.g., wandb.log({"predictions": wandb.Table(...)})
            pass

    # ── Final results ──
    results = {
        "final/train_loss": train_loss,
        "final/train_accuracy": train_acc,
        "final/val_loss": val_loss,
        "final/val_accuracy": val_acc,
    }

    return model, results
