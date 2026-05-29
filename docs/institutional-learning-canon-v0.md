# Institutional Learning Canon v0

Status: draft  
Authority plane: `SocioProphet/systems-learning-loops`  
Scope: evidence-backed institutional learning loops for research, delivery, governance, product, agent behavior, and doctrine promotion

## Purpose

This document generalizes the repository's existing research-pack method into a reusable institutional-learning canon for the SocioProphet estate.

The original method remains intact: primary sources, bounded extracts, source-backed claims, pattern pages, timelines, matrices, and ontology-ready records. This canon adds the downstream loop: how validated lessons become countermeasures, doctrine, tests, gates, receipts, and teaching objects.

The goal is to prevent institutional amnesia. A lesson is not captured merely because someone noticed it. A lesson is captured when it is source-backed, claim-bounded, patternized, assigned to an authority surface, and converted into a repeatable change with a receipt.

## Canonical loop

```text
Observe -> Source -> Quote/Extract -> Claim -> Pattern -> Countermeasure -> Doctrine -> Test/Gate -> Receipt -> Teach -> Reobserve
```

### Observe

An event, source, incident, historical pattern, delivery failure, operator note, user feedback, system behavior, or research finding enters attention.

Observation is not evidence by itself. It starts the loop.

### Source

The observation is linked to a source with provenance, date, author/institution where available, source type, evidence weight, and deduplication status.

Primary sources, institutional exhibits, RFCs, standards, logs, reproducible run outputs, and repo-local receipts outrank commentary and recollection.

### Quote/Extract

A bounded extract captures the relevant evidence without over-quoting or laundering interpretation into the source.

An extract may be a short quote, log excerpt, event fragment, command output, table row, metric, artifact selector, image region, audio segment, or structured observation.

### Claim

A claim is a bounded assertion linked to one or more sources and extracts.

Claims must remain smaller than conclusions. Claims can be supported, opposed, qualified, superseded, revoked, or left provisional.

### Pattern

A pattern is a recurring socio-technical structure extracted from claims.

A pattern must describe conditions, symptoms, failure modes, forces, countermeasures, and known limits. A pattern is not a vibe, slogan, or retrospective moral.

### Countermeasure

A countermeasure is an operational response to a pattern.

Countermeasures may be process changes, repo policies, product affordances, ontology terms, validation checks, playbooks, threat-model updates, governance rules, training material, or agent behavior constraints.

### Doctrine

Doctrine is the promoted form of a countermeasure.

Promotion requires an authority surface: a repo-local document, ontology module, policy object, SHACL shape, test, workflow, checklist, operating rule, or product contract.

### Test/Gate

A test or gate checks whether doctrine is being followed.

Not all doctrine is machine-checkable at v0. When it is not, the gate may be a review checklist, acceptance criterion, audit receipt, fixture, runbook, or explicit review question.

### Receipt

A receipt records what changed, why, from what evidence, under whose authority, and how it will be checked later.

Receipts prevent lessons from becoming untraceable culture.

### Teach

A teaching object turns a pattern into a reusable explanation for humans or agents.

Teaching objects may become Alexandrian Academy lessons, workroom notes, checklists, cards, walkthroughs, examples, drills, or agent boot contracts.

### Reobserve

A learned doctrine remains live only if the system can detect drift, regression, overfitting, misuse, or changed conditions.

Reobservation closes the loop and turns learning into cybernetic control rather than static documentation.

## Canon objects

### LearningSource

A primary or secondary source with provenance, evidence weight, aliases, source type, date, and retrieval/citation metadata.

Expected home: `kb/sources/`.

### BoundedExtract

A short compliant excerpt, observation, log fragment, artifact selector, or event fragment used as evidence.

Expected home: `kb/quotes/` or a future generalized `kb/extracts/` lane.

### LearningClaim

A bounded assertion linked to supporting, opposing, or qualifying sources and extracts.

Expected home: `kb/claims/`.

### LearningPattern

A recurring socio-technical structure with conditions, symptoms, forces, failure modes, countermeasures, and limits.

Expected home: `kb/patterns/`.

### Countermeasure

A proposed or adopted operational response to a learning pattern.

Expected home: pattern pages at v0; later may become its own structured lane.

### DoctrinePromotion

A record that a countermeasure has been promoted into an authority surface.

Examples include an Ontogenesis vocabulary term, Prophet Platform workroom rule, Agentplane action gate, SCOPE-D validation scenario, Delivery Excellence checklist, or Sociosphere stabilization rule.

### LearningReceipt

A record connecting evidence, claim, pattern, countermeasure, doctrine, test/gate, and adoption state.

A learning receipt should answer: what did we learn, from what evidence, what changed, where did it land, and how will we know whether it still works?

### TeachingObject

A human- or agent-facing explanation derived from a pattern and its doctrine.

Examples include Alexandrian Academy lessons, workroom cards, agent boot-contract notes, examples, checklists, drills, or short operator-facing summaries.

## Repo consumers

| Consumer repo | How it consumes this canon |
| --- | --- |
| `SocioProphet/ontogenesis` | Converts stable learning patterns into vocabularies, semantic constraints, contexts, shapes, and ontology-backed doctrine. |
| `SocioProphet/gaia-world-model` | Supplies world evidence, observation manifests, temporal/geospatial evidence, and world-learning events. |
| `SocioProphet/sociosphere` | Tracks cross-repo adoption, stabilization state, recovery ledgers, and estate-level learning drift. |
| `SocioProphet/prophet-platform` | Turns lessons into workroom rules, memory behavior, topic-pack behavior, UX affordances, and operator-facing substrate. |
| `SocioProphet/agentplane` | Converts doctrine into action-admission behavior, agent boot constraints, runtime receipts, and effectful-work gates. |
| `SocioProphet/SCOPE-D` | Converts patterns into defensive tests, purple-team exercises, empirical feedback, and threat-model updates. |
| `SocioProphet/delivery-excellence` | Converts lessons into delivery discipline, acceptance criteria, postmortem loops, and execution-quality gates. |
| `SocioProphet/model-governance-ledger` | Records learning events, evaluation outcomes, drift, inference/training receipts, and model-governance feedback loops. |
| `SocioProphet/alexandrian-academy` | Converts teaching objects into canonized learning materials, review cards, lessons, and next-best-action guidance. |

## Promotion discipline

A lesson may not jump directly from observation to doctrine.

The minimum promotion path is:

```text
source-backed extract -> bounded claim -> named pattern -> countermeasure -> authority surface -> receipt
```

Skipping this path creates brittle doctrine: rules with no evidence, tests with no claim, policies with no source, or cultural memory with no receipt.

## Claim boundaries

This canon does not claim that every historical source produces a correct lesson. It does not promote anecdotes to policy. It does not treat pattern names as proof. It does not replace domain-specific review in consumer repos.

The canon defines a learning-control process. Individual claims, patterns, and countermeasures retain their own evidence grade.

## First implementation path

The first implementation stage should remain document- and taxonomy-level:

1. define this canon document;
2. add an institutional-learning topic taxonomy;
3. add one or two example pattern records showing the full path from source to doctrine;
4. only then consider YAML/JSON-LD schemas or ontology terms.

The canonical repo principle remains: primary-first, quote-bounded, claims-over-vibes, explicit deduplication, and commons semantics.
