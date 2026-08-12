"""Script that parses CSV files defining shared resources.

It extract prefixes and stores them as a JSON-LD context.
"""

import argparse
import csv
import json
import sys
import warnings
from pathlib import Path
from typing import Optional


thisdir = Path(__file__).resolve().parent
default_files = [
    # "equipments.csv",  # no dedicated prefix for each equipment
    "organisations.csv",
    "people.csv",
    "projects.csv",
]


def parse(filename: Path, **spec) -> dict:
    """Parse a CSV file and return a dict with all prefixes defined in it.

    Args:
        filename: File to parse.
        spec: Dict with keyword arguments to csv.reader() for specifying
            how `filename` is formatted.
    """
    prefixes = {}
    conf = spec if spec else {}
    with open(filename, newline="") as csvfile:
        reader = csv.reader(csvfile, **conf)
        header = next(reader)
        if not "prefix" in header and not "namespace" in header:
            warnings.warn(
                f"{filename}: Missing 'prefix' or 'namespace' in header"
            )
            return {}
        iprefix = header.index("prefix")
        ins = header.index("namespace")
        for row in reader:
            prefix = row[iprefix]
            ns = row[ins]
            if prefix and ns:
                prefixes[prefix] = ns

    return prefixes


def write_jsonld(output: Optional[Path], prefixes: dict) -> None:
    """Write JSON-LD context.

    Args:
        output: File to write to. If None, write to stdout.
        prefixes: Dict mapping prefixes to corresponding namespaces.
    """
    context = {"@context": prefixes}
    jsonld = json.dumps(context, indent=2, sort_keys=False)
    if output:
        with open(output, "w") as f:
            f.write(jsonld)
    else:
        print(jsonld)


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Extract prefixes from CSV files defining shared resources."
    )
    parser.add_argument(
        "paths",
        metavar="PATH",
        default=["."],
        nargs="*",
        help=(
            "Directories or CSV files to parse. "
            "If no argument is given, it defaults to the current directory. "
            "If a directory is given, the following files within the directory "
            "are parsed (if they exists): "
            "organisations.csv, people.csv, projects.csv"
        ),
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="OUTPUT",
        type=Path,
        help="JSON-LD file to write. The default is to write to stdout.",
    )
    args = parser.parse_args()

    prefixes = {}

    for path in args.paths:
        abspath = Path(path).resolve()
        if abspath.is_dir:
            for filename in default_files:
                prefixes.update(parse(abspath / filename))
        else:
            prefixes.update(parse(abspath))

    write_jsonld(args.output, prefixes)


if __name__ == "__main__":
    main()
