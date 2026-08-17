"""Parse composition.csv files.

Compositions has a more complex representation in RDF and requires
special handling.
"""

import argparse
import csv
import json
import warnings
from pathlib import Path
from typing import Optional

from tripper import Namespace, Session, Triplestore
from tripper.datadoc import store

from utils import atomic_masses, get_emmo, get_species, get_unit, normalize_unit

TEMPLATE_URL = (
    "https://github.com/SINTEF/physmet-data-documentation-templates/"
    "blob/main/templates/compositions.csv"
)

EMMO = Namespace(
    "https://w3id.org/emmo#",
    label_annotations=True,
    triplestore=get_emmo,
    check=True,
)




def parse(filename: Path, **spec) -> list:
    """Parse a CSV file with chemical compositions.

    Args:
        filename: CSV file to parse.
        spec: Keyword arguments to csv.reader() for specifying how `filename`
            is formatted.

    Returns:
        List of compositions correctly represented according to EMMO.
    """
    conf = spec if spec else {}
    with open(filename, newline="", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, **conf)
        header = [h.strip() for h in next(reader)]

        # Array of indices for columns with chemical compositions
        icomp = [
            i for i, h in enumerate(header) if h.split("[")[0] in atomic_names
        ]

        # Chemical symbols
        symbols = [header[i].split("[", 1)[0] for i in icomp]

        # Determine unit
        unitname = None
        for i in icomp:
            u = normalize_unit(
                header[i].split("[")[1].rstrip("]") if "[" in h else "wt%"
            )
            if unitname is None:
                unitname = u
            elif u != unitname:
                raise ValueError("All compositions must have the same unit")
        quantity, unit = get_unit(unitname)

        compositions = []
        for row in reader:
            d = {
                "@id": [cell for h, cell in zip(header, row) if h == "@id"][0],
                "@type": EMMO:ChemicalComposition,
                "hasSingleComponentComposition": [],
                # TODO: include other non-composition annotations
            }
            values = to_wtpercent([row[i] for i in icomp], symbols, unitname)
            for symbol, v in zip(symbols, values):
                species = get_species(symbol)
                d["hasSingleComponentComposition"].append(
                    {
                        "@type": EMMO.SingleComponentComposition,
                        "hasSpeciesPart": species,
                        "hasQuantityPart": {
                            "@type": quantity,
                            "hasMeasurementUnit": unit,
                            "dataValue": v,
                        },
                    }
                )
            compositions.append(d)

    return compositions


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Converts CSV with chemical composition to RDF.",
        epilog="The output can be specified with either the "
        "--triplestore/--config options or with the --backend/"
        "--base-iri/--database/--package options."
    )
    parser.add_argument(
        "csvfile",
        metavar="PATH",
        help=(
            "CSV file with compositions. For an example file, see "
            f"{TEMPLATE_URL}"
        ),
    )
    parser.add_argument(
        "--config",
        "-c",
        metavar="PATH",
        type=Path,
        help="Tripper session configuration file.",
    )
    parser.add_argument(
        "--triplestore",
        "-t",
        metavar="NAME",
        help=(
            "Name of triplestore to connect to. The name should be "
            "defined in the session configuration file."
        ),
    )
    parser.add_argument(
        "--backend",
        "-b",
        default="rdflib",
        help=(
            'Triplestore backend to use. Defaults to "rdflib" - an '
            "in-memory rdflib triplestore, that can be pre-loaded with "
            "--parse."
        ),
    )
    parser.add_argument(
        "--base-iri",
        "-B",
        help="Base IRI of the triplestore.",
    )
    parser.add_argument(
        "--database",
        "-d",
        help="Name of database to connect to (for backends supporting it).",
    )
    parser.add_argument(
        "--package",
        help="Only needed when `backend` is a relative module.",
    )
    parser.add_argument(
        "--parse",
        "-p",
        metavar="LOCATION",
        help="Load triplestore from this location.",
    )
    parser.add_argument(
        "--parse-format",
        "-F",
        help="Used with `--parse`. Format to use when parsing triplestore.",
    )
    parser.add_argument(
        "--prefix",
        "-P",
        action="append",
        metavar="PREFIX=URL",
        help=(
            "Namespace prefix to bind to the triplestore. "
            "This option can be given multiple times."
        ),
    )

    args = parser.parse_args()

    if args.triplestore:
        session = Session(config=args.config)
        ts = session.get_triplestore(args.triplestore)
    else:
        ts = Triplestore(
            backend=args.backend,
            base_iri=args.base_iri,
            database=args.database,
            package=args.package,
        )

    if args.parse:
        ts.parse(args.parse, format=args.parse_format)

    if args.prefix:
        for token in args.prefix:
            prefix, ns = token.split("=", 1)
            ts.bind(prefix, ns)

    compositions = parse(args.csvfile)
    store(ts, compositions)


if __name__ == "__main__":
    main()
