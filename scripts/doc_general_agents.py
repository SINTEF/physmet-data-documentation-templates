"""Populate ae KB with general agents, i.e. people, equipment,
projects and organisations.
"""
from pathlib import Path

from tripper import Triplestore
from tripper.datadoc import TableDoc, get_context, store

rootdir = Path(__file__).resolve().parent.parent
outdir = rootdir / "tests" / "output"
tablesdir = rootdir / "tables"


def add_general_agents(ts: "Triplestore"):
    """Add general agents to the triplestore `ts`.

    General agents include currently people, projects, organisations
    and equipment.

    """
    context = get_context(
        str(tablesdir / "context.json"),
        theme="ddoc:datadoc",
    )
    names = "people", "equipments", "projects", "organisations"

    tables = [
        TableDoc.parse_csv(
            csvfile=tablesdir / f"{name}.csv",
            context=context,
        ) for name in names
    ]
    dicts = []
    for table in tables:
        dicts.extend(table.asdicts())

    store(ts, dicts, context=context)


if __name__ == "__main__":
    ts = Triplestore("rdflib")
    add_general_agents(ts)
    ts.serialize(outdir / "general.ttl")
