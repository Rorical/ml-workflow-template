"""Manage WandB Launch queue: check status, list pending jobs, monitor agents.

Usage:
    python .claude/skills/manage-queue/manage_queue.py --project <project> <command> [options]

Subcommands:
    status    - Show queue status (pending/running jobs)
    pending   - List all pending jobs in queue
    running   - List all currently running jobs
    history   - Show recent job history (completed/failed)
"""

import argparse
import json
import os
import sys

import wandb


def get_api():
    return wandb.Api()


def get_runs_by_state(api, entity, project, state):
    """Get runs filtered by state."""
    path = f"{entity}/{project}" if entity else project
    runs = api.runs(path, filters={"state": state}, order="-created_at")
    return list(runs)


# ── status ───────────────────────────────────────────────────────────────────


def cmd_status(args):
    """Show overall queue status."""
    api = get_api()
    path = f"{args.entity}/{args.project}" if args.entity else args.project

    # Count by state
    states = ["running", "finished", "crashed", "failed", "killed", "preempting", "preempted"]
    counts = {}
    for state in states:
        runs = api.runs(path, filters={"state": state})
        counts[state] = len(list(runs))

    # Pending: check for queued runs (recently created, not yet running)
    all_runs = api.runs(path, order="-created_at")
    total = len(list(all_runs))

    print(f"Queue Status: {args.entity + '/' if args.entity else ''}{args.project}")
    print(f"  Queue: {args.queue or 'N/A'}")
    print()
    print(f"{'State':<15} {'Count':<10}")
    print("-" * 25)
    for state in states:
        if counts[state] > 0:
            print(f"{state:<15} {counts[state]:<10}")
    print(f"{'TOTAL':<15} {total:<10}")

    # Show running runs with branch info
    running = get_runs_by_state(api, args.entity, args.project, "running")
    if running:
        print(f"\nCurrently Running ({len(running)}):")
        print(f"{'Run Name':<30} {'Branch':<25} {'Created':<20}")
        print("-" * 75)
        for run in running:
            branch = run.config.get("branch", "N/A")
            print(f"{run.name:<30} {branch:<25} {run.created_at:<20}")

    if args.json:
        print("\n" + json.dumps({"counts": counts, "total": total}, indent=2))


# ── pending ──────────────────────────────────────────────────────────────────


def cmd_pending(args):
    """List pending/queued runs."""
    api = get_api()

    # WandB doesn't have a "pending" state per se for runs.
    # Pending jobs are in the launch queue before becoming runs.
    # We show recently created runs that haven't started training yet.
    path = f"{args.entity}/{args.project}" if args.entity else args.project
    runs = api.runs(path, order="-created_at")

    pending = []
    for run in runs:
        if run.state in ("running",):
            # Check if run just started (no history yet)
            if run.lastHistoryStep == -1 or run.lastHistoryStep == 0:
                pending.append(run)
        # Also include preempting
        if run.state in ("preempting",):
            pending.append(run)

    if not pending:
        print("No pending jobs found.")
        print("Note: Jobs waiting in the Launch queue appear once an agent picks them up.")
        return

    print(f"{'Run Name':<30} {'Branch':<25} {'State':<12} {'Created':<20}")
    print("-" * 87)
    for run in pending:
        branch = run.config.get("branch", "N/A")
        print(f"{run.name:<30} {branch:<25} {run.state:<12} {run.created_at:<20}")


# ── running ──────────────────────────────────────────────────────────────────


def cmd_running(args):
    """List all currently running jobs."""
    api = get_api()
    running = get_runs_by_state(api, args.entity, args.project, "running")

    if not running:
        print("No running jobs.")
        return

    print(f"{'Run Name':<30} {'Branch':<25} {'Step':<10} {'Created':<20}")
    print("-" * 85)
    for run in running:
        branch = run.config.get("branch", "N/A")
        step = run.lastHistoryStep if run.lastHistoryStep >= 0 else "N/A"
        print(f"{run.name:<30} {branch:<25} {str(step):<10} {run.created_at:<20}")

    if args.json:
        output = []
        for run in running:
            output.append({
                "name": run.name,
                "id": run.id,
                "branch": run.config.get("branch"),
                "step": run.lastHistoryStep,
                "created_at": run.created_at,
            })
        print("\n" + json.dumps(output, indent=2, default=str))


# ── history ──────────────────────────────────────────────────────────────────


def cmd_history(args):
    """Show recent job history."""
    api = get_api()
    path = f"{args.entity}/{args.project}" if args.entity else args.project

    runs = api.runs(path, order="-created_at")
    runs = list(runs)[:args.limit]

    if not runs:
        print("No runs found.")
        return

    print(f"{'Run Name':<30} {'Branch':<25} {'State':<12} {'Created':<20}")
    print("-" * 87)
    for run in runs:
        branch = run.config.get("branch", "N/A")
        print(f"{run.name:<30} {branch:<25} {run.state:<12} {run.created_at:<20}")

    # Summary
    state_counts = {}
    for run in runs:
        state_counts[run.state] = state_counts.get(run.state, 0) + 1
    print(f"\nLast {len(runs)} runs: {state_counts}")

    if args.json:
        output = []
        for run in runs:
            output.append({
                "name": run.name,
                "id": run.id,
                "branch": run.config.get("branch"),
                "state": run.state,
                "created_at": run.created_at,
            })
        print("\n" + json.dumps(output, indent=2, default=str))


# ── main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Manage WandB Launch queue.")
    parser.add_argument("--project", default=os.environ.get("WANDB_PROJECT"), help="WandB project name (default: $WANDB_PROJECT).")
    parser.add_argument("--entity", default=os.environ.get("WANDB_ENTITY"), help="WandB entity (default: $WANDB_ENTITY).")
    parser.add_argument("--queue", default=os.environ.get("WANDB_QUEUE"), help="Queue name (default: $WANDB_QUEUE).")
    parser.add_argument("--json", action="store_true", help="JSON output.")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show queue status.")

    sub.add_parser("pending", help="List pending jobs.")

    sub.add_parser("running", help="List running jobs.")

    p = sub.add_parser("history", help="Recent job history.")
    p.add_argument("--limit", type=int, default=20, help="Max runs to show (default: 20).")

    args = parser.parse_args()
    if not args.project:
        parser.error("--project is required (or set WANDB_PROJECT env var)")
    cmds = {"status": cmd_status, "pending": cmd_pending, "running": cmd_running, "history": cmd_history}
    cmds[args.command](args)


if __name__ == "__main__":
    main()
