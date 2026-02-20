# PhysMet Data Documentation Procedure

This document describes the step-by-step procedure for creating and managing projects with SEM microscopy data using the `physmet-folders.py` tool.

## Prerequisites

- Python 3.x installed
- Access to the `physmet-folders.py` script

**Important Note on Command Execution:**

All commands in this document should be executed from your **working directory** where you want to create or access your projects (not from the script's location). You need to specify the **explicit path** to `physmet-folders.py` in your commands.

**Examples:**

```bash
# If the script is in C:\path\to\physmet-data-documentation-templates\microscopy\scripts\
python C:\path\to\physmet-data-documentation-templates\microscopy\scripts\physmet-folders.py init

# Or use relative paths from your working directory
python ..\..\microscopy\scripts\physmet-folders.py init

# On Linux/Mac
python /path/to/physmet-data-documentation-templates/microscopy/scripts/physmet-folders.py init
```

For convenience, you may want to:
- Add the script directory to your PATH
- Create an alias or shortcut

Throughout this document, commands are shown as `python physmet-folders.py` for readability, but remember to use the full path to the script.

## Workflow Overview

1. Create a new project
2. Define processing routes
3. Register samples with their processing history
4. Add SEM characterization sessions
5. Document SEM characterization

---

## Step 1: Create a New Project

Create a new project folder structure with all necessary documentation files.

**Command:**
```bash
python physmet-folders.py init
```

**Interactive prompts:**
- Project/Folder name: Enter your project name (e.g., `MyProject`)
- Author name: Press Enter to accept default (your username) or type a name
- Destination directory: Press Enter to use current directory or specify a path

**Alternative (non-interactive):**
```bash
python physmet-folders.py init -p MyProject
```
Then press Enter twice to accept defaults for author and destination.

**What gets created:**
```
MyProject/
├── readme.txt           # Project documentation template
├── info.txt             # Basic project metadata
├── samples.csv          # Sample tracking list
├── instruments.csv      # Available instruments
├── processing.csv       # Processing routes catalog
└── SEM/                 # SEM microscopy data folder
```

---

## Step 2: Define Processing Routes

Edit the `processing.csv` file to define the processing routes that will be applied to your samples.

**Location:** `MyProject/processing.csv`

**Format:**
```csv
ProcessID,ProcessingRoute,Notes
P001,"Heat treatment: 500C for 2h, Air cooling","Optional: add any relevant details about this process"
P002,"As-received, No processing","Baseline/control samples"
P003,"Cold rolling: 50% reduction","Mechanical deformation"
```

**Instructions:**
1. Open `processing.csv` in a text editor or Excel
2. Each row defines one processing route
3. **ProcessID**: Unique identifier (e.g., P001, P002, P003)
4. **ProcessingRoute**: Short description of the process
5. **Notes**: Optional details about the process definition
6. Save the file

**Example processing routes:**
- Heat treatments (temperature, duration, cooling rate)
- Mechanical processing (rolling, forging, extrusion)
- As-received state (baseline/control)

---

## Step 3: Register Samples

Manually register your samples in the `samples.csv` file with their processing history.

**Location:** `MyProject/samples.csv`

**Format:**
```csv
SampleId, Date(YYYY-MM-DD), ProcessIDs
SAMPLE001, 2026-02-20, [P001]
SAMPLE002, 2026-02-21, [P002]
SAMPLE003, 2026-02-22, [P001,P003]
```

**Instructions:**
1. Open `samples.csv` in a text editor or Excel
2. Add a new row for each sample
3. **SampleId**: Unique identifier for the sample (e.g., SAMPLE001, SAMPLE002)
4. **Date**: Date the sample was created/received (format YYYY-MM-DD)
5. **ProcessIDs**: Reference to processing route(s) from `processing.csv` as a Python list
   - Single process: `[P001]` (sample underwent only heat treatment)
   - Sequential processes: `[P001,P003]` (sample was heat treated, then cold rolled)
   - As-received: `[P002]` (no processing applied)
6. Save the file

**Example entries:**
```csv
SampleId, Date(YYYY-MM-DD), ProcessIDs
AL001, 2026-02-15, [P001]
AL002, 2026-02-15, [P002]
AL003, 2026-02-16, [P001,P003]
CU001, 2026-02-18, [P002]
```

**Note:** This step is done manually because sample creation is typically tracked separately from characterization. You register all your samples with their processing history before performing characterization.

---

## Step 4: Add SEM Characterization Session

When you're ready to perform SEM imaging on a sample, create a characterization session folder.

**Command:**
```bash
python physmet-folders.py add -s SAMPLE_ID -d YYYY-MM-DD -p MyProject
```

**Parameters:**
- `-s SAMPLE_ID`: Sample identifier that exists in `samples.csv` (e.g., SAMPLE001)
- `-d YYYY-MM-DD`: Date of the SEM session (e.g., 2026-02-20)
- `-p MyProject`: Project name (optional if default project is set)

**Example:**
```bash
python physmet-folders.py add -s SAMPLE001 -d 2026-02-20 -p MyProject
```

**What happens:**
- Verifies that SAMPLE001 exists in `samples.csv`
- Creates a folder: `SEM/SEM_SAMPLE001_2026-02-20/`
- Files created in the SEM folder:
  - `info.txt` - Basic session metadata
  - `readme.txt` - SEM session documentation template (pre-filled with sample ID, date, project, operator)

**Important:** The sample must already exist in `samples.csv` before you can add a characterization session. If the sample is not found, you'll get an error message.

**Multiple characterization sessions:** You can add multiple SEM sessions for the same sample on different dates. Each will create its own folder (e.g., `SEM_SAMPLE001_2026-02-20`, `SEM_SAMPLE001_2026-03-15`).

---

## Step 5: Document SEM Characterization

After performing SEM imaging, document the characterization session in the sample's folder.

**Location:** `MyProject/SEM/SEM_SAMPLEID_DATE/readme.txt`

**What to document:**

### Before/During imaging:
Fill in the template sections in `readme.txt`:

1. **IMAGING PURPOSE**
   - What features are you documenting?
   - Example: Surface morphology, grain structure, fracture analysis

2. **AREAS OF INTEREST**
   - Which regions did you image and why?
   - Example: Center of sample, edge regions, specific defects

3. **FILE ORGANIZATION**
   - Explain your file naming convention
   - Example: Images numbered sequentially, grouped by magnification

### During/After imaging:
Continue filling in:

4. **OBSERVATIONS**
   - Notable features, anomalies, or findings
   - Unexpected observations

5. **POST-PROCESSING** (if applicable)
   - Image enhancements applied
   - Example: Contrast adjustment, noise reduction

6. **OBSERVER NOTES**
   - Additional context about the session
   - Equipment performance, recommendations

7. **SCALE/MAGNIFICATION SUMMARY**
   - Overview of scales used
   - Example: Low mag (100×), detail (1,000×), high res (10,000×)

**Store SEM images** in the same folder: `MyProject/SEM/SEM_SAMPLEID_DATE/`

---

## Additional Commands

### List all projects
```bash
python physmet-folders.py list
```

### Set default project
```bash
python physmet-folders.py set-default -p MyProject
```
After setting a default, you can omit the `-p` parameter in add commands.

### Display help
```bash
python physmet-folders.py --help
```

### Display version
```bash
python physmet-folders.py --version
```

---

## Best Practices

1. **Consistent Naming**
   - Use clear, systematic sample IDs
   - Example: `PROJ_001`, `PROJ_002` or `AA_001`, `BB_001`

2. **Processing Routes**
   - Define all process routes before adding samples
   - Use descriptive ProcessIDs (P001, P002) and clear descriptions
   - Document process parameters fully

3. **Documentation**
   - Fill in the readme.txt templates completely
   - Update immediately after characterization while fresh in memory
   - Include scale bars or magnification info

4. **File Organization**
   - Keep all SEM images in their respective folders
   - Use consistent file naming within each characterization session
   - Include metadata files from the SEM instrument

5. **Version Control**
   - Keep project files under version control (git)
   - Commit changes to CSV files when samples or processes are added
   - Don't track large image files directly (consider git-lfs)

---

## Example Workflow

Complete example from start to finish:

```bash
# 1. Create project
python physmet-folders.py init -p AluminumStudy
# Press Enter twice to accept defaults

# 2. Edit processing.csv (manual step)
# Add: P001,"Annealing: 400C for 4h, Furnace cooling","Stress relief"
# Add: P002,"As-received","Control samples"

# 3. Register samples in samples.csv (manual step)
# Open AluminumStudy/samples.csv and add:
# AL001, 2026-02-15, [P001]
# AL002, 2026-02-15, [P002]
# AL003, 2026-02-16, [P001,P003]

# 4. Add SEM characterization session for first sample
python physmet-folders.py add -s AL001 -d 2026-02-20 -p AluminumStudy
# This creates: AluminumStudy/SEM/SEM_AL001_2026-02-20/

# 5. Perform SEM imaging (external step)
# Save images to: AluminumStudy/SEM/SEM_AL001_2026-02-20/

# 6. Document the characterization (manual step)
# Edit: AluminumStudy/SEM/SEM_AL001_2026-02-20/readme.txt
# Fill in all sections with session details

# 7. Add characterization for second sample
python physmet-folders.py add -s AL002 -d 2026-02-21 -p AluminumStudy

# 8. Later, add another characterization session for the first sample
python physmet-folders.py add -s AL001 -d 2026-03-15 -p AluminumStudy
# This creates: AluminumStudy/SEM/SEM_AL001_2026-03-15/
```

---

## Troubleshooting

**"Sample not found in samples.csv" error:**
- Check that the sample is registered in `samples.csv`
- Verify the sample ID spelling matches exactly
- Add the sample to `samples.csv` if it doesn't exist

**"Project not found" error:**
- Check project name spelling
- Use `python physmet-folders.py list` to see available projects
- Set default project if working with one project repeatedly

**"SEM directory not found":**
- Verify project structure is intact
- Re-create project if necessary

**Timeout when running commands:**
- If `init` or `add` commands hang, they may be waiting for input
- Provide all required parameters: `-p` for project, `-s` for sample, `-d` for date

---

## File Formats

### samples.csv
```csv
SampleId, Date(YYYY-MM-DD), ProcessIDs
SAMPLE001, 2026-02-20, [P001]
SAMPLE002, 2026-02-21, [P001,P003]
```

### processing.csv
```csv
ProcessID,ProcessingRoute,Notes
P001,"Heat treatment: 500C/2h","Annealing cycle"
P002,"As-received",""
```

### instruments.csv
```csv
Instrument,Type,Location,Contact,Notes
SEM_1,Scanning Electron Microscope,Lab A,Dr. Smith,"JEOL JSM-7000F"
```

---

## Contact & Support

For issues or questions about this procedure, contact the project administrator or refer to the project documentation.
