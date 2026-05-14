# Coordinate/Readout Cipher Experiment Claim Boundary

Status: **claim-boundary document / Issue #3 pre-run gate / not result evidence**.  
Canonical pattern: `kb/patterns/coordinate-basis-vs-readout-basis-involution.md`.  
Canonical claim: `kb/claims/coordinate-basis-vs-readout-basis.yaml`.  
Source record: `kb/sources/cipher-involution-experiment.yaml`.  
Related issue: `#3` — corrected centroid/readout-basis cipher experiment.

## 0. Purpose

This document defines what the corrected cipher/readout experiment may claim before the run occurs.

The experiment is meant to test whether moving an involutive transform from a coordinate basis into a predeclared readout/centroid basis improves selectivity while preserving:

```text
involution + selectivity + balance + composability
```

The experiment is not theorem-facing. It is a computational diagnostic for the canonical KB pattern.

## 1. Evidence class

The corrected run has evidence class:

```yaml
evidence_class: computational_diagnostic
claim_role: empirical_basis_update
stage: pending_run
```

It is not:

```yaml
evidence_class: theorem_facing
```

and it is not a proof artifact for Hodge, BSD, Con(PA), `np-program`, Heller-Winters, or any Clay-adjacent claim.

## 2. What is being tested

The run tests this empirical question:

```text
Given a fixed coordinate-basis negative result with selectivity approximately 0.015,
does the predeclared centroid/readout-basis construction using GF(4)-based MOLS
increase selectivity while preserving involution?
```

The confirmed prior result is:

```text
coordinate-basis involution error < 1e-16
coordinate-basis selectivity ≈ 0.015
```

The prediction under test is:

```text
readout-basis selectivity lift: 5x to 50x
```

This prediction is pending. It must not be reported as confirmed before the corrected run lands.

## 3. Pinned construction

The run must use the construction already pinned in Issue #3.

Field:

```text
GF(4) = F2[alpha] / (alpha^2 + alpha + 1)
elements = [0, 1, alpha, alpha + 1]
```

Affine MOLS family:

```text
L_m(x, y) = m x + y
```

Canonical pair:

```text
L_1(x, y)     = x + y
L_alpha(x,y) = alpha x + y
```

This pair is an input convention, not an output selected after observing results.

Sensitivity runs over other `GF(4)` slope choices are allowed only after the canonical run is recorded and must be labeled as sensitivity analysis.

## 4. Z4 rejection requirement

The run must explicitly reject cyclic `Z4` substitution.

The negative control is:

```text
Z4 may provide a Latin table.
Z4 is not V4.
Z4 is not the additive group of GF(4).
Z4 is not the required all-involutive readout structure.
Z4 must not be used as the canonical MOLS mask source.
```

The rejection is a structural guardrail, not an empirical preference.

If a run silently permits `Z4` as a substitute for `GF(4)`, the run fails the claim boundary even if selectivity improves.

## 5. Corrected centroid/readout basis

The term `corrected centroid` must be operationalized before execution.

The run must specify:

```yaml
readout_basis:
  centroid_definition: string
  centroid_training_data: string
  normalization: string
  predeclared_before_masks: true
  predeclared_before_scores: true
```

The correction must state what was wrong with the earlier coordinate or centroid construction, and why the new construction is the intended readout basis.

The implementation may use the word `cipher`, but the empirical object is the basis-aligned involutive transform. Cipher language is interpretive framing; the measured quantities are basis, masks, involution error, selectivity, and balance/composability diagnostics.

## 6. Required outputs

The run must emit a machine-readable result artifact containing:

```yaml
experiment_id: string
claim_id: COORD_READOUT_INVOLUTION_001
pattern: coordinate-basis-vs-readout-basis-involution
evidence_class: computational_diagnostic
construction:
  field: GF(4)
  presentation: F2[alpha]/(alpha^2 + alpha + 1)
  element_order: [0, 1, alpha, alpha + 1]
  mols_pair: [L_1, L_alpha]
  z4_rejected: true
baseline:
  coordinate_basis_involution_error: number
  coordinate_basis_selectivity: number
corrected_run:
  readout_basis_definition: string
  involution_error: number
  selectivity: number
  selectivity_lift_vs_coordinate: number
  balance_metric: number
  composability_metric: number
failure_criteria:
  declared: true
provenance:
  code_hash: string
  data_hash: string
  convention_hash: string
  generated_at: string
nonclaims:
  - string
```

## 7. Pass / fail semantics

A run passes the diagnostic only if:

```text
1. GF(4) / L_1 / L_alpha construction is used first.
2. Z4 substitution is explicitly rejected.
3. Coordinate-basis baseline is replayed or imported with provenance.
4. Corrected readout/centroid basis is predeclared.
5. Involution error remains within the declared tolerance.
6. Selectivity lift is measured without post-hoc mask-family selection.
7. Failure criteria are declared before scoring.
8. Result artifact includes provenance and nonclaims.
```

A run may falsify the prediction. If selectivity does not lift by the predicted 5x-50x range, the correct action is to update the claim status, not to search for a new MOLS construction until success.

## 8. Nonclaims

This experiment does not claim:

```text
- Hodge, BSD, Con(PA), P vs NP, RH/GRH, or Clay progress;
- that typological parallels are formal reductions;
- that the toy embedding/cipher experiment measures the mathematical systems named in the parallels;
- that readout-basis identification is solved in any downstream repo;
- that a positive selectivity lift proves a theorem;
- that a negative result refutes the mathematical analogies;
- that GF(4) is the unique useful finite-field construction beyond this pinned run;
- that cipher terminology is the only interpretation of the transform.
```

## 9. Composition rule

Fixture-level or computational-diagnostic evidence may not be composed into a higher-level claim without a composition warrant.

Any document that cites multiple computational diagnostics as support for a theorem-facing or cross-repo claim must include:

```yaml
composition_warrant:
  inputs: list[string]
  target_claim: string
  reason_composition_is_valid: string
  nonclaims: list[string]
```

Without a composition warrant, combined citation of multiple diagnostics remains descriptive only.

## 10. Implementation gate

Issue #3 may proceed only after this claim-boundary document is merged or otherwise referenced by the implementation PR.

The implementation PR must state:

```text
This PR implements the computational diagnostic defined by
kb/patterns/coordinate-readout-cipher-experiment-claim-boundary.md.
```

and must preserve the evidence class:

```yaml
evidence_class: computational_diagnostic
```