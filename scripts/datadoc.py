import csv
import fnmatch
import urllib
from datetime import datetime
from pathlib import Path

import yaml

from tripper import Triplestore, CHAMEO, EMMO

#from path2dict import find_datadocs


rootdir = Path(__file__).resolve().parent.parent
datadir = rootdir / "tests" / "data"
outdir = rootdir / "tests" / "output"
tablesdir = rootdir / "tables"


def find_datadocs(root, keys=None):
    """
    """
    root = Path(root).resolve()

    # sanity check
    if not root.is_dir():
        raise ValueError(f"{root} is not a directory")

    results = []
    default_info = {}

    def walk(current_path, depth, parts, keys, info):
        if (current_path / ".ddocignore").exists():
            return

        infofile = current_path / "info.yaml"
        if infofile.exists():
            with open(infofile, "rt") as f:
                conf = yaml.safe_load(f)
            if "dir_structure" in conf:
                depth = 1
                keys = conf["dir_structure"].split("/")
            info.update(conf)

        if depth >= len(keys):
            info["path"] = "/".join(parts)
            results.append(info.copy())
            for child in current_path.iterdir():
                if child.is_file():
                    for pattern in info.get("data_files", []):
                        if fnmatch.fnmatch(child.name, pattern):
                            info["path"] = str(child)
                            info["filename"] = child.name
                            results.append(info.copy())
            return

        key = keys[depth].strip()
        for child in current_path.iterdir():
            if child.is_dir():
                if key:
                    info[key] = child.name
                walk(child, depth + 1, parts + [child.name], keys, info.copy())

    # root corresponds to first key
    walk(root, 1, [root.name], keys, default_info)

    return results


def write_csv(filename, headers, data):
    with open(filename, "wt", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(headers))
        writer.writeheader()
        writer.writerows(data)


_instrument_iris = {}  # cache

def get_instrument_iri(identifier):
    """Return the instrument IRI for `identifier`."""
    if not _instrument_iris:
        with open(tablesdir / "equipments.csv", "rt") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "identifier" in row:
                    _instrument_iris[row["identifier"]] = row["@id"]
    return _instrument_iris.get(identifier)


def document(pathdicts):
    """
    """
    samples = []
    datasets = []
    processes = []
    basesample_iris = set()

    for info in infodicts:
        path = info["path"]
        fullpath = (datadir.parent / path).resolve()
        prefix = info.get("user_prefix", "physmet")
        basesample_iri = f"{prefix}:{info['sample']}"
        process_iri = f"{basesample_iri}/{info['process']}"
        dataset_iri = f"{process_iri}/{info['dataset']}"
        sample_iri = f"{dataset_iri}-sample"

        if "base_url" in info:
            url = info["base_url"] + urllib.parse.quote(path)
        else:
            url = None

        releaseDate = info.get("releaseDate")
        if not releaseDate:
            mtime = Path(fullpath).stat().st_mtime
            releaseDate = datetime.fromtimestamp(mtime).isoformat()

        instrument = info.get("instrument")

        if "filename" in info:
            dataset = {
                "@id": f"{dataset_iri}/{info['filename']}",
                "@type": EMMO.Dataset,  # XXX - should be more specific
                "distribution.downloadURL": url,
                "isDatumOf": dataset_iri,
                "releaseDate": releaseDate,
            }
            datasets.append(dataset)

        else:

            if basesample_iri not in basesample_iris:
                basesample_iris.add(basesample_iri)
                basesample = {
                    "@id": basesample_iri,
                    "@type": CHAMEO.Sample,  # should be more specific
                    "title": info["sample"],
                    "description": None,  # add more info...
                    "note": None,
                    "hasComposition": None,  # XXX TODO
                    "creator": info.get("creator"),
                    "creationDate": None,  # from info
                    "location": None,  # XXX - sample storage location
                    "isTemporalPartOf": info.get("material"),
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
                "creator": info.get("creator"),
                "creationDate": None,  # not sure how this can be inferred
                "location": None,  # XXX - sample storage location
                "isTemporalPartOf": None,
                "isSpatioTemporalPartOf": basesample_iri,
            }
            samples.append(sample)

            dataset = {
                "@id": dataset_iri,
                "@type": EMMO.Dataset,  # XXX - should be more specific
                "distribution.accessURL": url,
                "distribution.downloadURL": None,
                "title": info["dataset"],
                "description": (
                    f"{info['process']} investigation of sample "
                    f"{info['sample'] } using {instrument}"
                ),
                "processedFrom": sample_iri,
                "isDatumOf": None,
                "rightsHolder": info.get("rightsHolder"),
                "license": license,
                "creator": info.get("creator"),
                "contactPerson": info.get("contactPerson"),
                "releaseDate": None,
            }
            datasets.append(dataset)

            process = {
                "@id": process_iri,
                "@type": EMMO.Measurement,
                "note": None,
                "hasInput": sample_iri,
                "hasOutput": dataset_iri,
                "hasOperator": info.get("operator"),
                "performedWith": get_instrument_iri(instrument),
            }
            processes.append(process)


    write_csv(outdir / "samples.csv", sample.keys(), samples)
    write_csv(outdir / "datasets.csv", dataset.keys(), datasets)
    write_csv(outdir / "processes.csv", process.keys(), processes)


if __name__ == "__main__":
    infodicts = find_datadocs("tests/data")
    document(infodicts)

    import json
    #print(json.dumps(infodicts, indent=4))
