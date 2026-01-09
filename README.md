# Research: Internet Origins, Protocol Culture, and Legendary Growing Pains

This repository is a **topic-driven research pack**: we capture **primary sources**, extract **bounded quotes**, turn them into **claims**, and then distill recurring **socio-technical patterns** (e.g., bikeshedding, Eternal September) that still govern modern distributed systems and communities.

## What we are building (deliverables)

1. **Evidence ledger**: a curated catalog of sources with provenance, evidence weight, and deduplication/aliasing.
2. **Quote pack**: short compliant excerpts mapped to claims (avoid long verbatim extracts).
3. **Pattern library**: each “legend” becomes an explicit pattern with conditions, symptoms, and countermeasures.
4. **Timeline spine**: dated events linking technical evolution + social scaling shocks.
5. **Matrix**: mapping from stack component (BBS/Usenet/email/web) to stressors (moderation, identity, replication, etc.).
6. **Ontology**: an RDF/JSON-LD schema that makes the above machine-readable and composable with the broader Socioprophet knowledge fabric.

## Repository layout

- `kb/`
  - `sources/` — source registry (YAML) + derived JSON-LD
  - `patterns/` — pattern pages (Markdown) + instances (YAML)
  - `quotes/` — extracted quotes (bounded) + locations
  - `claims/` — claim statements tied to sources and quotes
  - `topics/` — topic taxonomy and research domains
- `ontology/`
  - `internet-legends.ttl` — core classes and properties (RDF/Turtle)
  - `context.jsonld` — JSON-LD context for the same vocabulary
- `matrix/` — crosswalks and comparison tables
- `timeline/` — timeline artifacts and event records
- `scripts/` — validation and conversion helpers

## Principles (non-negotiable)

- **Primary-first**: RFCs, institutional exhibits, archival publications outrank wikis/blogs/forums.
- **Quote-bounded**: keep excerpts short (and always cite location).
- **Claims > vibes**: every assertion is a claim node that points to supporting sources.
- **Dedup explicitly**: same artifact hosted in multiple places must be linked via `alias_of`.
- **Commons semantics**: neutral, non-enterprise framing; focus on open civic/cultural knowledge.

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

This repo is scaffolded; the next commit wave is to fill `kb/sources/sources.yaml` with the complete enumerated list, then generate `kb/sources/sources.jsonld` and start extracting quotes for P0 sources.
