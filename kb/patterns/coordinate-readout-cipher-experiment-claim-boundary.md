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
increase selectivity while preserving V4 translation involution?
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

## 4. Involution convention

In this document, `involution` means the additive `V4` translation structure, not involutivity of each Latin-square readout map.

For every element:

```text
a in GF(4)
```

characteristic two gives:

```text
a + a = 0.
```

Therefore every translation:

```text
tau_a(x) = x + a
```

satisfies:

```text
tau_a(tau_a(x)) = x.
```

The maps:

```text
L_1(x,y) = x + y
L_alpha(x,y) = alpha*x + y
```

are readout/MOLS maps. They are not required to be involutions. The involutive operators diagnosed by the experiment are the `V4` translation masks and their induced action under the readout construction.

A run that treats `L_alpha` itself as an involution fails this claim boundary.

## 5. Z4 rejection requirement

The run must explicitly reject cyclic `Z4` substitution.

The negative control is:

```text
Z4 may provide a Latin table.
Z4 is not V4.
Z4 is not the additive group of GF(4).
Z4 is not all-involutive: 1 in Z4 has order 4.
Z4 is not the required all-involutive readout structure.
Z4 must not be used as the canonical MOLS mask source.
```

The rejection is a structural guardrail, not an empirical preference.

If a run silently permits `Z4` as a substitute for `GF(4)`, the run fails the claim boundary even if selectivity improves.

## 6. Corrected centroid/readout basis

The term `corrected centroid` must be operationalized before execution.

### 6.1 Readout embedding

Use the pinned `GF(2)`-coordinate embedding:

```text
iota: GF(4) -> F2^2 subset R^2

iota(0)         = (0, 0)
iota(1)         = (1, 0)
iota(alpha)     = (0, 1)
iota(alpha + 1) = (1, 1)
```

This is the v0 readout coordinate system for the pinned presentation:

```text
GF(4) = F2[alpha] / (alpha^2 + alpha + 1).
```

A trace-dual basis may be explored only as a separately labeled sensitivity run.

### 6.2 Null centroid

For each pinned readout `L_m`, define the analytic null centroid under uniform measure on `GF(4)^2`:

```text
c_null = E[iota(L_m(x,y))] = (1/2, 1/2).
```

This centroid is computed in closed form. It uses no training data.

The sample centroid for a run is:

```text
c_sample = mean_i iota(L_m(x_i, y_i)).
```

Balance metric:

```text
balance_metric = ||c_sample - c_null||_2 / sqrt(2)
```

This lies in `[0,1]` because the ambient readout space is the unit square.

### 6.3 Centroid training data

The analytic null centroid uses no training data.

For comparison against the earlier coordinate-basis run, the baseline centroid must be imported from the prior run by:

```yaml
baseline_provenance:
  code_hash: string
  data_hash: string
  convention_hash: string
```

No centroid may be trained on the corrected-run sample.

### 6.4 Normalization

All centroid distances use the same fixed normalization:

```text
normalized_distance = ||c_sample - c_null||_2 / sqrt(2)
```

No per-run rescaling is allowed.

This keeps balance and selectivity outputs composable across diagnostic runs.

### 6.5 Predeclaration binding

The readout-basis block must be hashed before mask construction and before scoring:

```yaml
readout_basis:
  embedding: iota_GF4_to_F2xF2
  centroid_definition: analytic_uniform_GF4xGF4_expectation
  centroid_training_data: none
  normalization: L2_distance_over_sqrt2
  predeclared_before_masks: true
  predeclared_before_scores: true
  convention_hash: string
```

If this block changes after the run begins, the convention hash changes and the run fails the boundary check.

## 7. Selectivity metric v0

The v0 selectivity metric is a target-vs-incorrect-mask margin in the fixed `iota` readout coordinates.

For each nonzero `a in GF(4)`, let the intended translation mask be:

```text
tau_a(z) = z + a.
```

Let `delta_a` be the observed mean readout displacement induced by `tau_a` in the corrected basis. Let:

```text
t_a = iota(a)
```

be the intended displacement label. Define:

```text
correct_distance_a   = ||delta_a - t_a||_2 / sqrt(2)
incorrect_distance_a = min_{b != a, b != 0} ||delta_a - iota(b)||_2 / sqrt(2)
selectivity_margin_a = incorrect_distance_a - correct_distance_a
```

Aggregate selectivity:

```text
selectivity = mean_{a in GF(4)^*} selectivity_margin_a.
```

Positive selectivity means the observed displacement is closer to the intended nonzero `V4` translation than to any incorrect nonzero translation. Negative selectivity means the run is closer to an incorrect mask than the intended mask.

Baseline selectivity must be computed by the same formula on the coordinate-basis baseline artifact or imported with provenance if already computed.

Selectivity lift:

```text
selectivity_lift_vs_coordinate = selectivity_corrected / max(abs(selectivity_coordinate), epsilon_floor)
```

The run must report the `epsilon_floor` used. The default is:

```text
epsilon_floor = 1e-12.
```

## 8. Failure criteria v0

Separate validity of the run from confirmation of the prediction.

### 8.1 Run-validity pass

A run is valid only if:

```text
1. GF(4) / L_1 / L_alpha construction is used first.
2. Z4 substitution is explicitly rejected.
3. Coordinate-basis baseline is replayed or imported with provenance.
4. Corrected readout/centroid basis is predeclared and convention-hashed.
5. Involution error for all nonzero tau_a satisfies the declared tolerance.
6. Selectivity is computed by the v0 margin metric.
7. Balance is computed by normalized centroid distance to (1/2, 1/2).
8. No post-hoc mask-family selection occurs.
9. Result artifact includes provenance and nonclaims.
```

Default involution tolerance:

```text
involution_error_tolerance = 1e-12
```

### 8.2 Prediction outcome labels

A valid run receives one of these labels:

```text
empirical_pair_confirmed:
  selectivity_lift_vs_coordinate >= 5
  balance_metric_corrected <= balance_metric_coordinate
  involution_error <= tolerance

weak_support:
  selectivity_lift_vs_coordinate > 1
  balance_metric_corrected <= balance_metric_coordinate
  involution_error <= tolerance

falsified_directional:
  selectivity_lift_vs_coordinate <= 1
  or balance_metric_corrected > balance_metric_coordinate
  or involution_error > tolerance
```

The earlier 5x-50x expectation is a prediction band, not a run-validity criterion.

A result below 5x but above 1x is weak support, not confirmation. A result at or below 1x falsifies the directional prediction unless separately explained by a predeclared diagnostic failure.

## 9. Required outputs

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
  involution_operators: V4_translations_tau_a
  z4_rejected: true
readout_basis:
  embedding: iota_GF4_to_F2xF2
  centroid_definition: analytic_uniform_GF4xGF4_expectation
  centroid_training_data: none
  normalization: L2_distance_over_sqrt2
  convention_hash: string
baseline:
  coordinate_basis_involution_error: number
  coordinate_basis_selectivity: number
  coordinate_basis_balance_metric: number
  provenance:
    code_hash: string
    data_hash: string
    convention_hash: string
corrected_run:
  involution_error: number
  selectivity: number
  selectivity_lift_vs_coordinate: number
  balance_metric: number
  composability_metric: number
  outcome_label: empirical_pair_confirmed | weak_support | falsified_directional
failure_criteria:
  declared: true
  involution_error_tolerance: 1e-12
  epsilon_floor: 1e-12
provenance:
  code_hash: string
  data_hash: string
  convention_hash: string
  generated_at: string
nonclaims:
  - string
```

## 10. Nonclaims

This experiment does not claim:

```text
- Hodge, BSD, Con(PA), P vs NP, RH/GRH, or Clay progress;
- that typological parallels are formal reductions;
- that the toy embedding/cipher experiment measures the mathematical systems named in the parallels;
- that readout-basis identification is solved in any downstream repo;
- that a positive selectivity lift proves a theorem;
- that a negative result refutes the mathematical analogies;
- that GF(4) is the unique useful finite-field construction beyond this pinned run;
- that cipher terminology is the only interpretation of the transform;
- that the affine MOLS maps L_m themselves are involutions.
```

## 11. Composition rule

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

## 12. Implementation gate

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