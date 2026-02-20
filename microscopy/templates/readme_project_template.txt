PROJECT DOCUMENTATION
=====================

Project Name: {project_name}
Created By: {author}
Date Created: {date}


PROJECT DESCRIPTION
-------------------
[ Describe the overall purpose and scope of this project ]
[ Example: Materials characterization study, failure analysis, development project, etc. ]


OBJECTIVES
----------
[ List the main objectives of this project ]
[ What questions are you trying to answer? What properties are being investigated? ]


SAMPLE OVERVIEW
---------------
[ General information about the samples in this project ]
[ Material types, source, processing history, common characteristics, etc. ]
[ Detailed sample information is tracked in samples.csv ]


FOLDER STRUCTURE
----------------
{project_name}/
├── readme.txt           # This file - project documentation
├── info.txt             # Basic project metadata
├── samples.csv          # Sample tracking list
├── instruments.csv          # Instruments list
├── processing.csv          # Sample processing list
└── SEM/                 # SEM microscopy data
    └── SEM_SAMPLE_DATE/ # Individual sample folders


DATA ORGANIZATION
-----------------
- Each sample is registered in samples.csv with Sample ID and date
- SEM imaging data is stored in SEM/SEM_SAMPLEID_DATE/ folders
- Each characterization folder contains its own readme.txt with session details


SAMPLE NAMING CONVENTION
-------------------------
[ Describe your sample ID naming scheme ]
[ Example: Material code + sequence number, date-based codes, etc. ]
[ Current suggestion for PhysMet: AuthorID+number]


PROCESSING CONDITIONS
---------------------
[ Document common experimental parameters or processing conditions of the samples ]
[ Temperature history, deformation, sample preparation protocols, etc. ]
[ Detailed processing information is tracked in processing.csv ]


CHARACTERIZATION INSTRUMENTS
----------------------------
[ Document the instruments used during the characterization ]
[ Detailed instruments information is provided in instruments.csv ]


NOTES
-----
[ Any additional project-specific information ]
[ Collaborators, funding sources, special requirements, safety considerations, etc. ]


CONTACT INFORMATION
-------------------
Primary Investigator: {author}
Institution: [ Add institution name ]
Email: [ Add contact email ]


REFERENCES
----------
[ Link to related projects, publications, or documentation ]
[ Standard operating procedures, method references, etc. ]
