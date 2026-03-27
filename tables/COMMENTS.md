COMMENTS
========

General
-------
Documentation should be easy accessible and not require login to read.
Remember, NTNU students are external with short-lived sessions before
they have to login again.

If you want to keep this repo private, at least put all the
documentation on a public GitLab Pages.


Keyword names
-------------
Keywords in YAML-sections in README-files and table headers should be:
- case sensitive (JSON-LD mappings are case sensitive)
- reuse names of terms in standard vocabularies (unless there are good reasons to do otherwise)
- be a single word without special characters
- be written with lowerCamelCase (unless there are good reasons to do otherwise)

We should publish lists of available keywords and their meaning.
The Tripper documentation already contain such a [list](https://emmc-asbl.github.io/tripper/latest/datadoc/keywords/), but that should be improved.



Identifiers
-----------
Everything in the knowledge base should have a globally unique and persistent identifier.
In the context of the knowledge base we call these IDs for *International Resource Identifiers* (IRIs).
We use namespaces to ensure globally uniqueness.

For example, a SEM dataset by Andreas Voll Bugten may be identified by the IRI
https://orcid.org/0000-0003-0311-8584/JP16/SEM/220406aa/nitride5.tif
where https://orcid.org/0000-0003-0311-8584/ is a unique prefix for all data and other resources related to Andreas.

This namespace can be abbreviated with a prefix.
Each person, project and organisation has a prefix assigned to them, which is unique within the scope of our knowledge base.

For example, we have assigned the prefix "avb" to Andreas Voll Bugten.
When documenting the above dataset, we will refer to it with the following IRI:
`abd:JP16/SEM/220406aa/nitride5.tif`.

Samples coming from Elkem, should use the Elkem prefix, and so forth.

> [!NOTE]
> An IRI written with a prefix is called a [CURIE] (compact URI).
> A CURIE differ from a [QName] in that the part following the colon may contain embedded slashes.

The prefixes are maintained in the three global tables:
- people.csv
- projects.csv
- organisations.csv



[CURIE]: https://www.w3.org/2001/sw/BestPractices/HTML/2005-10-27-CURIE
[Qname]: https://en.wikipedia.org/wiki/QName
