
# SEM/TEM Microscopy Data Structure & Naming Conventions

This document defines the file structure, naming conventions, and metadata
requirements for SEM (Scanning Electron Microscopy) and TEM (Transmission
Electron Microscopy) projects.

By following consistent conventions ensures:

- Easy identification of image content without opening files
- Chronological and version‑controlled organization of datasets
- Efficient collaboration and long‑term data usability

## A recommended folder hierarchy

```plaintext
Project_Name/
│
├── 01_Samples/
│   ├── Sample_A/
│   │   ├── Preparation/
│   │   └── Metadata/
│   └── Sample_B/
│
├── 02_SEM/
│   ├── Raw/
│   │   ├── YYYYMMDD_Instrument_Run/
│   │   └── ...
│   ├── Processed/
│   └── Analysis/
│
├── 03_TEM/
│   ├── Raw/
│   ├── Processed/
│   └── Analysis/
│
├── 04_Results/
│   ├── Figures/
│   ├── Plots/
│   └── Exports/
│
├── 05_Writing/
│   ├── Reports/
│   ├── Manuscripts/
│   └── Presentations/
│
└── README.md
```

## File Naming Conventions
Use the following general rules for clarity and sorting:

- Use ASCII only, no spaces, no special characters
- One dot only before file extension
- Max length ~30 characters
- Dates in YYYYMMDD
- Use leading zeros for numbering (e.g., 001)
- All names should be case‑independent

For examples:

SEM File Naming Schema
```plaintext
SEM Image
[Date]_[Instrument]_[Mag]_[Detector]_[SampleID]_[Seq].tiff
TEM Image
[Date][Instrument][KV][Mode][SampleID]_[Seq].tiff
```

- `Date`: YYYYMMDD  
- `Instrument`: SEM model name  
- `Mag`: Magnification, e.g., `005kX`  
- `Detector`: e.g., SE, BSE  
- `SampleID`: internal identifier  
- `Seq`: 001–999
- `KV`: accelerating voltage, e.g., `200kV`  
- `Mode`: BF, DF, HRTEM, SAED, STEM‑HAADF, etc.

## Metadata Requirements

Metadata is "data about data". It describes information such as who created
something, when it was created, what it contains, or how it should be used.
For example, the author and publication date of a document, or the date and
camera model stored inside a photograph’s EXIF data, are all metadata.

A simple way to think about it:
If data is a book, metadata is the title, author, keywords, and table of
contents. These do not contain the content, but they describe it so you can
understand it quickly.

Metadata matters because it:

1. Makes data easier to find Metadata allows information systems, search
   engines, and users to quickly locate relevant files, datasets, or records 
   without looking inside each one. It improves searchability and filtering.
2. Helps users understand the data: Metadata explains what a dataset 
   represents, how it was produced, and how it should be interpreted, even if 
   the user wasn't involved in its creation. This provides clarity and context.
3. Supports organization and management: Metadata is essential for sorting, 
   classifying, and structuring large collections of information, whether in 
   research, libraries, or digital repositories.
4. Improves data governance and quality: Metadata helps with tracking data 
   lineage, ensuring consistency, supporting regulatory compliance, and 
   keeping datasets trustworthy.
5. Enables interoperability and reuse: Standardized metadata allows 
   information to be shared across systems, supports long‑term preservation, 
   and makes datasets reusable by others (people or machines).

The 15 core elements for metadata are descirbed in [dcmi.md](./docs/dcmi.md).
And an example is geven below:

```plaintext
session_metadata.txt

Date:        2026-02-16
Operator:    Name Surname
Instrument:  SEM XL30
Sample:      SA12
Environment: Vacuum / Low-vac
Notes:       Tilted 30°, working distance 10 mm

sample_metadata.txt

SampleID:           SA12
Material:           Al-Mg alloy
Preparation:        Mechanical polish + ion milling
Coating:            Carbon coat 10 nm
Storage Location:   -80°C freezer, box B12
```

The metadata can be gather in on file (Excel or CSV), with the column as
metadata and the rows as the individuas like records, samples, etc.


| Sample ID  | Title | Material | Preparation | Source |
| --- | --- | --- | --- | --- |
| SA12       | SS    | Al-Mg    | polish      | B12    |
| ...        |       |          |             |        |
| ...        |       |          |             |        |

