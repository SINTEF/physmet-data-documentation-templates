import urllib
from pathlib import Path
from secrets import token_urlsafe

from tripper import Triplestore, EMMO

from path2dict import find_datadocs


rootdir = Path(__file__).resolve().parent.parent
datadir = rootdir / "tests" / "data"

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
contactPerson = "pers:MarisaDiSabatino"



def newid(prefix, nbytes=8):
    """Return a new random URL-safe ID with given prefix."""
    return f"{prefix}:{token_urlsafe(nbytes)}"


def dict2row(header, d):
    """Return a list with the data items in `d` ordered according to `header`."""
    return [d.get(h, "") for h in header]


def document(pathdicts):
    sample_header = [
        "@id",
        "@type",
        "title",
        "description",
        "note",
        #"hasComposition",
        "creator",
        "creationDate",
        "location",
        "isTemporalPartOf",
        "isSpatioTemporalPartOf",
    ]
    dataset_header = [
        "@id",
        "@type",
        "distribution.accessURL",
        #"distribution.downloadURL",
        "title",
        "description",
        "processedFrom",
        "rightsHolder",
        "license",
        "creator",
        "contactPerson",
        "releaseDate",
    ]
    process_header = [
        "@id",
        "@type",
        "note",
        "hasInput",
        "hasOutput",
        "hasOperator",
        "performedWith",
    ]


    samples = []
    datasets = []
    processes = []

    for pd in pathdicts:
        path = "/".join(d.values())  # restore the path
        sample_iri = f"{user_prefix}:{pd['sample']}"
        process_iri = f"{sample_iri}-{pd['method']}"
        dataset_iri = f"{process_iri}-{pd['experiment']}"

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
            "releaseDate": "",  # XXX get creation data from file system
        }





dicts = find_datadocs("tests/data", keys)

for d in dicts:
    path = "/".join(d.values())
    print(path)
