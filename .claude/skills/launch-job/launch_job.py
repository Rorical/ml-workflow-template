"""Launch a WandB job for a specific git branch.

Usage:
    python .claude/skills/launch-job/launch_job.py --branch <branch-name> [options]

This script creates a temporary WandB Launch job from the current git repo
at a specific branch and pushes it to a launch queue for execution by agents
running in GPU environments.
"""

import argparse
import json
import os
import subprocess
import sys

import wandb
from wandb.sdk.launch import launch_add


def get_git_remote_url() -> str:
    """Get the git remote URL of the current repo."""
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def branch_exists(branch: str) -> bool:
    """Check if a local git branch exists."""
    result = subprocess.run(
        ["git", "rev-parse", "--verify", branch],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def get_branch_head(branch: str) -> str:
    """Get the HEAD commit hash of a branch."""
    result = subprocess.run(
        ["git", "rev-parse", branch],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description="Launch a WandB job for a git branch.")
    parser.add_argument("--branch", required=True, help="Git branch name to launch.")
    parser.add_argument("--queue", default=os.environ.get("WANDB_QUEUE"), help="WandB Launch queue name (default: $WANDB_QUEUE).")
    parser.add_argument("--project", default=os.environ.get("WANDB_PROJECT"), help="WandB project name (default: $WANDB_PROJECT).")
    parser.add_argument("--entity", default=os.environ.get("WANDB_ENTITY"), help="WandB entity (default: $WANDB_ENTITY).")
    parser.add_argument("--entry-point", default="main.py", help="Entry point script (default: main.py).")
    parser.add_argument("--config", default=None, help="JSON string or path to JSON file with run config overrides.")
    parser.add_argument("--resource", default=None, help="Compute resource type (e.g., local-process, kubernetes).")
    parser.add_argument("--resource-args", default=None, help="JSON string with resource args.")
    parser.add_argument("--docker-image", default=None, help="Docker image to use instead of building from repo.")
    parser.add_argument("--priority", type=int, default=None, help="Job priority in queue.")
    parser.add_argument("--dry-run", action="store_true", help="Print config without launching.")
    args = parser.parse_args()

    # Validate branch
    if not branch_exists(args.branch):
        print(f"Error: branch '{args.branch}' does not exist locally.", file=sys.stderr)
        sys.exit(1)

    # Get repo info
    repo_url = get_git_remote_url()
    commit = get_branch_head(args.branch)

    # Parse config overrides
    run_config = {}
    if args.config:
        try:
            run_config = json.loads(args.config)
        except json.JSONDecodeError:
            # Treat as file path
            with open(args.config) as f:
                run_config = json.load(f)

    # Always inject branch metadata
    run_config["branch"] = args.branch
    run_config["commit"] = commit

    # Build launch config
    config = {
        "overrides": {
            "run_config": run_config,
            "entry_point": ["python", args.entry_point],
        },
    }

    # Parse resource args
    resource_args = None
    if args.resource_args:
        try:
            resource_args = json.loads(args.resource_args)
        except json.JSONDecodeError:
            with open(args.resource_args) as f:
                resource_args = json.load(f)

    if not args.project:
        parser.error("--project is required (or set WANDB_PROJECT env var)")
    if not args.queue:
        parser.error("--queue is required (or set WANDB_QUEUE env var)")

    if args.dry_run:
        print("=== Dry Run ===")
        print(f"Repo:       {repo_url}")
        print(f"Branch:     {args.branch}")
        print(f"Commit:     {commit}")
        print(f"Queue:      {args.queue}")
        print(f"Project:    {args.project}")
        print(f"Entity:     {args.entity}")
        print(f"Entry:      {args.entry_point}")
        print(f"Resource:   {args.resource}")
        print(f"Config:     {json.dumps(config, indent=2)}")
        return

    # Push job to queue
    print(f"Launching job for branch '{args.branch}' (commit {commit[:8]})...")
    print(f"  Repo:    {repo_url}")
    print(f"  Queue:   {args.queue}")
    print(f"  Project: {args.project}")

    queued_run = launch_add(
        uri=repo_url,
        job=None,
        config=config,
        project=args.project,
        entity=args.entity,
        queue_name=args.queue,
        resource=args.resource,
        resource_args=resource_args,
        entry_point=["python", args.entry_point],
        name=f"{args.branch}-{commit[:8]}",
        version=args.branch,
        docker_image=args.docker_image,
        priority=args.priority,
    )

    print(f"Job queued successfully.")
    print(f"  Run ID:  {queued_run.id}")
    print(f"  State:   {queued_run.state}")


if __name__ == "__main__":
    main()
