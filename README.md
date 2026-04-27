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

## path2dict.py

A small CLI tool to extract structured metadata from directory paths or
directory trees.

* Parse paths to values
* Configure for your path structure with `--config`
* Outputs as json or CSV to stdout

### Usage

`path2dict.py` maps filesystem structure into fields defined by a configurable
schema, e.g.:
```
user/sample/instrument/method/experiment
```

To use it, try this script from repo's root directory.
```bash
python scripts/path2dict.py tests/data --config "/sample/instrument/method/experiment"
```

For CSV output, add `--csv` and direct stdout to a file, `> out.csv`,
```bash
python scripts/path2dict.py tests/data --config "/sample/instrument/method/experiment" --csv > out.csv
```
with this output,
```csv
,sample,instrument,method,experiment
,JM12,SEM,EDS,220304f
,JM12,SEM,EDS,220303h
,JM12,SEM,Imaging,Areas analyzed with SIMS
...
```

### Ontologies

To combine with ontologies, the variables can be named from the corresponding
ontology, then later parsed with e.g. `tripper.datadoc`.
```bash
python scripts/path2dict.py tests/data --config "/prov:wasDerivedFrom/emmo:isOutputOf/@type/dcterms:title"
```
has output 
```
prov:wasDerivedFrom="JM12" / emmo:isOutputOf="SEM" / @type="EDS" / dcterms:title="220304f" / 
prov:wasDerivedFrom="JM12" / emmo:isOutputOf="SEM" / @type="EDS" / dcterms:title="220303h" / 
prov:wasDerivedFrom="JM12" / emmo:isOutputOf="SEM" / @type="Imaging" / dcterms:title="Areas analyzed with SIMS" / 
...
```


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
