# PhysMet Data Documentation Templates

## Description

The objective of this repository is to share templates and recommended folder structures to
store data in the frame of the SFI PhysMet.

Each type of measurement or simulation has its own folder providing the templates.
The template folder also includes examples of files to be filled as well as reference files to
be copied as-is (for example, a list of available equipment).

## Installation and Use

Clone the repository:

```bash
git clone https://github.com/your-org/physmet-data-documentation-templates.git
```

Then go to your local (or synchronized SharePoint folder and follow the procedure).

## treeweaver.py

A small CLI tool to extract structured metadata from directory paths or
directory trees.

* Parse paths to values
* Configure for your path structure with `--config`
* Optionally rewrite or derive fields with repeated `--template`
* Outputs as json or CSV to stdout

### Requirements

Python 3.12 and pyyaml. Can most easily be setup with `uv`,
e.g. `uv run scripts/treeweaver.py --help`

### Usage

`treeweaver.py` maps filesystem structure into fields defined by a configurable
schema, e.g.:
```
user/sample/instrument/method/experiment
```

To use it, try this script from repo's root directory.
```bash
uv run scripts/treeweaver.py tests/data --config "/sample/instrument/method/experiment"
```

For CSV output, add `--csv` and direct stdout to a file, `> out.csv`,
```bash
uv run scripts/treeweaver.py tests/data --config "/sample/instrument/method/experiment" --csv > out.csv
```
with this output,
```csv
,sample,instrument,method,experiment
,JM12,SEM,EDS,220304f
,JM12,SEM,EDS,220303h
,JM12,SEM,Imaging,Areas analyzed with SIMS
...
```

#### Templating 

To rewrite or derive fields, repeat `--template` with `FIELD=TEMPLATE`
entries:

```bash
uv run scripts/treeweaver.py tests/data \
  --config "/processedFrom/isOutputOf/@id" \
  --template "processedFrom=physmet:sample/{processedFrom}" \
  --template "isOutputOf=physmet:instrument/{isOutputOf}" \
  --json
```

Templates can reference any extracted field by name, including `@id`. The
template target may be an existing field or a new derived field. Templates may
also be constant strings:

```bash
uv run scripts/treeweaver.py tests/data \
  --config "/processedFrom/test/@id" \
  --template "newProp={processedFrom}_{@id}"
```

```bash
uv run scripts/treeweaver.py tests/data \
  --config "/processedFrom/test/@id" \
  --template "kind=dataset"
```

Fields without a matching `--template` keep the existing raw behavior.

#### Ontologies

To combine with ontologies, the variables can be named from the corresponding
ontology, then later parsed with e.g. `tripper.datadoc`.
```bash
uv run scripts/treeweaver.py tests/data --config "/emmo:processedFrom/emmo:isOutputOf/@type/dcterms:title"
```
has output
```
emmo:processedFrom="JM12" / emmo:isOutputOf="SEM" / @type="EDS" / dcterms:title="220304f" /
emmo:processedFrom="JM12" / emmo:isOutputOf="SEM" / @type="EDS" / dcterms:title="220303h" /
emmo:processedFrom="JM12" / emmo:isOutputOf="SEM" / @type="Imaging" / dcterms:title="Areas analyzed with SIMS" /
...
```
If combined with `tripper.datadoc`, the output should be in a `--csv` instead.

#### treeweaver.yaml
Instead of passing all of the configuration and temlates to the CLI script, you can 
make a file `treeweaver.yaml` which defines all the templates. One example can be like
in the `tests/data/treeweaver.yaml`.
```yaml
# Treeweaver configuration file
root: true # Is this config file at root of filetree?
version: 1 # version
prune:     # Patterns/directories to ignore
  patterns:
    - "JO11"
intents:   # Here 3 intents are defined (run script 3 times with different outputs)
  sample:
    config: "/@id" # same as --config
    template:      # same as --template
      "@id": "physmet:sample/{@id}"
      "@type": "chameo:Sample"
  dataset:
    config: "/sampleId///@id"
    template:
      "@id": "physmet:dataset/{@id}"
      "@type": "ddoc:Dataset"
      processedFrom: "physmet:sample/{sampleId}"
      "distribution.accessUrl": "https://studntnu.sharepoint.com/:i:/r/sites/o365_SFIPhysMet/Shared%20Documents/Reseach%20Areas,%20RA%20(Open%20channel)/RA%203%20Sustainable%20and%20high-performance%20material%20development/Andreas%20Voll%20Bugten%20data/{localPath}"
  procedure:
    config: "/sampleId/instrument/label/expId"
    template:
      "@id": "physmet:procedure/{localPath}"
      "@type": "ddoc:Procedure"
      hasInput: "physmet:sample/{sampleId}"
      hasOutput: "physmet:dataset/{expId}"
```

Then, the config is automatically read and
used to write the corresponding documentation files. For instance in
`scripts/datadoc_intent.sh`,
```bash
uv run scripts/treeweaver.py tests/data --intent "sample" --csv > output/samples.csv
uv run scripts/treeweaver.py tests/data --intent "dataset" --csv > output/datasets.csv
uv run scripts/treeweaver.py tests/data --intent "procedure" --csv > output/procedures.csv
```
Each intent here is created to make different type of data documentation 
on the same filetree. These configuation files are recursively read,
meaning that if a `treeweaver.yaml` is found inside a folder, it will override
the configuration for that folder and all sub-folders.

If `root: False`, then the script will search parent directories until it
finds a `treeweaver.yaml` with `root: True` to find the full configuration.
See `/tests/data/JM11/SEM/Imaging/treeweaver.yaml` for an example.


## Templates Available (in alphabetical order)

### Microscopy

**Description:** Templates and scripts for managing SEM microscopy data documentation.

**Content:**
- Project initialization scripts
- Sample tracking templates (CSV)
- Processing routes catalog
- SEM characterization session templates
- Automated readme generation

**Recommended use:** See [microscopy/docs/procedure.md](microscopy/docs/procedure.md) for detailed instructions.


## Support

Contact the developer.


## Authors and Acknowledgment

Contributors to this project.


## License

To be determined.
