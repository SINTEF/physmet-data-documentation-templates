import csv
import urllib
from pathlib import Path
from secrets import token_urlsafe

from tripper import Triplestore, CHAMEO, EMMO

from path2dict import find_datadocs


rootdir = Path(__file__).resolve().parent.parent
datadir = rootdir / "tests" / "data"
outdir = rootdir / "tests" / "output"

# TODO
# - to extend keys to the actual datasets
# - sample should refer to
# - instrument should refer to an instrument individual in the equipment table
#keys = "/sample/instrument/method/experiment/datasets".split("/")
keys = "/sample/instrument/method/experiment".split("/")


base_url = "https://studntnu.sharepoint.com/:i:/r/sites/o365_SFIPhysMet/Shared%20Documents/Reseach%20Areas,%20RA%20(Open%20channel)/RA%203%20Sustainable%20and%20high-performance%20material%20development/Andreas%20Voll%20Bugten%20data/"
user_prefix = "avb"
rightsHolder = "org:NTNU"
license = "TBD"  # XXX - define a license
creator = "pers:AnderasVollBugten"
operator = creator
contactPerson = "pers:MarisaDiSabatino"
material = ""  # the material that the base samples are taken from


def newid(prefix, nbytes=8):
    """Return a new random URL-safe ID with given prefix."""
    return f"{prefix}:{token_urlsafe(nbytes)}"


def dict2row(header, d):
    """Return a list with the data items in `d` ordered according to `header`."""
    return [d.get(h, "") for h in header]


def write_csv(filename, headers, data):
    with open(filename, "wt", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(headers))
        writer.writeheader()
        writer.writerows(data)


def document(pathdicts):
    """
    """
    samples = []
    datasets = []
    processes = []
    basesample_iris = set()

    for pd in pathdicts:
        path = "/".join(pd.values())  # restore the path
        basesample_iri = f"{user_prefix}:{pd['sample']}"
        process_iri = f"{basesample_iri}/{pd['method']}"
        dataset_iri = f"{process_iri}/{pd['experiment']}"
        sample_iri = f"{dataset_iri}-sample"
        instrument_iri = None  # infer from table of pre-defined equipment

        if basesample_iri not in basesample_iris:
            basesample_iris.add(basesample_iri)
            basesample = {
                "@id": basesample_iri,
                "@type": CHAMEO.Sample,  # should ideally be more specific
                "title": pd["sample"],
                "description": None,  # add more info...
                "note": None,
                "hasComposition": None,  # XXX TODO
                "creator": creator,
                "creationDate": None,  # not sure how this can be inferred
                "location": None,  # XXX - sample storage location
                "isTemporalPartOf": material,
                "isSpatioTemporalPartOf": None,
            }
            samples.append(basesample)

        sample = {
            "@id": sample_iri,
            "@type": CHAMEO.Sample,  # should ideally be more specific
            "title": sample_iri.split(":", 1)[1],
            "description": None,  # add more info...
            "note": None,
            "hasComposition": None,  # XXX TODO
            "creator": creator,
            "creationDate": None,  # not sure how this can be inferred
            "location": None,  # XXX - sample storage location
            "isTemporalPartOf": None,
            "isSpatioTemporalPartOf": basesample_iri,
        }
        samples.append(sample)

        dataset = {
            "@id": dataset_iri,
            "@type": EMMO.Dataset,  # XXX - should be more specific
            "distribution.accessURL": base_url + urllib.parse.quote(path),
            #"distribution.downloadURL":  # XXX - we path to actual datasets
            "title": pd["experiment"],
            "description": (
                f"{pd['method']} investigation of sample {pd['sample'] } "
                f"using {pd['instrument']}"
            ),
            "processedFrom": sample_iri,
            "rightsHolder": rightsHolder,
            "license": license,
            "creator": creator,
            "contactPerson": contactPerson,
            "releaseDate": None,  # XXX get creation data from file system
        }
        datasets.append(dataset)

        process = {
            "@id": process_iri,
            "@type": EMMO.Measurement,
            "note": None,
            "hasInput": sample_iri,
            "hasOutput": dataset_iri,
            "hasOperator": operator,
            "performedWith": instrument_iri,
        }
        processes.append(process)


    write_csv(outdir / "samples.csv", sample.keys(), samples)
    write_csv(outdir / "datasets.csv", dataset.keys(), datasets)
    write_csv(outdir / "processes.csv", process.keys(), processes)


if __name__ == "__main__":
    pathdicts = find_datadocs("tests/data", keys)
    document(pathdicts)
