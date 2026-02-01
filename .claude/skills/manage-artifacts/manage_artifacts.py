"""Manage WandB artifacts: download models/checkpoints, query, link to registry.

Usage:
    python .claude/skills/manage-artifacts/manage_artifacts.py --project <project> <command> [options]

Subcommands:
    download    - Download an artifact (model, checkpoint, etc.)
    list        - List artifacts by type
    info        - Show artifact details, files, metadata
    link        - Link an artifact to the model registry
    search      - Search artifacts by name pattern or metadata
"""

import argparse
import json
import os
import re
import sys

import wandb


def get_api():
    return wandb.Api()


def resolve_artifact_path(name, entity, project):
    """Prepend entity/project if not already qualified."""
    if "/" not in name:
        prefix = f"{entity}/{project}" if entity else project
        return f"{prefix}/{name}"
    return name


# ── download ─────────────────────────────────────────────────────────────────


def cmd_download(args):
    """Download an artifact."""
    api = get_api()
    path = resolve_artifact_path(args.artifact, args.entity, args.project)

    print(f"Downloading: {path}")
    artifact = api.artifact(path)

    dest = args.output or f"./artifacts/{artifact.name}"
    artifact_dir = artifact.download(root=dest)
    print(f"Downloaded to: {artifact_dir}")
    print(f"Version: {artifact.version}")
    print(f"Type: {artifact.type}")
    print(f"Size: {artifact.size} bytes")


# ── list ─────────────────────────────────────────────────────────────────────


def cmd_list(args):
    """List artifacts by type."""
    api = get_api()
    path = f"{args.entity}/{args.project}" if args.entity else args.project
    artifact_type = args.type or "model"

    collections = api.artifact_collections(
        project_name=path,
        type_name=artifact_type,
    )

    print(f"Artifacts of type '{artifact_type}':")
    print(f"{'Name':<40} {'Versions':<10} {'Description':<35}")
    print("-" * 85)

    results = []
    for col in collections:
        versions = list(col.versions())
        desc = (col.description or "")[:33]
        print(f"{col.name:<40} {len(versions):<10} {desc:<35}")
        results.append({"name": col.name, "versions": len(versions), "description": col.description})

    if args.json:
        print("\n" + json.dumps(results, indent=2))


# ── info ─────────────────────────────────────────────────────────────────────


def cmd_info(args):
    """Show artifact details."""
    api = get_api()
    path = resolve_artifact_path(args.artifact, args.entity, args.project)
    artifact = api.artifact(path)

    aliases = [a.alias for a in artifact.aliases] if artifact.aliases else []

    print(f"Name:        {artifact.name}")
    print(f"Version:     {artifact.version}")
    print(f"Type:        {artifact.type}")
    print(f"Description: {artifact.description or 'N/A'}")
    print(f"State:       {artifact.state}")
    print(f"Size:        {artifact.size} bytes")
    print(f"Created:     {artifact.created_at}")
    print(f"Aliases:     {aliases}")

    if artifact.metadata:
        print(f"Metadata:\n{json.dumps(artifact.metadata, indent=2)}")

    print("\nFiles:")
    for f in artifact.files():
        size_str = f"{f.size} B"
        if f.size > 1e6:
            size_str = f"{f.size / 1e6:.1f} MB"
        elif f.size > 1e3:
            size_str = f"{f.size / 1e3:.1f} KB"
        print(f"  {f.name} ({size_str})")

    # Show lineage: which run produced this
    if hasattr(artifact, "logged_by") and artifact.logged_by:
        run = artifact.logged_by()
        if run:
            print(f"\nProduced by run: {run.name} (ID: {run.id})")
            branch = run.config.get("branch", "N/A")
            print(f"Branch: {branch}")

    if args.json:
        print("\n" + json.dumps({
            "name": artifact.name,
            "version": artifact.version,
            "type": artifact.type,
            "size": artifact.size,
            "aliases": aliases,
            "metadata": artifact.metadata,
        }, indent=2, default=str))


# ── link ─────────────────────────────────────────────────────────────────────


def cmd_link(args):
    """Link an artifact to the model registry."""
    api = get_api()
    path = resolve_artifact_path(args.artifact, args.entity, args.project)
    artifact = api.artifact(path)

    target = args.target
    print(f"Linking {path} -> {target}")

    with wandb.init(
        project=args.project,
        entity=args.entity,
        job_type="registry-link",
        name=f"link-{artifact.name}",
    ) as run:
        run.link_artifact(
            artifact,
            target_path=target,
            aliases=args.aliases.split(",") if args.aliases else None,
        )

    print(f"Linked successfully.")
    if args.aliases:
        print(f"Aliases: {args.aliases}")


# ── search ───────────────────────────────────────────────────────────────────


def cmd_search(args):
    """Search artifacts by name pattern."""
    api = get_api()
    path = f"{args.entity}/{args.project}" if args.entity else args.project
    artifact_type = args.type or "model"
    pattern = args.pattern

    collections = api.artifact_collections(
        project_name=path,
        type_name=artifact_type,
    )

    print(f"Search results for '{pattern}' (type: {artifact_type}):")
    print(f"{'Name':<40} {'Latest':<10} {'Aliases':<30}")
    print("-" * 80)

    for col in collections:
        if not re.search(pattern, col.name, re.IGNORECASE):
            continue
        versions = list(col.versions())
        if versions:
            latest = versions[0]
            aliases = [a.alias for a in latest.aliases] if latest.aliases else []
            print(f"{col.name:<40} {latest.version:<10} {', '.join(aliases):<30}")
        else:
            print(f"{col.name:<40} {'N/A':<10} {'':<30}")


# ── main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Manage WandB artifacts.")
    parser.add_argument("--project", default=os.environ.get("WANDB_PROJECT"), help="WandB project name (default: $WANDB_PROJECT).")
    parser.add_argument("--entity", default=os.environ.get("WANDB_ENTITY"), help="WandB entity (default: $WANDB_ENTITY).")
    parser.add_argument("--json", action="store_true", help="JSON output.")

    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("download", help="Download artifact.")
    p.add_argument("--artifact", required=True, help="Artifact name:version.")
    p.add_argument("--output", default=None, help="Local output directory.")

    p = sub.add_parser("list", help="List artifacts by type.")
    p.add_argument("--type", default="model", help="Artifact type (default: model).")

    p = sub.add_parser("info", help="Show artifact details.")
    p.add_argument("--artifact", required=True, help="Artifact name:version.")

    p = sub.add_parser("link", help="Link artifact to model registry.")
    p.add_argument("--artifact", required=True, help="Artifact name:version.")
    p.add_argument("--target", required=True, help="Registry target path (e.g., wandb-registry-model/my-model).")
    p.add_argument("--aliases", default=None, help="Comma-separated aliases.")

    p = sub.add_parser("search", help="Search artifacts by name pattern.")
    p.add_argument("--pattern", required=True, help="Regex pattern to match artifact names.")
    p.add_argument("--type", default="model", help="Artifact type (default: model).")

    args = parser.parse_args()
    if not args.project:
        parser.error("--project is required (or set WANDB_PROJECT env var)")
    cmds = {"download": cmd_download, "list": cmd_list, "info": cmd_info, "link": cmd_link, "search": cmd_search}
    cmds[args.command](args)


if __name__ == "__main__":
    main()
