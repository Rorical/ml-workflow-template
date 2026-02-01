"""Download a WandB dataset artifact to local disk.

Usage:
    python misc/download_dataset.py --artifact <name:version> [--output ./data/]
"""

import argparse
import os

import wandb


def main():
    parser = argparse.ArgumentParser(description="Download dataset artifact from WandB.")
    parser.add_argument("--artifact", required=True, help="Artifact name:version (e.g., my-data:latest).")
    parser.add_argument("--output", default="./data", help="Local output directory.")
    parser.add_argument("--project", default=os.environ.get("WANDB_PROJECT"), help="WandB project.")
    parser.add_argument("--entity", default=os.environ.get("WANDB_ENTITY"), help="WandB entity.")
    args = parser.parse_args()

    if not args.project:
        parser.error("--project required (or set WANDB_PROJECT)")

    api = wandb.Api()
    path = args.artifact
    if "/" not in path:
        prefix = f"{args.entity}/{args.project}" if args.entity else args.project
        path = f"{prefix}/{path}"

    print(f"Downloading: {path}")
    artifact = api.artifact(path)
    artifact_dir = artifact.download(root=args.output)
    print(f"Downloaded to: {artifact_dir}")
    print(f"Version: {artifact.version}, Size: {artifact.size} bytes")


if __name__ == "__main__":
    main()
