# Contributing

We treat every addition as an evidentiary artifact.

## Minimal contribution checklist

- Add or update `kb/sources/sources.yaml`:
  - include `id`, `title`, `type` (primary/secondary/tertiary), `url`, `venue`, `author`, `year`
  - if duplicate hosting: set `alias_of`
- If adding a claim:
  - create `kb/claims/<id>.md`
  - link at least one source id
  - include at least one bounded quote id (when available)
- If adding a pattern:
  - create `kb/patterns/<pattern_slug>.md` using the template

## Evidence weight rubric

Primary (P): RFCs, original publications, institutional exhibits, archival scans  
Secondary (S): reputable analyses that cite primary sources  
Tertiary (T): wiki/blog/forum summaries (use as leads, not load-bearing)
