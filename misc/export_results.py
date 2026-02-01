"""Export WandB results to local CSV files.

Usage:
    python misc/export_results.py --output results.csv [--metrics loss,accuracy]

Exports summary metrics for all finished runs to a CSV for external analysis.
"""

import argparse
import csv
import os

import wandb


def main():
    parser = argparse.ArgumentParser(description="Export WandB results to CSV.")
    parser.add_argument("--output", default="results.csv", help="Output CSV path.")
    parser.add_argument("--project", default=os.environ.get("WANDB_PROJECT"), help="WandB project.")
    parser.add_argument("--entity", default=os.environ.get("WANDB_ENTITY"), help="WandB entity.")
    parser.add_argument("--metrics", default=None, help="Comma-separated metrics to export (default: all).")
    args = parser.parse_args()

    if not args.project:
        parser.error("--project required (or set WANDB_PROJECT)")

    api = wandb.Api()
    path = f"{args.entity}/{args.project}" if args.entity else args.project
    runs = api.runs(path, filters={"state": "finished"}, order="-created_at")

    # Collect data
    rows = []
    all_keys = set()
    for run in runs:
        branch = run.config.get("branch", "N/A")
        row = {"run_name": run.name, "run_id": run.id, "branch": branch}
        for k, v in run.summary.items():
            if not k.startswith("_") and isinstance(v, (int, float)):
                row[k] = v
                all_keys.add(k)
        rows.append(row)

    if not rows:
        print("No finished runs found.")
        return

    # Filter metrics if specified
    if args.metrics:
        selected = [m.strip() for m in args.metrics.split(",")]
        all_keys = [k for k in selected if k in all_keys]
    else:
        all_keys = sorted(all_keys)

    # Write CSV
    fieldnames = ["run_name", "run_id", "branch"] + list(all_keys)
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported {len(rows)} runs to {args.output}")
    print(f"Metrics: {all_keys}")


if __name__ == "__main__":
    main()
