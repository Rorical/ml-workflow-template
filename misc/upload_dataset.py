"""Upload a local dataset to WandB as an artifact.

Usage:
    python misc/upload_dataset.py --name <artifact-name> --path <data-dir> [options]

This script runs locally. It fetches or processes data, then uploads it
as a versioned WandB artifact for reproducible training.
"""

import argparse
import os

import wandb


def main():
    parser = argparse.ArgumentParser(description="Upload dataset to WandB.")
    parser.add_argument("--name", required=True, help="Artifact name.")
    parser.add_argument("--path", required=True, help="Local path to data file or directory.")
    parser.add_argument("--project", default=os.environ.get("WANDB_PROJECT"), help="WandB project.")
    parser.add_argument("--entity", default=os.environ.get("WANDB_ENTITY"), help="WandB entity.")
    parser.add_argument("--description", default="", help="Artifact description.")
    parser.add_argument("--alias", default=None, help="Comma-separated aliases (added to 'latest').")
    args = parser.parse_args()

    if not args.project:
        parser.error("--project required (or set WANDB_PROJECT)")

    with wandb.init(
        project=args.project,
        entity=args.entity,
        job_type="dataset-upload",
        name=f"upload-{args.name}",
    ) as run:
        artifact = wandb.Artifact(
            name=args.name,
            type="dataset",
            description=args.description,
        )

        if os.path.isdir(args.path):
            artifact.add_dir(args.path)
        elif os.path.isfile(args.path):
            artifact.add_file(args.path)
        else:
            raise FileNotFoundError(f"Path not found: {args.path}")

        aliases = ["latest"]
        if args.alias:
            aliases.extend(a.strip() for a in args.alias.split(","))

        run.log_artifact(artifact, aliases=aliases)
        print(f"Uploaded: {args.name} ({aliases})")


if __name__ == "__main__":
    main()
