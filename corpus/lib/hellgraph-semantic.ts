/**
 * semantic — the vectorization pipeline, native to HellGraph.
 *
 * HellGraph already stores DocumentChunk atoms and embeds *entities* for merge
 * similarity; this module makes the FULL vector pipeline first-class so any consumer
 * (Noetica, the platform) gets it from the graph itself rather than re-implementing it:
 *
 *   chunk → embed → store vectors ON chunk atoms → cosine semantic search
 *   + brain IMPORT/EXPORT — load/dump PRECOMPUTED vectors (base64-float32) so the
 *     expensive embed pass is done once offline and injected as a portable "brain".
 *
 * Embed-agnostic: every embedding op takes an optional EmbedFn; the default calls a
 * local Ollama (OLLAMA_HOST / nomic-embed-text), matching the rest of HellGraph, but
 * callers can inject any embedder. Vector storage/import/export need no embedder at all.
 */
import * as fs from 'node:fs'
import { getHellGraph } from './store'

export type EmbedFn = (text: string) => Promise<number[]>

const OLLAMA_BASE = process.env['OLLAMA_HOST'] ?? 'http://127.0.0.1:11434'
const EMBED_MODEL = process.env['HELLGRAPH_EMBED_MODEL'] ?? 'nomic-embed-text'
const CHUNK_LABEL = 'DocumentChunk'
const CHUNK_SIZE = 1500
const CHUNK_OVERLAP = 200

/** Default embedder — local Ollama. Returns [] on failure so callers degrade gracefully. */
export async function embedText(text: string, opts: { base?: string; model?: string } = {}): Promise<number[]> {
  try {
    const res = await fetch(`${opts.base ?? OLLAMA_BASE}/api/embeddings`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ model: opts.model ?? EMBED_MODEL, prompt: text.slice(0, 8000) }),
      signal: AbortSignal.timeout(15_000),
    })
    if (!res.ok) return []
    const j = (await res.json()) as { embedding?: number[] }
    return j.embedding ?? []
  } catch {
    return []
  }
}

export function cosineSim(a: number[], b: number[]): number {
  let dot = 0, na = 0, nb = 0
  const n = Math.min(a.length, b.length)
  for (let i = 0; i < n; i++) { const x = a[i] ?? 0, y = b[i] ?? 0; dot += x * y; na += x * x; nb += y * y }
  return na > 0 && nb > 0 ? dot / (Math.sqrt(na) * Math.sqrt(nb)) : 0
}

/** Sliding-window chunker (chars), matching HellGraph's document ingest. */
export function chunkText(text: string, size = CHUNK_SIZE, overlap = CHUNK_OVERLAP): string[] {
  const chunks: string[] = []
  let start = 0
  while (start < text.length) {
    const end = Math.min(start + size, text.length)
    chunks.push(text.slice(start, end))
    if (end === text.length) break
    start = end - overlap
  }
  return chunks
}

// base64 ↔ Float32 vector (the compact, exact brain wire format)
export function encodeVec(v: number[]): string { return Buffer.from(Float32Array.from(v).buffer).toString('base64') }
export function decodeVec(b64: string): number[] {
  const buf = Buffer.from(b64, 'base64')
  return Array.from(new Float32Array(buf.buffer, buf.byteOffset, Math.floor(buf.byteLength / 4)))
}

/** Store one chunk atom carrying its text + vector (the unit the search reads).
 *  Canonical shape — matches the property names every consumer already reads
 *  (`text`/`embedding`/`doc_id`/`filename`/`chunk_index`), so there is ONE chunk
 *  representation across HellGraph and its consumers. Idempotent per (docId, idx). */
export function putChunk(o: { docId: string; idx: number; text: string; vec: number[]; filename: string; meta?: Record<string, string | number> }): void {
  const g = getHellGraph()
  g.addNode(`${o.docId}:chunk:${o.idx}`, [CHUNK_LABEL], {
    text: o.text,
    embedding: o.vec.length ? JSON.stringify(o.vec) : '',
    doc_id: o.docId,
    filename: o.filename,
    chunk_index: o.idx,
    created_at: new Date().toISOString(),
    ...(o.meta ?? {}),
  })
}

export interface VectorizeResult { docId: string; chunks: number; embedded: number }

/** Chunk → embed → store. The online path (embeds now). */
export async function vectorizeDocument(content: string, filename: string, embed: EmbedFn = embedText): Promise<VectorizeResult> {
  const g = getHellGraph()
  const docId = `urn:hellgraph:doc:${filename.replace(/[^a-z0-9]/gi, '-').toLowerCase()}-${Date.now()}`
  g.addNode(docId, ['RECORD', 'Document'], { filename, charCount: content.length, createdAt: new Date().toISOString() })
  const chunks = chunkText(content)
  let embedded = 0
  for (let i = 0; i < chunks.length; i++) {
    const vec = await embed(chunks[i]!)
    if (vec.length) embedded++
    putChunk({ docId, idx: i, text: chunks[i]!, vec, filename })
    g.addEdge('HAS_CHUNK', docId, `${docId}:chunk:${i}`, { chunkIndex: i, createdAt: new Date().toISOString() })
  }
  return { docId, chunks: chunks.length, embedded }
}

export interface ChunkHit { text: string; filename: string; score: number; docId: string }

/** Top-k chunks by cosine to the query embedding (lexical fallback for un-embedded
 *  chunks). `opts.scope` pins retrieval to chunks whose filename contains the substring
 *  — the non-destructive way to focus a polluted store (Noetica's NOETICA_DEMO_DOC). */
export async function semanticSearch(query: string, k = 5, embed: EmbedFn = embedText, opts: { scope?: string } = {}): Promise<ChunkHit[]> {
  const g = getHellGraph()
  let nodes = g.nodesByLabel(CHUNK_LABEL)
  if (opts.scope) {
    const f = nodes.filter((n) => String(n.properties['filename'] ?? '').toLowerCase().includes(opts.scope!.toLowerCase()))
    if (f.length > 0) nodes = f
  }
  if (nodes.length === 0) return []
  const qvec = await embed(query)
  const qTokens = new Set(query.toLowerCase().split(/\W+/).filter((t) => t.length > 2))
  const scored: ChunkHit[] = []
  for (const n of nodes) {
    const text = String(n.properties['text'] ?? n.properties['content'] ?? '')
    if (!text) continue
    const raw = String(n.properties['embedding'] ?? '')
    let score = 0
    if (raw && qvec.length) { try { score = cosineSim(qvec, JSON.parse(raw) as number[]) } catch { /* */ } }
    if (score === 0) {
      const cTokens = new Set(text.toLowerCase().split(/\W+/).filter((t) => t.length > 2))
      let overlap = 0
      for (const t of qTokens) if (cTokens.has(t)) overlap++
      score = qTokens.size ? (overlap / qTokens.size) * 0.5 : 0
    }
    scored.push({ text, filename: String(n.properties['filename'] ?? ''), score, docId: String(n.properties['doc_id'] ?? '') })
  }
  return scored.sort((a, b) => b.score - a.score).slice(0, k).filter((h) => h.score > 0.05)
}

/** Count of chunk atoms currently carrying a vector. */
export function vectorChunkCount(): number {
  return getHellGraph().nodesByLabel(CHUNK_LABEL).filter((n) => String(n.properties['embedding'] ?? '')).length
}

export interface BrainRow { slug?: string; field?: string; material?: string; level?: number; file?: string; ci?: number; text: string; vec: string }
export interface ImportResult { chunks: number; docs: number; skipped: number }

/**
 * Brain IMPORT — load a JSONL shard of PRECOMPUTED vectors (base64-float32) straight
 * into the atomspace as chunk atoms. No re-embedding: the offline embed pass is the
 * brain; this injects it. Idempotent per (docId, idx). The product edge, in the graph.
 */
export function importBrainShard(jsonl: string, opts: { limit?: number } = {}): ImportResult {
  // node-only deps, required lazily so the module loads in any bundler target
  const g = getHellGraph()
  const limit = opts.limit ?? Infinity
  let chunks = 0, skipped = 0
  const docs = new Set<string>()
  const lines = fs.readFileSync(jsonl, 'utf8').split('\n')
  for (const line of lines) {
    if (!line.trim() || chunks >= limit) continue
    let r: BrainRow
    try { r = JSON.parse(line) as BrainRow } catch { continue }
    if (!r.vec || !r.text) continue
    const docId = `urn:hellgraph:brain:${r.slug ?? 'shard'}:${r.file ?? 'doc'}`
    const idx = r.ci ?? chunks
    if (g.getNode(`${docId}:chunk:${idx}`)) { skipped++; continue }
    const meta: Record<string, string | number> = {}
    if (r.field) meta['field'] = r.field
    if (r.material) meta['material'] = r.material
    if (r.level != null) meta['level'] = r.level
    putChunk({ docId, idx, text: r.text, vec: decodeVec(r.vec), filename: `[${r.field ?? ''}/${r.material ?? ''}] ${r.slug ?? ''}`.trim(), meta })
    docs.add(docId); chunks++
  }
  return { chunks, docs: docs.size, skipped }
}

/** Brain EXPORT — dump chunk atoms (optionally filtered) to a JSONL shard. */
export function exportBrainShard(outPath: string, filter?: (n: { properties: Record<string, unknown> }) => boolean): number {
  const g = getHellGraph()
  const out: string[] = []
  for (const n of g.nodesByLabel(CHUNK_LABEL)) {
    if (filter && !filter(n)) continue
    const raw = String(n.properties['embedding'] ?? '')
    if (!raw) continue
    let vec: number[]
    try { vec = JSON.parse(raw) as number[] } catch { continue }
    out.push(JSON.stringify({
      slug: String(n.properties['filename'] ?? ''),
      field: n.properties['field'] ?? '', material: n.properties['material'] ?? '',
      file: String(n.properties['filename'] ?? ''), ci: Number(n.properties['chunk_index'] ?? n.properties['chunkIndex'] ?? 0),
      text: String(n.properties['text'] ?? n.properties['content'] ?? ''), dims: vec.length, vec: encodeVec(vec),
    }))
  }
  fs.writeFileSync(outPath, out.join('\n') + '\n')
  return out.length
}
