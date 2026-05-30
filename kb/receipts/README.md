# Learning Receipts

Status: draft  
Canon reference: `../../docs/institutional-learning-canon-v0.md`  
Pattern reference: `../patterns/institutional-amnesia.md`

## Purpose

Learning receipts record how a source-backed lesson became an operational change.

A lesson is not fully captured when it is merely discussed, summarized, remembered, or filed as an issue. A lesson is captured when the evidence, claim, pattern, countermeasure, doctrine surface, gate, adoption state, and reobservation plan are traceable.

This directory is the future home for those receipts.

## Minimum receipt fields

A v0 learning receipt should include:

- `receipt_id`: stable identifier.
- `status`: draft, provisional, admitted, superseded, revoked, or expired.
- `date`: date of receipt creation or update.
- `lesson_summary`: concise statement of what was learned.
- `source_refs`: evidence sources or source-ledger references.
- `extract_refs`: bounded quote, log, artifact selector, or observation references.
- `claim_refs`: claims supported, opposed, or qualified by the evidence.
- `pattern_refs`: related pattern records.
- `countermeasure_refs`: adopted or proposed countermeasures.
- `authority_surface`: repo, document, ontology module, policy, test, workflow, checklist, or product surface where the lesson landed.
- `gate_refs`: review question, CI check, validator, fixture, acceptance criterion, or audit process that checks the doctrine.
- `teaching_refs`: Academy object, workroom card, playbook, agent boot note, checklist, or drill derived from the lesson.
- `reobservation_plan`: what future evidence confirms, weakens, supersedes, or revokes the lesson.
- `claim_boundary`: what the receipt does not prove or authorize.

## Receipt states

- `draft`: receipt structure exists but evidence or authority references are incomplete.
- `provisional`: receipt has enough evidence and authority linkage for working use, but has not yet stabilized.
- `admitted`: receipt has source-backed claims, a named pattern or doctrine, an authority surface, and a gate or review mechanism.
- `superseded`: receipt was replaced by a newer receipt or stronger doctrine.
- `revoked`: receipt is no longer valid.
- `expired`: receipt aged out and requires reobservation before further use.

## v0 discipline

Receipts should not be used to launder weak claims into doctrine.

A receipt records the chain from evidence to change. It does not prove the claim by itself. It does not replace source review. It does not create authority outside the target repo or surface.

## Template

```yaml
receipt_id: il.receipt.example
status: draft
date: YYYY-MM-DD
lesson_summary: >-
  One or two sentences describing what was learned.
source_refs: []
extract_refs: []
claim_refs: []
pattern_refs: []
countermeasure_refs: []
authority_surface:
  repo: ""
  artifact: ""
  gate: ""
gate_refs: []
teaching_refs: []
reobservation_plan:
  confirming_signal: ""
  weakening_signal: ""
  supersession_trigger: ""
  review_cadence: ""
claim_boundary: >-
  State what this receipt does not prove, authorize, or settle.
```

## First receipt candidates

The first concrete receipts should cover:

1. Lost-work recovery map creation in `SocioProphet/sociosphere`.
2. DoNotLearn / DoNotLink recovery in `SocioProphet/ontogenesis`.
3. Institutional-learning canon and institutional-amnesia pattern creation in this repo.

Those receipts should remain concise and should point to committed artifacts rather than restating their content.
