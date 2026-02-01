"""Quick data exploration and stats.

Usage:
    python misc/explore_data.py --path <data-dir>

Prints basic stats about a dataset directory. Customize for your data format.
"""

import argparse
import os


def main():
    parser = argparse.ArgumentParser(description="Explore dataset.")
    parser.add_argument("--path", required=True, help="Path to data directory.")
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"Path not found: {args.path}")
        return

    # File inventory
    total_files = 0
    total_size = 0
    extensions = {}

    for root, dirs, files in os.walk(args.path):
        for f in files:
            fp = os.path.join(root, f)
            size = os.path.getsize(fp)
            total_files += 1
            total_size += size
            ext = os.path.splitext(f)[1] or "(no ext)"
            extensions[ext] = extensions.get(ext, 0) + 1

    print(f"Path: {args.path}")
    print(f"Total files: {total_files}")
    print(f"Total size: {total_size / 1e6:.1f} MB")
    print()
    print("File types:")
    for ext, count in sorted(extensions.items(), key=lambda x: -x[1]):
        print(f"  {ext}: {count}")

    # TODO: Add project-specific data exploration
    # e.g., load samples, print shapes, show class distribution


if __name__ == "__main__":
    main()
