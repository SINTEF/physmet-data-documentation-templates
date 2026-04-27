#!/usr/bin/env python3
# Get information from path to a dict (json)

import argparse
import json
from pathlib import Path
import csv
import sys

def build_datadoc(parts, keys):
    result = {}
    for key, value in zip(keys, parts):
        if key:  # skip empty key names
            result[key] = value

    return result

def find_datadocs(root, keys):
    root = Path(root).resolve()

    # sanity check
    if not root.is_dir():
        raise ValueError(f"{root} is not a directory")

    results = []

    def walk(current_path, depth, parts):
        if depth == len(keys):
            results.append(build_datadoc(parts, keys))
            return

        for child in current_path.iterdir():
            if child.is_dir():
                walk(child, depth + 1, parts + [child.name])

    # root corresponds to first key
    walk(root, 1, [root.name])

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Discover datadoc entries from a structured directory"
    )
    parser.add_argument(
        "path",
        help="Root path (corresponding to first config element)"
    )
    parser.add_argument(
        "--config",
        default="/user/sample/instrument/method/experiment",
        help='''Slash-separated structure, (default: %(default)s)".

        Not starting with a slash (e.g. user/) will ignore the root-directory.
        Empty values like user//inst will cause the middle directory names to
        not be stored.'''
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Output as CSV"
    )

    args = parser.parse_args()

    keys = [k.strip() for k in args.config.split("/")]

    if not keys:
        raise ValueError("Config must contain at least one field")

    results = find_datadocs(args.path, keys)

    if args.json:
        print(json.dumps(results, indent=2))
    elif args.csv:
        writer = csv.DictWriter(sys.stdout, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)
    else:
        for r in results:
            for k, v in r.items():
                print(f"{k}=\"{v}\" / ", end="")
            print()

if __name__ == "__main__":
    main()
