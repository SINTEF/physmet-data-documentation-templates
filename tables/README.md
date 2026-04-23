Templates
=========
This folder contain a set of templates for data documentation.
The figure below shows an overview of the templates and how they relate to each other.

![Tables](figs/tables.svg)
> Figure 1. Overview of template tables and how they relate to each other.
>
> The colour coding is as follows; red: general tables reused between
> projects, blue: tables created by the individual data producer (not
> all tables are needed by everyone); violet: templates for new
> classes and properties.

Each row in the tables documents an individual, class or property that will be added to the knowledge base.
The templates can be grouped into three categories

Individuals documented by the user:
- **[datasets.csv](datasets.csv)**: Datasets.
- **[samples.csv](samples.csv)**: Physical samples (material objects) that are processed and characterised.
- **[processes.csv](processes.csv)**: Processes and procedures. Includes materials processing, characterisation and computations. Has samples/datasets as input and output.
- **[software.csv](software.csv)**: Software used for driving a process.
- **[composition.csv](composition.csv)**: Chemical composition of a sample.

Class-level documentation - generalised input provided by the user:
- **[datasetClasses.csv](datasetClasses.csv)**: Dataset classes, like the general concept of a TEM bright field image. An actual TEM bright field image would be an instance of this class.
- **[sampleClasses.csv](sampleClasses.csv)**: Sample classes, like TEM sample. An actual TEM sample would be an instance of this class.
- **[processClasses.csv](processClasses.csv)**: Process classes, like TEM bright field imaging. Has class-level samples/datasets as input and output.
- **[properties.csv](properties.csv)**: For user-defined annotations, data properties or object properties.

Agents maintained at Centre-level:
- **[projects.csv](projects.csv)**: Projects. May e.g. be referred to as the creator of a sample or dataset.
- **[organisations.csv](organisations.csv)**: Organisations. May e.g. be referred to as the owner of a dataset.
- **[people.csv](people.csv)**: People. May be a contact point for a sample, dataset or equipment or the operator of a process.
- **[equipment.csv](equipment.csv)**: Equipment for materials processing, characterisation instruments, etc.



Documenting workflows
---------------------
Workflows are documented as a set of processes with objects (samples/datasets) as input or output.

Workflows can both be documented at individual-level (for provenance) or at a class-level (to describe a reusable workflow that might or might not yet have been executed).

![General workflow](https://raw.githubusercontent.com/HEU-MatCHMaker/DataDocumentation/refs/heads/master/tutorial/figs/workflow.svg)
> Figure 2. General workflow.
