# Coordinate-Basis vs Readout-Basis Involution

Status: **canonical cross-repo pattern / mixed [M][E][T] / positive readout-basis run pending**.  
Claim ID: `COORD_READOUT_INVOLUTION_001`.  
Primary source record: `kb/sources/cipher-involution-experiment.yaml`.

## 0. Pattern name

`coordinate-basis-vs-readout-basis-involution`

## 1. Core claim

An involutive transform achieves selectivity only when applied in a basis aligned to the readout structure of interest.

Coordinate-basis involutions preserve reversibility but do not automatically align with a specific observable. A sign flip, cipher mask, or `Z/2` action can be perfectly reversible and still have poor selectivity for the direction that the system is trying to read.

The four required properties for reversible precision edits are:

```text
involution + selectivity + balance + composability
```

The order-four algebraic structure supporting all four is:

```text
V4 = Z/2 x Z/2
```

realized through mutually orthogonal Latin squares over `GF(4)`, not through the cyclic group `Z4`.

## 2. Mathematical dependency [M]

The load-bearing mathematical dependency is the finite-field construction:

```text
GF(4) = GF(2^2)
V4 = additive group of GF(4)
MOLS from the affine plane AG(2, GF(4))
```

A canonical affine construction is:

```text
L_m(x, y) = m x + y
```

for distinct slopes `m` in `GF(4)`. A pair such as `L_1` and `L_alpha` yields all sixteen ordered pairs as `(x, y)` ranges over `GF(4)^2`.

The cyclic group `Z4` is rejected. Its Cayley table is Latin, but it is not an all-involutive structure and does not supply the required orthogonal mate at even order. The failure is structural, not accidental.

## 3. Empirical source [E]

The Part B cipher experiment reported:

```text
coordinate-basis involution error: < 1e-16
coordinate-basis selectivity: approximately 0.015
```

across four cipher/sign-flip variants.

Interpretation: the tested transforms preserved involution but failed readout selectivity in the coordinate basis.

Pending prediction:

```text
centroid/readout-basis selectivity should increase by 5x to 50x
```

when the corrected run uses readout-aligned flips and proper `GF(4)`-based MOLS masks.

This positive readout-basis run is not yet attached to the repo. Until then, the empirical status is negative coordinate-basis result confirmed, positive readout-basis prediction pending.

## 4. Typological parallels [T]

These parallels are structural analogies, not formal reductions.

### Hodge

The Hodge star / Weil-operator structure supplies involution and balance. The Hodge conjecture is the selectivity question: which rational `(p,p)` classes align with algebraic cycle directions?

### BSD

The root number `epsilon` is a global sign/involution on the `L`-function side. It does not by itself align to the Selmer/Mordell-Weil direction that determines rank. Selmer alignment is the readout-basis problem.

### Con(PA) / diagonalization

Certificate axioms can behave like coordinate-basis involutions. Selectivity for the consistency boundary requires a diagonal or fixed-point construction; the diagonal lemma is the readout-basis mechanism.

### `mu_2` monodromy / np-program

The Catalan `mu_2` fixture detects a `Z/2` sign channel. It does not identify which `Z/2` factor in `V4` is active and does not supply the full `GF(4)` MOLS readout structure.

### Spectral / Heller-Winters

Eigenvalue sign symmetry, complex conjugation, and functional-equation symmetry are coordinate-basis involutions unless the eigenfunctions/operators are aligned to the declared arithmetic or geometric readout basis.

## 5. Cross-repo policy

This file is the canonical pattern owner. Downstream math repositories should reference this page with thin backlinks rather than copying the full pattern.

Expected downstream reference form:

```text
See SocioProphet/systems-learning-loops: kb/patterns/coordinate-basis-vs-readout-basis-involution.md.
```

A downstream repository may add a one-paragraph barrier note explaining how the pattern applies locally, but the claim text, empirical source, and ontology live here.

## 6. Nonclaims

This pattern does not prove Hodge, BSD, Con(PA), P vs NP, RH/GRH, or any Clay problem.

It does not claim that the toy embedding experiment measures the corresponding mathematical systems.

It does not supply the readout basis in any downstream repo. Identifying the readout basis is precisely the hard open problem in each target lane.

It does not treat the pending centroid-basis run as executed.

## 7. Promotion rule

The pattern may be promoted from `positive_prediction_pending` to `empirical_pair_confirmed` only after a corrected readout-basis run is committed with:

```text
1. source code or notebook;
2. fixed random seed;
3. coordinate-basis baseline replay;
4. centroid/readout-basis replay;
5. GF(4)-MOLS mask construction;
6. JSON result artifact;
7. explicit failure criteria.
```

Until then, the confirmed empirical content is the coordinate-basis failure, not the full positive doctrine.