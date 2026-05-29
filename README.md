# Research: Internet Origins, Protocol Culture, and Institutional Learning Loops

This repository is both a **topic-driven research pack** and a reusable **institutional-learning canon** for the SocioProphet estate.

At the research-pack layer, we capture **primary sources**, extract **bounded quotes**, turn them into **claims**, and then distill recurring **socio-technical patterns** such as bikeshedding, Eternal September, protocol drift, governance breakdown, and scaling shocks that still govern modern distributed systems and communities.

At the institutional-learning layer, we convert source-backed patterns into countermeasures, doctrine, tests/gates, receipts, and teaching objects that can be consumed by Ontogenesis, GAIA, Sociosphere, Prophet Platform, Agentplane, SCOPE-D, Delivery Excellence, Model Governance Ledger, and Alexandrian Academy.

## Canon entry point

- [`docs/institutional-learning-canon-v0.md`](docs/institutional-learning-canon-v0.md) — canonical loop for turning observations, sources, bounded extracts, claims, and patterns into countermeasures, doctrine, tests/gates, receipts, teaching objects, and reobservation.

## What we are building (deliverables)

1. **Evidence ledger**: a curated catalog of sources with provenance, evidence weight, and deduplication/aliasing.
2. **Quote/extract pack**: short compliant excerpts and bounded observations mapped to claims.
3. **Pattern library**: each “legend” or institutional failure mode becomes an explicit pattern with conditions, symptoms, forces, countermeasures, and limits.
4. **Timeline spine**: dated events linking technical evolution, social scaling shocks, governance breakdowns, and doctrine promotion moments.
5. **Matrix**: mapping from stack component or institutional surface to stressors such as moderation, identity, replication, admission, drift, memory, and accountability.
6. **Ontology**: an RDF/JSON-LD schema that makes the above machine-readable and composable with the broader Socioprophet knowledge fabric.
7. **Learning receipts**: records connecting evidence, claims, patterns, countermeasures, doctrine, tests/gates, and downstream adoption.
8. **Teaching objects**: human- and agent-facing lessons, checklists, workroom cards, boot-contract notes, drills, and Academy-ready materials.

## Repository layout

- `kb/`
  - `sources/` — source registry (YAML) + derived JSON-LD
  - `patterns/` — pattern pages (Markdown) + instances (YAML)
  - `quotes/` — extracted quotes (bounded) + locations
  - `claims/` — claim statements tied to sources and quotes
  - `topics/` — topic taxonomy and research domains
- `docs/` — canon, doctrine, and process notes
- `ontology/`
  - `internet-legends.ttl` — core classes and properties (RDF/Turtle)
  - `context.jsonld` — JSON-LD context for the same vocabulary
- `matrix/` — crosswalks and comparison tables
- `timeline/` — timeline artifacts and event records
- `scripts/` — validation and conversion helpers

## Principles (non-negotiable)

- **Primary-first**: RFCs, institutional exhibits, archival publications, source-controlled artifacts, reproducible run outputs, and signed receipts outrank wikis/blogs/forums.
- **Quote-bounded**: keep excerpts short and always cite location.
- **Claims > vibes**: every assertion is a claim node that points to supporting sources.
- **Dedup explicitly**: same artifact hosted in multiple places must be linked via `alias_of`.
- **Commons semantics**: neutral, non-enterprise framing; focus on open civic/cultural knowledge.
- **Doctrine requires receipts**: a lesson is not promoted until the evidence, claim, pattern, countermeasure, authority surface, and review path are traceable.

## Quickstart (local)

We keep local repos under `~/dev/<reponame>` by default.

```bash
mkdir -p ~/dev
cd ~/dev
# put this repo directory here, then:
git init
git add .
git commit -m "Initialize research pack: internet legends"
```

## Status

This repo is scaffolded. The next commit wave is to fill `kb/sources/sources.yaml` with the complete enumerated list, generate `kb/sources/sources.jsonld`, start extracting quotes for P0 sources, and add the first institutional-learning topic taxonomy under `kb/topics/`.
