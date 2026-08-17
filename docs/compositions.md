# Compositions
A simplified user-friendly table format is provided for specifying alloy compositions.
An example table may look like this:

| @id        | Fe[wt%] | Mn[wt%] | C[wt%] | B[wt%] | Si[wt%] | Al[wt%] | Ti[wt%] | Ca[wt%] |
|------------|---------|---------|--------|--------|---------|---------|---------|---------|
| avb:JM     | 57      | 13      | 24     | 6      |         |         |         |         |
| elkem:FeSi | 25.06   | 0.13    |        |        | bal     | 0.81    | 0.12    | 0.12    |

**Notes**:
* @id is (as usual) a unique id for a given composition.
* @type is implicitly assumed to be emmo:ChemicalComposition.
* The header of columns specifying chemical composition should start with a chemical symbol optionally followed by a square bracket with the unit. Default unit is "wt%".
* Supported units include:
  - weight percent: wt%, wt-percent, weight-percent, mass% (default)
  - atom percent: at%, at-percent
  - weight fraction: wtfrac, wt-fraction, weight-fraction
  - atom fraction: atfrac, at-fraction, atom-fraction
* A composition value starting with "bal" means that the value in this cell is adjusted such that the total composition is 100%.
