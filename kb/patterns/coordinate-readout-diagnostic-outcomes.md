# Coordinate/Readout Diagnostic Outcome Semantics

Status: **outcome-semantics note / computational-diagnostic consumer guide / not result evidence**.  
Applies to: `COORD_READOUT_INVOLUTION_001`.  
Diagnostic implementation: `experiments/coordinate_readout_cipher_diagnostic.py`.  
Boundary: `kb/patterns/coordinate-readout-cipher-experiment-claim-boundary.md`.

## 0. Purpose

The coordinate/readout diagnostic is now implemented. This note defines what each possible result licenses and what it rules out.

The diagnostic remains:

```yaml
evidence_class: computational_diagnostic
```

It is not theorem-facing evidence.

## 1. What the diagnostic measures

The diagnostic measures whether the pinned readout construction improves a v0 selectivity metric while preserving the finite-field structure declared in the boundary document.

Pinned structure:

```text
GF(4) = F2[alpha]/(alpha^2 + alpha + 1)
V4 translation involution tau_a(x)=x+a
MOLS/readout pair L_1 / L_alpha
iota: GF(4) -> F2^2 -> R^2
analytic null centroid (1/2, 1/2)
```

The corrected displacement order is:

```text
delta = iota(L_m(tau_a(x), y) + L_m(x, y))
```

not Euclidean subtraction after embedding.

## 2. Outcome fields

The receipt separates:

```yaml
statuses:
  protocol_valid: boolean
  prediction_outcome: protocol_incomplete | empirical_pair_confirmed | weak_support | falsified_directional
```

These fields have different meanings and must not be collapsed into a single pass/fail result.

## 3. Protocol-invalid outcome

### 3.1 Definition

`protocol_valid: false` means the run did not satisfy the pinned boundary conditions.

Examples:

```text
- missing or invalid baseline provenance;
- absent boundary hash;
- failure to reject Z4;
- missing readout-basis predeclaration;
- involution error above tolerance;
- output schema incomplete.
```

### 3.2 What it licenses

A protocol-invalid run licenses only this conclusion:

```text
No empirical inference can be drawn from this run.
```

It may justify implementation repair or boundary amendment, depending on the failure.

### 3.3 What it does not rule out

It does not rule out:

```text
- the v0 directional prediction;
- the coordinate/readout-basis pattern;
- GF(4) / V4 as the correct structure for this diagnostic;
- any typological parallel.
```

A protocol-invalid result is a failed measurement, not a negative diagnostic result.

## 4. `falsified_directional`

### 4.1 Definition

A valid run receives `falsified_directional` if:

```text
protocol_valid == true
and one or more of:
  selectivity_lift_vs_coordinate <= 1
  balance_metric_corrected > balance_metric_coordinate
  involution_error > tolerance
```

### 4.2 What it licenses

This outcome licenses:

```text
The v0 directional prediction failed under the pinned construction.
```

The KB claim should be updated to record that the corrected readout-basis run did not improve the v0 metric under the pinned `GF(4)` / `L_1` / `L_alpha` / `iota` convention.

### 4.3 What it rules out

It rules out only:

```text
v0 directional support under the pinned protocol.
```

It does not rule out:

```text
- the broader coordinate/readout-basis pattern;
- all GF(4)-based readout constructions;
- trace-dual embeddings or other predeclared future embeddings;
- other selectivity metrics;
- Hodge/BSD/Con(PA)/mu2/spectral analogies;
- theorem-facing uses.
```

Any alternative construction must be introduced by a new boundary document before rerun. It may not be selected post hoc to rescue the prediction.

## 5. `weak_support`

### 5.1 Definition

A valid run receives `weak_support` if:

```text
protocol_valid == true
selectivity_lift_vs_coordinate > 1
balance_metric_corrected <= balance_metric_coordinate
involution_error <= tolerance
selectivity_lift_vs_coordinate < 5
```

### 5.2 What it licenses

This outcome licenses:

```text
The v0 readout-basis direction improved over baseline, but below the predeclared 5x confirmation threshold.
```

The KB claim may be updated from `positive_prediction_pending` to a weak-support status for this exact v0 diagnostic.

Recommended status wording:

```text
computational_diagnostic_weak_support_v0
```

### 5.3 What it does not license

It does not license:

```text
- empirical_pair_confirmed;
- theorem-facing support;
- cross-repo promotion;
- I-12 promotion;
- replacement of the v0 metric with a stronger metric after observing the result.
```

## 6. `empirical_pair_confirmed`

### 6.1 Definition

A valid run receives `empirical_pair_confirmed` if:

```text
protocol_valid == true
selectivity_lift_vs_coordinate >= 5
balance_metric_corrected <= balance_metric_coordinate
involution_error <= tolerance
```

The 5x lower bound is the confirmation threshold for the v0 diagnostic. The earlier 5x-50x prediction band is recorded as background expectation; the receipt should still report whether the observed lift is below, within, or above the band if that field exists.

### 6.2 What it licenses

This outcome licenses:

```text
The coordinate/readout-basis claim has a complete v0 empirical pair:
  coordinate-basis negative result;
  readout-basis positive result under the pinned GF(4) construction.
```

The claim record may be updated from:

```text
empirical_basis_confirmed__positive_prediction_pending
```

to a status such as:

```text
empirical_pair_confirmed_v0
```

The source record may attach the receipt as the positive readout-basis result.

### 6.3 What it does not license

It does not license:

```text
- theorem-facing status;
- proof of any mathematical conjecture;
- formal reduction to Hodge, BSD, Con(PA), np-program, or Heller-Winters;
- claim that readout-basis identification is solved in any downstream repo;
- generalization to other fields, groups, embeddings, or metrics;
- I-12 promotion.
```

## 7. `protocol_valid: true` with any prediction outcome

A protocol-valid run, regardless of result, licenses a provenance update:

```text
The diagnostic has been executed under the pinned boundary.
```

It does not by itself determine whether the prediction was confirmed.

The prediction outcome is carried only by:

```yaml
statuses.prediction_outcome
```

and the associated metrics.

## 8. Positive-outcome distinction rule

The distinction between `weak_support` and `empirical_pair_confirmed` is a **threshold-strength distinction** inside the v0 metric, not a replication distinction and not a partial-scope distinction.

Concretely:

```text
weak_support:
  1 < selectivity_lift_vs_coordinate < 5

empirical_pair_confirmed:
  selectivity_lift_vs_coordinate >= 5
```

both with:

```text
protocol_valid == true
balance_metric_corrected <= balance_metric_coordinate
involution_error <= tolerance
```

Therefore:

```text
- weak_support is not a single-run placeholder for later replication;
- empirical_pair_confirmed is not a statement about replication count;
- weak_support is not partial confirmation of only some downstream mathematical scope;
- empirical_pair_confirmed does not widen the scope beyond the pinned v0 diagnostic.
```

Every receipt carrying either positive outcome must record the actual measured values for at least:

```text
selectivity_lift_vs_coordinate
balance_metric_corrected
balance_metric_coordinate
involution_error
tolerance
confirmation_threshold
```

The confirmation threshold is fixed at `5` for this v0 diagnostic unless a later boundary document supersedes it before execution.

## 9. Consequence table

| Protocol valid | Prediction outcome | Licensed update | Ruled out |
|---|---|---|---|
| false | protocol_incomplete | no empirical inference; repair protocol | nothing about the hypothesis |
| true | falsified_directional | v0 directional prediction failed | only v0 support under pinned protocol |
| true | weak_support | weak v0 computational support | empirical-pair confirmation and theorem claims |
| true | empirical_pair_confirmed | v0 empirical pair confirmed | theorem / cross-repo / Clay claims still not licensed |

## 10. Composition rule

No diagnostic outcome may be composed into a higher-level claim without a composition warrant.

Required schema:

```yaml
composition_warrant:
  inputs: list[string]
  target_claim: string
  evidence_classes: list[string]
  reason_composition_is_valid: string
  nonclaims: list[string]
```

Without a composition warrant, citations to this diagnostic remain descriptive.

## 11. Canonical computational-diagnostic non-license list

Because this artifact's maximum evidence class is `computational_diagnostic`, no outcome from this diagnostic licenses:

```text
- theorem-facing claims;
- A2-track promotion;
- I-12 claims;
- Hodge claims;
- BSD claims;
- Con(PA) claims;
- P vs NP claims;
- RH / GRH claims;
- Clay-prize-level claims.
```

This list is stated here because these are known adjacent overreach surfaces for coordinate/readout-style diagnostics. Future diagnostics may inherit this list only if their boundary document explicitly says they use the canonical computational-diagnostic non-license list.

If a future diagnostic has different adjacent overreach surfaces, it must add its own local non-license list rather than silently relying on this one.

## 12. Nonclaims

This outcome semantics note does not claim:

```text
- any diagnostic outcome has occurred;
- the v0 prediction is true or false;
- the diagnostic is theorem-facing;
- any cross-repo mathematical program is advanced;
- any Hodge, BSD, Con(PA), P vs NP, RH/GRH, or Clay progress.
```

It defines how to interpret future diagnostic receipts.
