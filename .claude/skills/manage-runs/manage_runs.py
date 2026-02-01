"""Manage WandB runs: tag, delete, cancel, cleanup.

Usage:
    python .claude/skills/manage-runs/manage_runs.py --project <project> <command> [options]

Subcommands:
    tag       - Add/remove tags on runs (e.g., mark winners/losers)
    note      - Add notes to a run
    delete    - Delete runs (with optional artifact cleanup)
    cleanup   - Bulk delete crashed/failed runs
    cancel    - Mark running runs for cancellation
"""

import argparse
import json
import os
import sys

import wandb


def get_api():
    return wandb.Api()


def get_run_by_branch(api, entity, project, branch):
    """Get latest run for a branch."""
    path = f"{entity}/{project}" if entity else project
    runs = api.runs(path, filters={"config.branch": branch}, order="-created_at")
    runs = list(runs)
    if not runs:
        print(f"No runs found for branch '{branch}'.", file=sys.stderr)
        sys.exit(1)
    return runs[0]


def resolve_run(api, entity, project, run_id=None, branch=None):
    """Resolve a run by ID or branch name."""
    if run_id:
        path = f"{entity}/{project}/{run_id}" if entity else f"{project}/{run_id}"
        return api.run(path)
    elif branch:
        return get_run_by_branch(api, entity, project, branch)
    else:
        print("Error: provide --run-id or --branch.", file=sys.stderr)
        sys.exit(1)


# ── tag ──────────────────────────────────────────────────────────────────────


def cmd_tag(args):
    """Add or remove tags on a run."""
    api = get_api()
    run = resolve_run(api, args.entity, args.project, args.run_id, args.branch)

    if args.add:
        new_tags = [t.strip() for t in args.add.split(",")]
        run.tags = list(set(run.tags + new_tags))
        print(f"Added tags: {new_tags}")

    if args.remove:
        rm_tags = [t.strip() for t in args.remove.split(",")]
        run.tags = [t for t in run.tags if t not in rm_tags]
        print(f"Removed tags: {rm_tags}")

    run.update()
    print(f"Run: {run.name} (ID: {run.id})")
    print(f"Tags: {run.tags}")


# ── note ─────────────────────────────────────────────────────────────────────


def cmd_note(args):
    """Add notes to a run."""
    api = get_api()
    run = resolve_run(api, args.entity, args.project, args.run_id, args.branch)

    if args.append:
        existing = run.notes or ""
        run.notes = f"{existing}\n{args.text}".strip()
    else:
        run.notes = args.text

    run.update()
    print(f"Run: {run.name} (ID: {run.id})")
    print(f"Notes: {run.notes}")


# ── delete ───────────────────────────────────────────────────────────────────


def cmd_delete(args):
    """Delete a run."""
    api = get_api()
    run = resolve_run(api, args.entity, args.project, args.run_id, args.branch)

    print(f"Deleting run: {run.name} (ID: {run.id}), state: {run.state}")
    branch = run.config.get("branch", "N/A")
    print(f"Branch: {branch}")

    if not args.force:
        confirm = input("Confirm delete? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

    run.delete(delete_artifacts=args.delete_artifacts)
    print(f"Deleted.{' (with artifacts)' if args.delete_artifacts else ''}")


# ── cleanup ──────────────────────────────────────────────────────────────────


def cmd_cleanup(args):
    """Bulk delete crashed/failed runs."""
    api = get_api()
    path = f"{args.entity}/{args.project}" if args.entity else args.project

    states = [s.strip() for s in args.states.split(",")]
    all_runs = []
    for state in states:
        runs = api.runs(path, filters={"state": state}, order="-created_at")
        all_runs.extend(list(runs))

    if not all_runs:
        print(f"No runs with states {states} found.")
        return

    print(f"Found {len(all_runs)} runs to clean up:")
    print(f"{'Run Name':<30} {'State':<12} {'Branch':<25} {'Created':<20}")
    print("-" * 87)
    for run in all_runs:
        branch = run.config.get("branch", "N/A")
        print(f"{run.name:<30} {run.state:<12} {branch:<25} {run.created_at:<20}")

    if args.dry_run:
        print("\nDry run — no runs deleted.")
        return

    if not args.force:
        confirm = input(f"\nDelete all {len(all_runs)} runs? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

    for run in all_runs:
        run.delete(delete_artifacts=args.delete_artifacts)
        print(f"  Deleted: {run.name}")

    print(f"\nCleaned up {len(all_runs)} runs.")


# ── cancel ───────────────────────────────────────────────────────────────────


def cmd_cancel(args):
    """Mark running runs for cancellation by updating their tags."""
    api = get_api()

    if args.branch:
        run = get_run_by_branch(api, args.entity, args.project, args.branch)
        runs_to_cancel = [run]
    elif args.all_running:
        path = f"{args.entity}/{args.project}" if args.entity else args.project
        runs = api.runs(path, filters={"state": "running"}, order="-created_at")
        runs_to_cancel = list(runs)
    else:
        run = resolve_run(api, args.entity, args.project, args.run_id, None)
        runs_to_cancel = [run]

    if not runs_to_cancel:
        print("No running runs found.")
        return

    for run in runs_to_cancel:
        branch = run.config.get("branch", "N/A")
        print(f"Cancelling: {run.name} (branch: {branch}, state: {run.state})")
        if run.state == "running":
            run.tags = list(set(run.tags + ["cancelled"]))
            run.update()
            print(f"  Tagged as 'cancelled'. The running process should check for this tag and exit.")
        else:
            print(f"  Skipped — state is '{run.state}', not running.")

    print("\nNote: Tagging as 'cancelled' is advisory. To force-stop, cancel the job in the WandB Launch UI.")


# ── main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Manage WandB runs.")
    parser.add_argument("--project", default=os.environ.get("WANDB_PROJECT"), help="WandB project name (default: $WANDB_PROJECT).")
    parser.add_argument("--entity", default=os.environ.get("WANDB_ENTITY"), help="WandB entity (default: $WANDB_ENTITY).")
    parser.add_argument("--json", action="store_true", help="JSON output.")

    sub = parser.add_subparsers(dest="command", required=True)

    # tag
    p = sub.add_parser("tag", help="Add/remove tags on a run.")
    p.add_argument("--run-id", default=None, help="Run ID.")
    p.add_argument("--branch", default=None, help="Branch name (uses latest run).")
    p.add_argument("--add", default=None, help="Comma-separated tags to add.")
    p.add_argument("--remove", default=None, help="Comma-separated tags to remove.")

    # note
    p = sub.add_parser("note", help="Add notes to a run.")
    p.add_argument("--run-id", default=None, help="Run ID.")
    p.add_argument("--branch", default=None, help="Branch name.")
    p.add_argument("--text", required=True, help="Note text.")
    p.add_argument("--append", action="store_true", help="Append to existing notes.")

    # delete
    p = sub.add_parser("delete", help="Delete a run.")
    p.add_argument("--run-id", default=None, help="Run ID.")
    p.add_argument("--branch", default=None, help="Branch name.")
    p.add_argument("--delete-artifacts", action="store_true", help="Also delete associated artifacts.")
    p.add_argument("--force", action="store_true", help="Skip confirmation.")

    # cleanup
    p = sub.add_parser("cleanup", help="Bulk delete crashed/failed runs.")
    p.add_argument("--states", default="crashed,failed", help="Comma-separated states to clean (default: crashed,failed).")
    p.add_argument("--delete-artifacts", action="store_true", help="Also delete artifacts.")
    p.add_argument("--force", action="store_true", help="Skip confirmation.")
    p.add_argument("--dry-run", action="store_true", help="List without deleting.")

    # cancel
    p = sub.add_parser("cancel", help="Cancel running runs.")
    p.add_argument("--run-id", default=None, help="Run ID.")
    p.add_argument("--branch", default=None, help="Branch name.")
    p.add_argument("--all-running", action="store_true", help="Cancel all running runs.")

    args = parser.parse_args()
    if not args.project:
        parser.error("--project is required (or set WANDB_PROJECT env var)")
    cmds = {"tag": cmd_tag, "note": cmd_note, "delete": cmd_delete, "cleanup": cmd_cleanup, "cancel": cmd_cancel}
    cmds[args.command](args)


if __name__ == "__main__":
    main()
