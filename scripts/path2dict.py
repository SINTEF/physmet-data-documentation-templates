#!/usr/bin/env python3
# Get information from path to a dict (json)

import argparse
import json
from pathlib import Path
import csv
import re
import sys
from typing import Optional


def _parse_slash_config(config, option_name):
    tokens = [token.strip() for token in config.split("/")]
    if not tokens:
        raise ValueError(f"{option_name} must contain at least one field")
    return tokens


PLACEHOLDER_PATTERN = re.compile(r"\{([^{}]+)\}")


def _parse_template_mappings(templates):
    mapping = {}
    ordered_templates = []
    for template_arg in templates or []:
        target, sep, template = template_arg.partition("=")
        target = target.strip()
        template = template.strip()

        if not sep or not target or not template:
            raise ValueError(
                "--template must be on the form FIELD=TEMPLATE"
            )
        if target in mapping and mapping[target] != template:
            raise ValueError(
                f"conflicting --template definitions for field '{target}'"
            )
        if target not in mapping:
            ordered_templates.append((target, template))
        mapping[target] = template

    return ordered_templates


def _render_template(template, context):
    def replace(match):
        field_name = match.group(1)
        if field_name not in context:
            raise ValueError(
                f"--template references unknown field '{field_name}'"
            )
        return context[field_name]

    return PLACEHOLDER_PATTERN.sub(replace, template)


def _build_datadoc(
    parts,
    keys,
    store_path,
    templates=None,
):
    result = {}

    for key, value in zip(keys, parts):
        if key:  # skip empty key names
            result[key] = value
    if store_path:
        result[store_path] = "/".join(parts)

    for target, template in templates or []:
        result[target] = _render_template(template, result)

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
        metavar="FIELD=TEMPLATE",
        help="""Template for assigning or deriving field values. May be given
        multiple times. Templates can reference extracted fields as
        "{fieldName}", for example processedFrom=physmet:sample/{processedFrom}
        or newProp={processedFrom}_{@id}."""
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
        fieldnames = [k for k in keys if k]
        if args.store_path:
            fieldnames.append(args.store_path)
        for target, _template in templates:
            if target not in fieldnames:
                fieldnames.append(target)
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    else:
        for r in results:
            for k, v in r.items():
                print(f"{k}=\"{v}\" / ", end="")
            print()

if __name__ == "__main__":
    main()
