# Institutional Amnesia

Status: draft  
Pattern id: `il.pattern.institutional-amnesia`  
Canon reference: `docs/institutional-learning-canon-v0.md`  
Topic lanes: `il.source-discipline`, `il.pattern-library`, `il.doctrine-promotion`, `il.delivery-learning`, `il.workroom-memory-learning`, `il.teaching-and-canonization`

## Summary

Institutional amnesia occurs when important knowledge exists somewhere in the organization or estate but does not remain actionable. The knowledge may live in chat history, operator memory, old planning notes, partial repo artifacts, orphaned issues, stale branches, archived documents, or uncatalogued examples. The failure is not that the knowledge never existed. The failure is that it lacks a current owner, authority surface, receipt, retrieval path, and reobservation mechanism.

## Conditions

Institutional amnesia tends to appear when:

- work happens across many repositories, agents, documents, workrooms, and time horizons;
- high-value concepts are discussed before there is a durable authority surface;
- implementation moves faster than documentation, taxonomy, and receipt generation;
- backlog items are captured as issues but not promoted into doctrine, schemas, tests, or examples;
- important ideas are frozen correctly but lack explicit return conditions;
- repo-local artifacts exist but are not indexed by an estate-level recovery or inventory surface;
- operators rely on memory, chat context, or model recall instead of source-backed records.

## Symptoms

Observable signs include:

- repeated rediscovery of the same concept;
- disagreement about whether prior work was done;
- high-value terms appearing in conversation but not in repo search;
- stale issues with no authority artifact;
- implementation artifacts with no doctrine note or receipt;
- doctrine notes with no owning repo;
- frozen research ideas with no named prerequisite for re-entry;
- recovery work beginning from memory rather than from an indexed ledger.

## Failure modes

When institutional amnesia is not countered:

- strategic concepts become trivia rather than infrastructure;
- agents and humans rebuild partial versions of prior work;
- privacy, governance, safety, and delivery lessons fail to constrain future execution;
- speculative items either disappear entirely or return without their original claim boundaries;
- repo estates accumulate unowned conceptual debt;
- downstream products implement weaker versions of already-discovered doctrine;
- auditability collapses because the source-to-claim-to-doctrine path is missing.

## Forces

The pattern recurs because:

- conversation is faster than canonization;
- issue creation is easier than doctrine promotion;
- implementation pressure rewards local progress over estate-level traceability;
- source-backed evidence requires more discipline than recollection;
- cross-repo work creates ownership ambiguity;
- useful frozen ideas are easy to mistake for abandoned ideas;
- memory systems can retrieve fragments without proving authority or currency.

## Source-backed claims

| Claim id | Claim | Evidence refs | Status |
| --- | --- | --- | --- |
| `il.claim.amnesia.exists-without-absence` | Institutional amnesia can occur even when knowledge exists; the failure is loss of actionable ownership, authority, receipt, and retrieval. | `SocioProphet/sociosphere:docs/strategy/lost-work-recovery-map.md`; `SocioProphet/systems-learning-loops:docs/institutional-learning-canon-v0.md` | proposed |
| `il.claim.recovery-needs-disposition` | A recovered thread must resolve into an owner repo, archive-only status, frozen return condition, or intentional non-pursuit rationale. | `SocioProphet/sociosphere:docs/strategy/lost-work-recovery-map.md` | proposed |
| `il.claim.lesson-needs-loop` | A lesson is not captured merely by noticing it; it must move through source, extract, claim, pattern, countermeasure, doctrine, gate, receipt, teaching, and reobservation. | `docs/institutional-learning-canon-v0.md` | proposed |

## Countermeasures

| Countermeasure id | Countermeasure | Authority surface | Status |
| --- | --- | --- | --- |
| `il.countermeasure.recovery-map` | Maintain a lost-work recovery map for high-value concepts that fell out of active backlog visibility. | `SocioProphet/sociosphere:docs/strategy/lost-work-recovery-map.md` | provisional |
| `il.countermeasure.do-not-lose-again` | Require each recovered thread to have an owner repo, archive-only status, frozen return condition, or intentional closure rationale. | `SocioProphet/sociosphere` | provisional |
| `il.countermeasure.patternize-recovery` | Convert recurring recovery failures into pattern records, not just issue lists. | `SocioProphet/systems-learning-loops` | proposed |
| `il.countermeasure.receipt-backed-promotion` | Promote lessons into doctrine only when the evidence, claim, countermeasure, authority surface, and receipt path are traceable. | `SocioProphet/systems-learning-loops` | proposed |

## Doctrine promotion

| Promotion id | Target repo/surface | Artifact or gate | Status |
| --- | --- | --- | --- |
| `il.promotion.sociosphere-recovery-map` | `SocioProphet/sociosphere` | `docs/strategy/lost-work-recovery-map.md` | provisional |
| `il.promotion.ontogenesis-privacy-recovery` | `SocioProphet/ontogenesis` | DoNotLearn / DoNotLink doctrine, TTL, context, examples, SHACL, validator | provisional |
| `il.promotion.systems-learning-canon` | `SocioProphet/systems-learning-loops` | `docs/institutional-learning-canon-v0.md`; `kb/topics/institutional-learning.yaml`; this pattern | provisional |

## Test / gate

Future recovery work should ask:

- Does the recovered item have an owning repo?
- Does it have an authority artifact or explicit deferred disposition?
- Is there a source-backed claim explaining why it matters?
- Is it patternized if the failure mode can recur?
- Is there a countermeasure and a receipt path?
- Does the item have a reobservation or review trigger?

Machine-checkable gates are deferred until the pattern taxonomy stabilizes. The v0 gate is review-based.

## Teaching object

Human-facing lesson: knowledge that is remembered but not owned is still operationally lost.

Agent-facing boot note: when recovering prior work, do not stop at summary or issue creation. Assign authority, create or update the durable artifact, preserve claim boundaries, and record the next gate.

Workroom card: “Where does this lesson live now, and what proves it will still matter next month?”

Academy object: institutional learning loop exercise using a recovered concept and requiring source, claim, pattern, countermeasure, doctrine, receipt, and reobservation fields.

## Reobservation plan

Confirming signals:

- recovered concepts now have owner repos and durable artifacts;
- future work references the authority artifact instead of relying on memory;
- new patterns are added when recovery failures recur;
- downstream repos consume the doctrine through tests, examples, or review gates.

Weakening signals:

- recovery artifacts are created but never used;
- repo-local implementations diverge from the recovery map;
- lessons remain prose-only without countermeasures;
- operators still need to ask what prior work existed because inventory surfaces are incomplete.

Supersession trigger:

- an estate-level inventory and learning-receipt system makes this pattern mechanically detectable and partially enforceable.

Review cadence:

- review after every major lost-work recovery tranche;
- review when Sociosphere/workspace-inventory gains estate-ledger coverage;
- review when Alexandrian Academy begins consuming teaching objects from this repo.

## Claim boundary

This pattern does not assert that every forgotten or dormant concept should be revived. Some items should remain archive-only, intentionally closed, or frozen with return conditions. The claim is narrower: when a concept is strategically valuable enough to recover, it must receive explicit disposition and a durable authority surface rather than returning to unowned memory.
