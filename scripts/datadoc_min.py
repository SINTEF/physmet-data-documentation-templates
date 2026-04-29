#!/bin/env/python3
from pathlib import Path
from tripper import Session
from tripper.datadoc import TableDoc
from tripper import EMMO, CHAMEO, DCTERMS

root_dir = Path(__file__).parent.parent
output_dir = root_dir / "output"
output_dir.mkdir(exist_ok=True)

# Retrieve a triplestore as described by the local session.yaml file.
session = Session(root_dir / "conf" / "session.yaml")
ts = session.get_triplestore("MemDB")

# Add data documentation from csv to triplestore.
prefixes = {
    "physmet" : "https://www.ntnu.edu/physmet/",
    "temgo" : "https://www.ntnu.edu/temgemini/vocab/temgo#",
    "data" : "http://www.example.org/data/",
    "sample" : "http://www.example.org/sample/",
    "dom" : "http://www.example.org/tem/",
    "mat" : "https://www.ntnu.edu/temgemini/alloys#",
    "pr" : "http://www.example.org/process/",
    "ddoc" : "http://www.example.org/ddoc/",
}

context = {
    "hasInput" : {
        "@id": EMMO.hasInput,
        "@type": "@id",
    },
    "processedFrom" : {
        "@id": EMMO.processedFrom,
        "@type": "@id",
    },
    "hasOutput" : {
        "@id": EMMO.hasOutput,
        "@type": "@id",
    },
    "isOutputOf" : {
        "@id": EMMO.isOutputOf,
        "@type": "@id",
    },
    "isInputOf" : {
        "@id": EMMO.isInputOf,
        "@type": "@id",
    },
    "isAfter" : {
        "@id": EMMO.isAfter,
        "@type": "@id",
    },
    "isBefore" : {
        "@id": EMMO.isBefore,
        "@type": "@id",
    },
    "identifier" : {
        "@id": DCTERMS.identifier,
    },
    "isTemporalPartOf" : {
        #"@id" : EMMO.isTemporalPartOf,
        "@id" : "https://w3id.org/emmo#EMMO_f722a7a9_864d_4896_a331_f90141f90a0a",
        "@type" : "@id",
    },
}

datasets_path = output_dir / "datasets.csv"
datadoc = TableDoc.parse_csv(datasets_path, prefixes=prefixes, context=context)
datadoc.save(ts)

samples_path = output_dir / "samples.csv"
datadoc = TableDoc.parse_csv(samples_path, prefixes=prefixes, type=CHAMEO.Sample, context=context)
datadoc.context.add_context(context)
datadoc.save(ts)

processes_path = output_dir / "procedures.csv"
datadoc = TableDoc.parse_csv(processes_path, prefixes=prefixes, type=EMMO.Procedure, context=context)
datadoc.context.add_context(context)
datadoc.save(ts)

# Serialize to a file
ts.serialize(output_dir / "physmet_datadoc.ttl")
