"""Fetch and analyze WandB run results for branch evaluation.

Usage:
    python .claude/skills/check-results/check_results.py --project <project> [options]

Subcommands:
    status    - Check run status for branches (running, finished, crashed, etc.)
    summary   - Fetch summary metrics for finished runs, compare across branches
    history   - Fetch full metric history for a specific run/branch
    compare   - Side-by-side comparison of branches on key metrics
    artifacts - List artifacts logged by runs
    diagnose  - Diagnose failed/crashed runs with logs and system metrics
    report    - Full report across all branches for winner selection

This is the primary tool for evaluating experiment branches and deciding
which branches to merge into main.
"""

import argparse
import json
import os
import subprocess
import sys
from typing import Optional

import wandb


def get_api() -> wandb.Api:
    return wandb.Api()


def get_runs_by_branch(
    api: wandb.Api,
    entity: Optional[str],
    project: str,
    branch: Optional[str] = None,
    state: Optional[str] = None,
) -> list:
    """Fetch runs filtered by branch and/or state."""
    path = f"{entity}/{project}" if entity else project
    filters = {}
    if branch:
        filters["config.branch"] = branch
    if state:
        filters["state"] = state
    runs = api.runs(path, filters=filters, order="-created_at")
    return list(runs)


def get_latest_run_per_branch(
    api: wandb.Api,
    entity: Optional[str],
    project: str,
    state: Optional[str] = None,
) -> dict:
    """Get the most recent run for each branch."""
    runs = get_runs_by_branch(api, entity, project, state=state)
    branch_runs = {}
    for run in runs:
        branch = run.config.get("branch")
        if branch and branch not in branch_runs:
            branch_runs[branch] = run
    return branch_runs


# ── Subcommand: status ──────────────────────────────────────────────────────


def cmd_status(args):
    """Show run status for all branches or a specific branch."""
    api = get_api()
    runs = get_runs_by_branch(api, args.entity, args.project, branch=args.branch)

    if not runs:
        print("No runs found.")
        return

    print(f"{'Branch':<30} {'Run Name':<30} {'State':<12} {'Created':<20}")
    print("-" * 92)
    for run in runs:
        branch = run.config.get("branch", "N/A")
        print(f"{branch:<30} {run.name:<30} {run.state:<12} {run.created_at:<20}")


# ── Subcommand: summary ─────────────────────────────────────────────────────


def cmd_summary(args):
    """Fetch summary metrics for finished runs."""
    api = get_api()
    branch_runs = get_latest_run_per_branch(
        api, args.entity, args.project, state="finished"
    )

    if not branch_runs:
        print("No finished runs found.")
        return

    # Determine metric keys to display
    metric_keys = None
    if args.metrics:
        metric_keys = [m.strip() for m in args.metrics.split(",")]
    else:
        # Auto-detect: collect all numeric summary keys across runs
        all_keys = set()
        for run in branch_runs.values():
            for k, v in run.summary.items():
                if not k.startswith("_") and isinstance(v, (int, float)):
                    all_keys.add(k)
        metric_keys = sorted(all_keys)

    if not metric_keys:
        print("No numeric metrics found in run summaries.")
        return

    # Print table
    header = f"{'Branch':<30}" + "".join(f"{k:<20}" for k in metric_keys)
    print(header)
    print("-" * len(header))

    for branch, run in sorted(branch_runs.items()):
        values = []
        for k in metric_keys:
            v = run.summary.get(k)
            if isinstance(v, float):
                values.append(f"{v:<20.6f}")
            elif v is not None:
                values.append(f"{str(v):<20}")
            else:
                values.append(f"{'N/A':<20}")
        print(f"{branch:<30}" + "".join(values))

    # JSON output
    if args.json:
        output = {}
        for branch, run in sorted(branch_runs.items()):
            output[branch] = {
                "run_id": run.id,
                "run_name": run.name,
                "metrics": {
                    k: run.summary.get(k)
                    for k in metric_keys
                    if run.summary.get(k) is not None
                },
                "config": dict(run.config),
            }
        print("\n" + json.dumps(output, indent=2, default=str))


# ── Subcommand: history ──────────────────────────────────────────────────────


def cmd_history(args):
    """Fetch full metric history for a branch's latest run."""
    api = get_api()
    runs = get_runs_by_branch(
        api, args.entity, args.project, branch=args.branch, state="finished"
    )

    if not runs:
        print(f"No finished runs found for branch '{args.branch}'.")
        return

    run = runs[0]  # latest
    print(f"Run: {run.name} (ID: {run.id})")
    print(f"Branch: {args.branch}")
    print(f"State: {run.state}")
    print()

    # Determine keys
    keys = None
    if args.metrics:
        keys = [m.strip() for m in args.metrics.split(",")]

    # Fetch history
    history = list(run.scan_history(keys=keys))

    if not history:
        print("No history records found.")
        return

    if args.json:
        print(json.dumps(history, indent=2, default=str))
        return

    # Print as table (first and last N rows)
    if keys is None:
        keys = [k for k in history[0].keys() if not k.startswith("_")]

    header = f"{'step':<10}" + "".join(f"{k:<20}" for k in keys)
    print(header)
    print("-" * len(header))

    display_rows = history
    if len(history) > args.rows:
        display_rows = history[: args.rows // 2] + history[-(args.rows // 2) :]
        mid = args.rows // 2
    else:
        mid = None

    for i, row in enumerate(display_rows):
        if mid is not None and i == mid:
            print(f"{'...':<10}" + "".join(f"{'...':<20}" for _ in keys))
        step = row.get("_step", "?")
        vals = []
        for k in keys:
            v = row.get(k)
            if isinstance(v, float):
                vals.append(f"{v:<20.6f}")
            elif v is not None:
                vals.append(f"{str(v):<20}")
            else:
                vals.append(f"{'':<20}")
        print(f"{str(step):<10}" + "".join(vals))


# ── Subcommand: compare ─────────────────────────────────────────────────────


def cmd_compare(args):
    """Side-by-side comparison of branches on key metrics."""
    api = get_api()
    branch_runs = get_latest_run_per_branch(
        api, args.entity, args.project, state="finished"
    )

    if not branch_runs:
        print("No finished runs found.")
        return

    # Filter to requested branches if specified
    if args.branches:
        selected = [b.strip() for b in args.branches.split(",")]
        branch_runs = {b: r for b, r in branch_runs.items() if b in selected}

    if not branch_runs:
        print("No matching branches found.")
        return

    # Determine metrics
    if args.metrics:
        metric_keys = [m.strip() for m in args.metrics.split(",")]
    else:
        all_keys = set()
        for run in branch_runs.values():
            for k, v in run.summary.items():
                if not k.startswith("_") and isinstance(v, (int, float)):
                    all_keys.add(k)
        metric_keys = sorted(all_keys)

    if not metric_keys:
        print("No numeric metrics found.")
        return

    # Compare: for each metric find best
    print(f"\n{'Metric':<25}", end="")
    branches = sorted(branch_runs.keys())
    for b in branches:
        print(f"{b:<25}", end="")
    print(f"{'Best':<25}")
    print("-" * (25 * (len(branches) + 2)))

    results = {}
    for metric in metric_keys:
        values = {}
        for b in branches:
            v = branch_runs[b].summary.get(metric)
            if isinstance(v, (int, float)):
                values[b] = v

        # Determine direction (higher or lower is better)
        # Heuristic: "loss", "error" → lower is better; else higher
        lower_better = any(
            kw in metric.lower() for kw in ["loss", "error", "perplexity", "mse", "mae", "rmse"]
        )

        best_branch = None
        if values:
            if lower_better:
                best_branch = min(values, key=values.get)
            else:
                best_branch = max(values, key=values.get)

        print(f"{metric:<25}", end="")
        for b in branches:
            v = values.get(b)
            if v is not None:
                marker = " *" if b == best_branch else ""
                print(f"{v:<23.6f}{marker:>2}", end="")
            else:
                print(f"{'N/A':<25}", end="")
        print(f"{best_branch or 'N/A':<25}")

        results[metric] = {
            "values": values,
            "best": best_branch,
            "lower_is_better": lower_better,
        }

    if args.json:
        print("\n" + json.dumps(results, indent=2, default=str))

    # Win count summary
    print(f"\n{'── Win Count ──':^{25 * (len(branches) + 2)}}")
    win_counts = {b: 0 for b in branches}
    for info in results.values():
        if info["best"] and info["best"] in win_counts:
            win_counts[info["best"]] += 1

    print(f"{'Branch':<25} {'Wins':<10}")
    print("-" * 35)
    for b in sorted(win_counts, key=win_counts.get, reverse=True):
        print(f"{b:<25} {win_counts[b]:<10}")


# ── Subcommand: artifacts ────────────────────────────────────────────────────


def cmd_artifacts(args):
    """List artifacts logged by runs for a branch."""
    api = get_api()
    runs = get_runs_by_branch(api, args.entity, args.project, branch=args.branch)

    if not runs:
        print(f"No runs found for branch '{args.branch}'.")
        return

    run = runs[0]
    print(f"Run: {run.name} (ID: {run.id})")
    print(f"Branch: {args.branch}")
    print()

    print(f"{'Name':<40} {'Type':<15} {'Size':<15} {'Aliases':<20}")
    print("-" * 90)
    for artifact in run.logged_artifacts():
        aliases = ", ".join(a.alias for a in artifact.aliases) if artifact.aliases else ""
        size = artifact.size if hasattr(artifact, "size") else "N/A"
        if isinstance(size, (int, float)) and size > 0:
            if size > 1e9:
                size_str = f"{size / 1e9:.1f} GB"
            elif size > 1e6:
                size_str = f"{size / 1e6:.1f} MB"
            elif size > 1e3:
                size_str = f"{size / 1e3:.1f} KB"
            else:
                size_str = f"{size} B"
        else:
            size_str = "N/A"
        print(f"{artifact.name:<40} {artifact.type:<15} {size_str:<15} {aliases:<20}")


# ── Subcommand: diagnose ────────────────────────────────────────────────────


def cmd_diagnose(args):
    """Diagnose failed/crashed runs with logs and system metrics."""
    api = get_api()

    if args.branch:
        runs = get_runs_by_branch(api, args.entity, args.project, branch=args.branch)
    else:
        # Get all non-finished runs
        runs = get_runs_by_branch(api, args.entity, args.project)
        runs = [r for r in runs if r.state in ("crashed", "failed", "killed", "preempted")]

    if not runs:
        print("No problematic runs found.")
        return

    for run in runs[:args.limit]:
        branch = run.config.get("branch", "N/A")
        print(f"{'=' * 80}")
        print(f"Run:     {run.name} (ID: {run.id})")
        print(f"Branch:  {branch}")
        print(f"State:   {run.state}")
        print(f"Created: {run.created_at}")
        print()

        # Config
        print("── Config ──")
        for k, v in sorted(run.config.items()):
            if not k.startswith("_"):
                print(f"  {k}: {v}")
        print()

        # Summary (may contain error info)
        print("── Summary ──")
        for k, v in sorted(run.summary.items()):
            if not k.startswith("_"):
                if isinstance(v, float):
                    print(f"  {k}: {v:.6f}")
                else:
                    print(f"  {k}: {v}")
        print()

        # System metrics
        sys_metrics = run.summary.get("_wandb", {}).get("runtime")
        if sys_metrics is not None:
            print(f"── Runtime: {sys_metrics:.1f}s ──")

        # Last N history rows (to see where it stopped)
        print("── Last History Steps ──")
        history = list(run.scan_history())
        tail = history[-5:] if len(history) >= 5 else history
        for row in tail:
            step = row.get("_step", "?")
            filtered = {
                k: (f"{v:.6f}" if isinstance(v, float) else v)
                for k, v in row.items()
                if not k.startswith("_")
            }
            print(f"  step {step}: {filtered}")

        if not history:
            print("  (no history logged)")
        print()

        # Files: try to get output.log
        print("── Log Tail ──")
        try:
            log_file = run.file("output.log")
            log_content = log_file.download(replace=True).read().decode("utf-8", errors="replace")
            lines = log_content.strip().split("\n")
            for line in lines[-20:]:
                print(f"  {line}")
        except Exception:
            print("  (output.log not available)")

        print()


# ── Subcommand: report ───────────────────────────────────────────────────────


def cmd_report(args):
    """Full report across all branches for winner selection."""
    api = get_api()
    all_runs = get_runs_by_branch(api, args.entity, args.project)
    branch_runs = get_latest_run_per_branch(api, args.entity, args.project)

    if not branch_runs:
        print("No runs found.")
        return

    # ── Overview ──
    print("=" * 80)
    print("EXPERIMENT REPORT")
    print("=" * 80)
    print(f"Project: {args.entity + '/' if args.entity else ''}{args.project}")
    print(f"Total runs: {len(all_runs)}")
    print(f"Branches: {len(branch_runs)}")
    print()

    # ── Status per branch ──
    print("── Branch Status ──")
    print(f"{'Branch':<30} {'State':<12} {'Run':<25} {'Created':<20}")
    print("-" * 87)
    for branch in sorted(branch_runs):
        run = branch_runs[branch]
        print(f"{branch:<30} {run.state:<12} {run.name:<25} {run.created_at:<20}")
    print()

    # ── Finished branches: metric comparison ──
    finished = {b: r for b, r in branch_runs.items() if r.state == "finished"}
    problematic = {b: r for b, r in branch_runs.items() if r.state in ("crashed", "failed", "killed")}
    running = {b: r for b, r in branch_runs.items() if r.state == "running"}

    if finished:
        # Collect all numeric metrics
        all_keys = set()
        for run in finished.values():
            for k, v in run.summary.items():
                if not k.startswith("_") and isinstance(v, (int, float)):
                    all_keys.add(k)

        if args.metrics:
            metric_keys = [m.strip() for m in args.metrics.split(",")]
        else:
            metric_keys = sorted(all_keys)

        if metric_keys:
            print("── Metric Comparison (Finished Runs) ──")
            branches = sorted(finished.keys())

            header = f"{'Metric':<25}" + "".join(f"{b:<25}" for b in branches)
            print(header)
            print("-" * len(header))

            win_counts = {b: 0 for b in branches}

            for metric in metric_keys:
                values = {}
                for b in branches:
                    v = finished[b].summary.get(metric)
                    if isinstance(v, (int, float)):
                        values[b] = v

                lower_better = any(
                    kw in metric.lower()
                    for kw in ["loss", "error", "perplexity", "mse", "mae", "rmse"]
                )

                best = None
                if values:
                    best = min(values, key=values.get) if lower_better else max(values, key=values.get)
                    if best:
                        win_counts[best] += 1

                print(f"{metric:<25}", end="")
                for b in branches:
                    v = values.get(b)
                    if v is not None:
                        marker = " *" if b == best else ""
                        print(f"{v:<23.6f}{marker:>2}", end="")
                    else:
                        print(f"{'N/A':<25}", end="")
                print()

            print()
            print("── Win Count ──")
            print(f"{'Branch':<30} {'Wins':<10}")
            print("-" * 40)
            for b in sorted(win_counts, key=win_counts.get, reverse=True):
                print(f"{b:<30} {win_counts[b]:<10}")
            print()

    # ── Hyperparameter diff ──
    if len(finished) > 1:
        print("── Hyperparameter Diff (Finished Runs) ──")
        all_config_keys = set()
        for run in finished.values():
            all_config_keys.update(
                k for k in run.config if not k.startswith("_") and k not in ("branch", "commit")
            )

        branches = sorted(finished.keys())
        header = f"{'Param':<30}" + "".join(f"{b:<25}" for b in branches)
        print(header)
        print("-" * len(header))

        for key in sorted(all_config_keys):
            values = [finished[b].config.get(key, "N/A") for b in branches]
            # Only show if there's a diff
            if len(set(str(v) for v in values)) > 1:
                print(f"{key:<30}" + "".join(f"{str(v):<25}" for v in values))
        print()

    # ── Problematic runs ──
    if problematic:
        print("── Problematic Runs (Need Attention) ──")
        for branch, run in sorted(problematic.items()):
            print(f"  {branch:<30} {run.state:<12} {run.name}")
        print()

    # ── Still running ──
    if running:
        print("── Still Running ──")
        for branch, run in sorted(running.items()):
            print(f"  {branch:<30} {run.name}")
        print()

    # ── Recommendations ──
    if finished:
        print("── Recommendations ──")
        if len(finished) == 1:
            b = list(finished.keys())[0]
            print(f"  Only one finished branch: {b}. Review metrics to decide.")
        else:
            # Rank by win count
            branches = sorted(finished.keys())
            win_counts_final = {b: 0 for b in branches}
            for metric in metric_keys:
                values = {}
                for b in branches:
                    v = finished[b].summary.get(metric)
                    if isinstance(v, (int, float)):
                        values[b] = v
                lower_better = any(
                    kw in metric.lower()
                    for kw in ["loss", "error", "perplexity", "mse", "mae", "rmse"]
                )
                if values:
                    best = min(values, key=values.get) if lower_better else max(values, key=values.get)
                    win_counts_final[best] += 1

            ranked = sorted(win_counts_final, key=win_counts_final.get, reverse=True)
            print(f"  Recommended winners (by metric win count):")
            for b in ranked:
                print(f"    {b}: {win_counts_final[b]} metric wins")

    # JSON output
    if args.json:
        report = {
            "project": args.project,
            "entity": args.entity,
            "total_runs": len(all_runs),
            "branches": {},
        }
        for branch, run in branch_runs.items():
            metrics = {
                k: v
                for k, v in run.summary.items()
                if not k.startswith("_") and isinstance(v, (int, float))
            }
            report["branches"][branch] = {
                "state": run.state,
                "run_id": run.id,
                "run_name": run.name,
                "config": {
                    k: v for k, v in run.config.items() if not k.startswith("_")
                },
                "metrics": metrics,
            }
        print("\n" + json.dumps(report, indent=2, default=str))


# ── Subcommand: post-pr ──────────────────────────────────────────────────────


def cmd_post_pr(args):
    """Post results as a comment on the branch's GitHub PR and update labels."""
    api = get_api()
    branch = args.branch

    # Find PR for this branch
    result = subprocess.run(
        ["gh", "pr", "list", "--head", branch, "--json", "number,url", "--limit", "1"],
        capture_output=True, text=True,
    )
    prs = json.loads(result.stdout) if result.stdout.strip() else []
    if not prs:
        print(f"No PR found for branch '{branch}'.")
        return

    pr_number = prs[0]["number"]
    pr_url = prs[0]["url"]
    print(f"PR #{pr_number}: {pr_url}")

    # Get run data
    runs = get_runs_by_branch(api, args.entity, args.project, branch=branch)
    if not runs:
        print(f"No WandB runs found for branch '{branch}'.")
        return

    run = runs[0]

    # Build comment body
    lines = [f"## WandB Results: `{branch}`", ""]
    lines.append(f"**Run:** {run.name} (ID: `{run.id}`)")
    lines.append(f"**State:** {run.state}")
    lines.append("")

    if run.state == "finished":
        # Metrics table
        metrics = {
            k: v for k, v in run.summary.items()
            if not k.startswith("_") and isinstance(v, (int, float))
        }
        if metrics:
            lines.append("### Metrics")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            for k in sorted(metrics):
                v = metrics[k]
                lines.append(f"| {k} | {v:.6f} |" if isinstance(v, float) else f"| {k} | {v} |")
            lines.append("")

        # Compare vs baseline if available
        baseline_runs = get_runs_by_branch(api, args.entity, args.project, branch="main", state="finished")
        if baseline_runs:
            baseline = baseline_runs[0]
            baseline_metrics = {
                k: v for k, v in baseline.summary.items()
                if not k.startswith("_") and isinstance(v, (int, float))
            }
            common = set(metrics.keys()) & set(baseline_metrics.keys())
            if common:
                lines.append("### vs Baseline (main)")
                lines.append("")
                lines.append("| Metric | Baseline | This Branch | Delta |")
                lines.append("|--------|----------|-------------|-------|")
                for k in sorted(common):
                    bv = baseline_metrics[k]
                    ev = metrics[k]
                    delta = ev - bv
                    sign = "+" if delta > 0 else ""
                    lines.append(f"| {k} | {bv:.6f} | {ev:.6f} | {sign}{delta:.6f} |")
                lines.append("")

        # Update label
        subprocess.run(
            ["gh", "pr", "edit", str(pr_number), "--add-label", "experiment:finished"],
            capture_output=True,
        )

    elif run.state in ("crashed", "failed", "killed"):
        lines.append(f"**⚠ Run {run.state}.** Use `/fix-and-relaunch {branch}` to diagnose and fix.")
        subprocess.run(
            ["gh", "pr", "edit", str(pr_number), "--add-label", f"experiment:{run.state}"],
            capture_output=True,
        )

    elif run.state == "running":
        step = run.lastHistoryStep if run.lastHistoryStep >= 0 else "N/A"
        lines.append(f"**Currently running.** Step: {step}")
        subprocess.run(
            ["gh", "pr", "edit", str(pr_number), "--add-label", "experiment:running"],
            capture_output=True,
        )

    comment_body = "\n".join(lines)

    # Post comment
    subprocess.run(
        ["gh", "pr", "comment", str(pr_number), "--body", comment_body],
        check=True,
    )
    print(f"Posted results to PR #{pr_number}")


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and analyze WandB run results for branch evaluation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--project", default=os.environ.get("WANDB_PROJECT"), help="WandB project name (default: $WANDB_PROJECT).")
    parser.add_argument("--entity", default=os.environ.get("WANDB_ENTITY"), help="WandB entity (default: $WANDB_ENTITY).")
    parser.add_argument("--json", action="store_true", help="Output results as JSON.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    p = subparsers.add_parser("status", help="Check run status for branches.")
    p.add_argument("--branch", default=None, help="Filter to specific branch.")

    # summary
    p = subparsers.add_parser("summary", help="Summary metrics for finished runs.")
    p.add_argument("--metrics", default=None, help="Comma-separated metric names.")

    # history
    p = subparsers.add_parser("history", help="Full metric history for a branch.")
    p.add_argument("--branch", required=True, help="Branch name.")
    p.add_argument("--metrics", default=None, help="Comma-separated metric names.")
    p.add_argument("--rows", type=int, default=40, help="Max rows to display (default: 40).")

    # compare
    p = subparsers.add_parser("compare", help="Side-by-side branch comparison.")
    p.add_argument("--branches", default=None, help="Comma-separated branch names (default: all).")
    p.add_argument("--metrics", default=None, help="Comma-separated metric names.")

    # artifacts
    p = subparsers.add_parser("artifacts", help="List artifacts for a branch.")
    p.add_argument("--branch", required=True, help="Branch name.")

    # diagnose
    p = subparsers.add_parser("diagnose", help="Diagnose failed/crashed runs.")
    p.add_argument("--branch", default=None, help="Branch name (default: all problematic).")
    p.add_argument("--limit", type=int, default=5, help="Max runs to diagnose (default: 5).")

    # report
    p = subparsers.add_parser("report", help="Full report for winner selection.")
    p.add_argument("--metrics", default=None, help="Comma-separated metric names to focus on.")

    # post-pr
    p = subparsers.add_parser("post-pr", help="Post results as PR comment.")
    p.add_argument("--branch", required=True, help="Branch name.")

    args = parser.parse_args()

    commands = {
        "status": cmd_status,
        "summary": cmd_summary,
        "history": cmd_history,
        "compare": cmd_compare,
        "artifacts": cmd_artifacts,
        "diagnose": cmd_diagnose,
        "report": cmd_report,
        "post-pr": cmd_post_pr,
    }

    if not args.project:
        parser.error("--project is required (or set WANDB_PROJECT env var)")

    commands[args.command](args)


if __name__ == "__main__":
    main()
