"""Manage WandB dataset artifacts: upload, download, list, version.

Usage:
    python .claude/skills/manage-datasets/manage_datasets.py --project <project> <command> [options]

Subcommands:
    upload    - Upload a local directory/file as a dataset artifact
    download  - Download a dataset artifact to local path
    list      - List all dataset artifacts in the project
    info      - Show details of a specific dataset artifact version
"""

import argparse
import json
import os
import sys



import wandb


def get_api():
    return wandb.Api()


# ── upload ───────────────────────────────────────────────────────────────────


def cmd_upload(args):
    """Upload local data as a WandB dataset artifact."""
    with wandb.init(
        project=args.project,
        entity=args.entity,
        job_type="dataset-upload",
        name=f"upload-{args.name}",
    ) as run:
        artifact = wandb.Artifact(
            name=args.name,
            type="dataset",
            description=args.description or "",
            metadata=json.loads(args.metadata) if args.metadata else {},
        )

        path = args.path
        if os.path.isdir(path):
            artifact.add_dir(path)
            print(f"Added directory: {path}")
        elif os.path.isfile(path):
            artifact.add_file(path)
            print(f"Added file: {path}")
        else:
            print(f"Error: path '{path}' does not exist.", file=sys.stderr)
            sys.exit(1)

        if args.reference:
            artifact.add_reference(args.reference, name="source")
            print(f"Added reference: {args.reference}")

        aliases = ["latest"]
        if args.alias:
            aliases.extend(args.alias.split(","))

        run.log_artifact(artifact, aliases=aliases)
        print(f"Uploaded artifact: {args.name}")
        print(f"Aliases: {aliases}")


# ── download ─────────────────────────────────────────────────────────────────


def cmd_download(args):
    """Download a dataset artifact."""
    api = get_api()
    artifact_path = args.artifact
    if "/" not in artifact_path:
        # Short name: prepend entity/project
        prefix = f"{args.entity}/{args.project}" if args.entity else args.project
        artifact_path = f"{prefix}/{artifact_path}"

    print(f"Downloading: {artifact_path}")
    artifact = api.artifact(artifact_path)

    dest = args.output or f"./data/{artifact.name}"
    artifact_dir = artifact.download(root=dest)
    print(f"Downloaded to: {artifact_dir}")
    print(f"Version: {artifact.version}")
    print(f"Size: {artifact.size} bytes")


# ── list ─────────────────────────────────────────────────────────────────────


def cmd_list(args):
    """List all dataset artifacts in the project."""
    api = get_api()
    path = f"{args.entity}/{args.project}" if args.entity else args.project

    collections = api.artifact_collections(
        project_name=path,
        type_name="dataset",
    )

    print(f"{'Name':<35} {'Versions':<10} {'Description':<40}")
    print("-" * 85)

    for col in collections:
        versions = list(col.versions())
        desc = col.description or ""
        if len(desc) > 38:
            desc = desc[:38] + ".."
        print(f"{col.name:<35} {len(versions):<10} {desc:<40}")

    if args.json:
        output = []
        for col in api.artifact_collections(project_name=path, type_name="dataset"):
            versions = list(col.versions())
            output.append({
                "name": col.name,
                "versions": len(versions),
                "description": col.description,
            })
        print("\n" + json.dumps(output, indent=2))


# ── info ─────────────────────────────────────────────────────────────────────


def cmd_info(args):
    """Show details of a specific dataset artifact."""
    api = get_api()
    artifact_path = args.artifact
    if "/" not in artifact_path:
        prefix = f"{args.entity}/{args.project}" if args.entity else args.project
        artifact_path = f"{prefix}/{artifact_path}"

    artifact = api.artifact(artifact_path)

    print(f"Name:        {artifact.name}")
    print(f"Version:     {artifact.version}")
    print(f"Type:        {artifact.type}")
    print(f"Description: {artifact.description or 'N/A'}")
    print(f"State:       {artifact.state}")
    print(f"Size:        {artifact.size} bytes")
    print(f"Created:     {artifact.created_at}")
    print(f"Aliases:     {[a.alias for a in artifact.aliases] if artifact.aliases else []}")

    if artifact.metadata:
        print(f"Metadata:    {json.dumps(artifact.metadata, indent=2)}")

    print("\nFiles:")
    for f in artifact.files():
        print(f"  {f.name} ({f.size} bytes)")

    if args.json:
        print("\n" + json.dumps({
            "name": artifact.name,
            "version": artifact.version,
            "type": artifact.type,
            "description": artifact.description,
            "size": artifact.size,
            "metadata": artifact.metadata,
            "aliases": [a.alias for a in artifact.aliases] if artifact.aliases else [],
        }, indent=2, default=str))


# ── main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Manage WandB dataset artifacts.")
    parser.add_argument("--project", default=os.environ.get("WANDB_PROJECT"), help="WandB project name (default: $WANDB_PROJECT).")
    parser.add_argument("--entity", default=os.environ.get("WANDB_ENTITY"), help="WandB entity (default: $WANDB_ENTITY).")
    parser.add_argument("--json", action="store_true", help="JSON output.")

    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("upload", help="Upload dataset artifact.")
    p.add_argument("--name", required=True, help="Artifact name.")
    p.add_argument("--path", required=True, help="Local file or directory to upload.")
    p.add_argument("--description", default=None, help="Artifact description.")
    p.add_argument("--metadata", default=None, help="JSON string of metadata.")
    p.add_argument("--alias", default=None, help="Comma-separated aliases (in addition to 'latest').")
    p.add_argument("--reference", default=None, help="External reference URI (e.g., s3://bucket/path).")

    p = sub.add_parser("download", help="Download dataset artifact.")
    p.add_argument("--artifact", required=True, help="Artifact name:version (e.g., my-data:v0 or my-data:latest).")
    p.add_argument("--output", default=None, help="Local output directory.")

    p = sub.add_parser("list", help="List dataset artifacts.")

    p = sub.add_parser("info", help="Show artifact details.")
    p.add_argument("--artifact", required=True, help="Artifact name:version.")

    args = parser.parse_args()
    if not args.project:
        parser.error("--project is required (or set WANDB_PROJECT env var)")
    {"upload": cmd_upload, "download": cmd_download, "list": cmd_list, "info": cmd_info}[args.command](args)


if __name__ == "__main__":
    main()
