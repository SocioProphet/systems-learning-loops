# OCW Corpus — Vectorized Teaching Objects for the Alexandrian Academy

A reproducible pipeline that turns the **MIT OpenCourseWare catalog** into a portable,
precomputed **vector brain** plus structured training materials (lectures, problem sets,
solutions, exams) — the substrate an agent studies, attempts, and is graded on in the
learning loop.

> **Pull the vectors:** `git lfs pull` after cloning. The brain is under
> `corpus/vectors/<subject>/<course>.jsonl` (base64-float32, 768-d nomic-embed).

## What's here

| Path | Contents |
|---|---|
| `vectors/` | **The brain** — precomputed embeddings, one JSONL per course, classified by material (lecture / recitation / assignment / solution / exam / reference). Git-LFS. |
| `pipeline/` | The end-to-end scripts (capture → vectorize → educate → study → grade → analyze) |
| `lib/` | Reusable engine: `hellgraph-semantic.ts` (the vector store + brain import/export) and `graph-surface.ts` (subgraph selection) |
| `catalog/` | `ocw_all_slugs.txt` (full 2,577-course OCW catalog) + `capture_manifest.jsonl` (what's been captured) |

## The vector format

Each line in a course shard:
```json
{ "slug": "...", "field": "mathematics", "material": "lecture", "level": 100,
  "file": "...", "ci": 0, "text": "<chunk>", "dims": 768, "vec": "<base64-float32>" }
```
- **768-d** `nomic-embed-text` embeddings, stored compact (base64 little-endian float32)
- `material` carries the OCW taxonomy so the curriculum structure (gradeable problems,
  solutions, exams) survives in the vectors, not just prose

Current snapshot: **~66,900 vectors across 30 courses** (math-dense — the dense-first
ordering vectorizes the equation-heavy STEM first).

## How to use it

**Inject the brain into a HellGraph agent (no re-embedding):**
```bash
npx tsx pipeline/inject-brain.ts corpus/vectors/mathematics --probe "chain rule"
```
This decodes the precomputed vectors straight into the atomspace via
`importBrainShard` — the expensive embed pass is done once, here, and shipped.

**Rebuild / extend from source:**
```bash
npx tsx pipeline/ocw-capture.ts            # download + extract course substance
npx tsx pipeline/build-corpus.ts           # chunk + embed → vectors/  (OLLAMA_HOST=…)
bash    pipeline/ocw-grind.sh              # supervised full-catalog grind (keep zips, batch-archive)
```

## The learning loop (Alexandrian Academy)

1. **Capture** (`fetch-ocw.ts` / `ocw-capture.ts`) — pull courses, classify media by the
   OCW taxonomy, keep the full archives, extract substance.
2. **Vectorize** (`build-corpus.ts`) — chunk + embed → the brain here.
3. **Educate** (`educate.ts`) — read lectures + transcripts into the knowledge base.
4. **Study & grade** (`study.ts`, `cas_grade.py`) — attempt the problem sets; grade
   **T1-first** by *computing* the answer with a CAS (deterministic, replayable),
   falling back to an LLM judge only when a problem isn't reducible to a rule.
5. **Generate** (`gen_exam.py`) — emit unlimited clean parametric problems with computed
   answers (the "problems are templates" insight).
6. **Analyze** — `core_models.py` (the ~7 governing models per domain), `sindy_discover.py`
   (rediscover those laws from data), `mine_equations.py` (validate against the corpus).
7. **Benchmark** (`study-test.ts`, `mmlu-bench.ts`) — MMLU STEM, random-without-replacement.

## Provenance & license

Vectors and text excerpts are **derived from MIT OpenCourseWare**, licensed
**CC BY-NC-SA 4.0** (attribution · non-commercial · share-alike). Use of this derived
material must honor those terms. Source: <https://ocw.mit.edu>.
