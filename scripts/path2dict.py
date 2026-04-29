#!/usr/bin/env python3
# Get information from path to a dict (json)

import argparse
import json
from pathlib import Path
import csv
import sys
from typing import Optional


def _parse_slash_config(config, option_name):
    tokens = [token.strip() for token in config.split("/")]
    if not tokens:
        raise ValueError(f"{option_name} must contain at least one field")
    return tokens


def _parse_template_mappings(templates):
    mapping = {}
    for template_arg in templates or []:
        predicate, sep, template = template_arg.partition("=")
        predicate = predicate.strip()
        template = template.strip()

        if not sep or not predicate or not template:
            raise ValueError(
                "--template must be on the form PREDICATE=TEMPLATE"
            )
        if "{value}" not in template:
            raise ValueError(
                "--template must contain the '{value}' placeholder"
            )
        if predicate in mapping and mapping[predicate] != template:
            raise ValueError(
                f"conflicting --template definitions for predicate '{predicate}'"
            )
        mapping[predicate] = template

    return mapping


def _transform_value(value, key, templates=None):
    if templates and key in templates:
        return templates[key].format(value=value)
    return value


def _build_datadoc(
    parts,
    keys,
    store_path,
    templates=None,
):
    result = {}

    for key, value in zip(keys, parts):
        if key:  # skip empty key names
            result[key] = _transform_value(
                value,
                key,
                templates=templates,
            )
    if store_path:
        result[store_path] = "/".join(parts)

    return result


def find_datadocs(
    root,
    keys,
    store_path: Optional[str] = "localPath",
    templates=None,
):
    """ If store_path, also store the full path in a variable with that name.
    E.g. store_path = "localPath" would produce localPath="data/JM12/SEM/EDS"
    """
    root = Path(root).resolve()

    # sanity check
    if not root.is_dir():
        raise ValueError(f"{root} is not a directory")

    results = []

    def walk(current_path, depth, parts):
        if depth == len(keys):
            results.append(
                _build_datadoc(
                    parts,
                    keys,
                    store_path,
                    templates=templates,
                )
            )
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
        help='''Slash-separated field mapping, (default: %(default)s)".

        Starting with a slash (e.g. /user) will ignore the root-directory.
        Empty values like user//inst will cause the middle directory names to
        not be stored.'''
    )
    parser.add_argument(
        "--template",
        action="append",
        default=[],
        metavar="PREDICATE=TEMPLATE",
        help="""Template for minting object values for a predicate from
        --config. May be given multiple times. Use "{value}" as the path
        segment placeholder, e.g. processedFrom=physmet:sample/{value}."""
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
    parser.add_argument(
        "--store_path",
        default="localPath",
        help="""Store path in a key (default: %(default)s). To not store, set
        to 'None'."""
    )

    args = parser.parse_args()

    if args.store_path.lower() == "none":
        args.store_path = None

    keys = _parse_slash_config(args.config, "--config")
    templates = _parse_template_mappings(args.template)

    results = find_datadocs(
        args.path,
        keys,
        store_path=args.store_path,
        templates=templates,
    )

    if args.json:
        print(json.dumps(results, indent=2))
    elif args.csv:
        if args.store_path:
            keys.append(args.store_path)
        keys = [k for k in keys if k]
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
