#!/usr/bin/env -S node --import tsx
/**
 * build-corpus — vectorize the captured MIT corpus into a portable BRAIN artifact.
 *
 * The product edge: do the expensive part once, offline. We read every captured course's
 * substance (lecture text + transcripts + problems/solutions/exams), classify it by the
 * OCW taxonomy, chunk it, and EMBED every chunk (nomic-embed, 768-d). The output is a
 * set of per-subject shards of {metadata + vector} — a precomputed knowledge base that
 * can be *injected* into an agent wholesale (no re-reading, no re-embedding at load).
 * "We compute the vectors and give them to you as a brain injection."
 *
 * Vectors are stored base64-float32 (compact, exact, fast to decode). Resumable
 * (per-slug built-set), crash-safe (a course's lines are flushed atomically, then the
 * slug is marked built), tier-prioritized (STEM first). Re-run to continue; tracks the
 * capture as more courses land.
 *
 * Env:
 *   OCW_CORPUS  captured substance (default ~/Downloads/MIT OCW/_corpus)
 *   OCW_BRAIN   output brain dir (default /Volumes/LaCie/ocw-brain if mounted, else local _brain)
 *   BRAIN_CONCURRENCY  parallel embeds (default 4)
 *   OCW_MAX_TIER  highest tier to vectorize (default 4 = all)
 *
 * Usage:  npx tsx scripts/build-corpus.ts [--tier N] [--limit N]
 */
import * as fs from 'node:fs'
import * as os from 'node:os'
import * as path from 'node:path'
import { execFileSync } from 'node:child_process'
import { chunkText } from '../lib/doc-store.js'
import { embedText, EMBED_MODEL } from '../lib/ollama.js'

const HOME = os.homedir()
const CORPUS = process.env['OCW_CORPUS'] || path.join(HOME, 'Downloads', 'MIT OCW', '_corpus')
// LOCAL-FIRST: the brain builds on the fast local SSD, never the removable USB disk.
// A separate, single-writer archive sync (scripts/sync-archive.ts) mirrors it to LaCie.
// This is the robustness fix — heavy embedding writes can't wedge on a flaky USB mount.
const BRAIN = process.env['OCW_BRAIN'] || path.join(HOME, 'Downloads', 'MIT OCW', '_brain')
const CONC = Number(process.env['BRAIN_CONCURRENCY'] || 4)
const MAX_TIER = (() => { const i = process.argv.indexOf('--tier'); return i >= 0 ? Number(process.argv[i + 1]) : Number(process.env['OCW_MAX_TIER'] || 4) })()
const LIMIT = (() => { const i = process.argv.indexOf('--limit'); return i >= 0 ? Number(process.argv[i + 1]) : Infinity })()
const MANIFEST = path.join(BRAIN, '_manifest.json')

type Material = 'syllabus' | 'lecture' | 'recitation' | 'assignment' | 'solution' | 'exam' | 'reference'
const LRT: Record<string, Material> = {
  'Lecture Notes': 'lecture', 'Lecture Videos': 'lecture', 'Readings': 'lecture',
  'Problem-solving Videos': 'recitation', 'Recitation Notes': 'recitation', 'Recitation Videos': 'recitation',
  'Problem Sets': 'assignment', 'Assignments': 'assignment',
  'Problem Set Solutions': 'solution', 'Exam Solutions': 'solution',
  'Exams': 'exam', 'Supplemental Exam Materials': 'exam',
}
const FIELD: Record<string, string> = {
  '1': 'civil_enviro_eng', '2': 'mech_eng', '3': 'materials_sci', '4': 'architecture', '5': 'chemistry',
  '6': 'eecs', '7': 'biology', '8': 'physics', '9': 'brain_cog_sci', '10': 'chem_eng', '11': 'urban_studies',
  '12': 'earth_planetary', '14': 'economics', '15': 'management', '16': 'aero_astro', '17': 'political_sci',
  '18': 'mathematics', '20': 'biological_eng', '21': 'humanities', '22': 'nuclear_sci', '24': 'linguistics_philosophy',
  hst: 'health_sci_tech', sts: 'sci_tech_society', mas: 'media_arts', esd: 'eng_systems', res: 'supplemental',
}
const TIER: Record<string, number> = {
  '18': 1, '8': 1, '5': 1, '7': 1, '6': 1, '12': 1, '9': 1, '20': 1,
  '1': 2, '2': 2, '3': 2, '10': 2, '16': 2, '22': 2, hst: 2, esd: 2, mas: 2, '14': 3, '15': 3, '11': 3,
}
function dept(slug: string): string {
  const m = slug.match(/^(res|hst|sts|mas|esd|cms|wgs|ec|es|cc)\b/) || slug.match(/^(\d+)/)
  return m ? m[1]! : '?'
}
const tierOf = (s: string) => TIER[dept(s)] ?? 4
const fieldOf = (s: string) => FIELD[dept(s)] ?? 'other'
// Equation-dense depts (math, physics, chem, EECS, stats-prob via 18/6) vectorize FIRST
// within their tier — they carry the governing-model signal we validate the thesis on.
const DENSE = new Set(['18', '8', '5', '6', '16', '22'])
const denseRank = (s: string) => (DENSE.has(dept(s)) ? 0 : 1)
/** Course level (100=intro … 700+=grad) from the number after the dept, for curriculum order. */
function levelOf(slug: string): number {
  const m = slug.match(/^\d+[-.]?(\d{2,3})/); if (!m) return 0
  const n = Number(m[1]); return n < 100 ? n * 10 : n
}

function walk(d: string): string[] { return fs.existsSync(d) ? fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)]) : [] }

/** basename → Material from OCW JSON metadata (authoritative). */
function classifier(dir: string): Map<string, Material> {
  const m = new Map<string, Material>()
  for (const j of walk(dir).filter((f) => f.endsWith('.json'))) {
    try {
      const d = JSON.parse(fs.readFileSync(j, 'utf8')) as { file?: string; learning_resource_types?: string[] }
      const mat = d.learning_resource_types?.map((t) => LRT[t]).find(Boolean)
      if (d.file && mat) m.set(path.basename(d.file), mat)
    } catch { /* */ }
  }
  return m
}
function classify(file: string, byMeta: Map<string, Material>): Material {
  const meta = byMeta.get(path.basename(file)); if (meta) return meta
  const p = file.toLowerCase()
  if (p.includes('syllabus')) return 'syllabus'
  if (/sol\b|solution/.test(p)) return 'solution'
  if (/exam|quiz|midterm|\bfinal\b/.test(p)) return 'exam'
  if (/prb|problem-set|assignment|\bpset\b/.test(p)) return 'assignment'
  if (/recitation/.test(p)) return 'recitation'
  if (/lecture|notes|reading|session|chapter|unit/.test(p)) return 'lecture'
  return 'reference'
}

function pdfText(file: string): string {
  try { return execFileSync('python3', ['-c', "from pypdf import PdfReader;import sys;print('\\n'.join((p.extract_text() or '') for p in PdfReader(sys.argv[1]).pages))", file], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 }) } catch { return '' }
}
function transcriptText(raw: string): string {
  const out: string[] = []
  for (let l of raw.split(/\r?\n/)) { l = l.trim(); if (!l || l === 'WEBVTT' || l.includes('-->') || /^\d+$/.test(l)) continue; out.push(l) }
  return out.join(' ').replace(/\s+/g, ' ').replace(/The following content is provided under a Creative Commons license\.[^.]*free\.?/i, '').trim()
}
function extract(file: string): string {
  const ext = path.extname(file).toLowerCase()
  if (ext === '.pdf') return pdfText(file)
  if (ext === '.vtt' || ext === '.srt') return transcriptText(fs.readFileSync(file, 'utf8'))
  if (['.txt', '.md', '.tex'].includes(ext)) return fs.readFileSync(file, 'utf8')
  return ''
}
const b64vec = (v: number[]) => Buffer.from(Float32Array.from(v).buffer).toString('base64')

async function mapPool<T, R>(items: T[], n: number, fn: (t: T) => Promise<R>): Promise<R[]> {
  const out: R[] = new Array(items.length); let i = 0
  await Promise.all(Array.from({ length: Math.min(n, items.length) }, async () => {
    while (i < items.length) { const k = i++; out[k] = await fn(items[k]!) }
  }))
  return out
}

/** Done-set = courses that already have a per-course brain file. No ledger to corrupt;
 *  a file's mere existence (written atomically via temp→rename) means it completed. */
function loadBuilt(): Set<string> {
  const s = new Set<string>()
  try {
    for (const field of fs.readdirSync(BRAIN)) {
      const fd = path.join(BRAIN, field)
      try { if (!fs.statSync(fd).isDirectory()) continue } catch { continue }
      for (const f of fs.readdirSync(fd)) if (f.endsWith('.jsonl')) s.add(f.replace(/\.jsonl$/, ''))
    }
  } catch { /* fresh */ }
  return s
}

async function main() {
  fs.mkdirSync(BRAIN, { recursive: true })
  const built = loadBuilt()
  const slugs = fs.readdirSync(CORPUS, { withFileTypes: true }).filter((e) => e.isDirectory()).map((e) => e.name)
    .filter((s) => tierOf(s) <= MAX_TIER && !built.has(s)).sort((a, b) => tierOf(a) - tierOf(b) || denseRank(a) - denseRank(b) || a.localeCompare(b))
  console.log(`# build-corpus → BRAIN=${BRAIN}`)
  console.log(`# ${built.size} courses already vectorized · ${slugs.length} to do (tier ≤ ${MAX_TIER}) · embed=${EMBED_MODEL} conc=${CONC}\n`)

  let done = 0, totalChunks = 0
  for (const slug of slugs) {
    if (done >= LIMIT) break
    const dir = path.join(CORPUS, slug)
    const byMeta = classifier(dir)
    const field = fieldOf(slug), level = levelOf(slug), tier = tierOf(slug)
    const files = walk(dir).filter((f) => ['.pdf', '.vtt', '.srt', '.txt', '.md', '.tex'].includes(path.extname(f).toLowerCase()))
    const lines: string[] = []
    const tally: Record<string, number> = {}
    for (const f of files) {
      const material = classify(f, byMeta)
      const text = extract(f)
      if (text.trim().length < 120) continue
      const chunks = chunkText(text)
      const vecs = await mapPool(chunks, CONC, (c) => embedText(c).catch(() => [] as number[]))
      chunks.forEach((c, ci) => {
        const v = vecs[ci]; if (!v || v.length === 0) return
        lines.push(JSON.stringify({ slug, field, tier, level, material, file: path.basename(f), ci, text: c, dims: v.length, vec: b64vec(v) }))
        tally[material] = (tally[material] || 0) + 1
      })
    }
    // ATOMIC per-course write: temp file → rename. An unplug/crash mid-write leaves only
    // a stray .tmp (ignored); the real file appears only once fully written. No shared
    // shard to truncate, no ledger to desync. A course with 0 vectors is left undone (retry).
    if (lines.length) {
      const outDir = path.join(BRAIN, field)
      const out = path.join(outDir, `${slug}.jsonl`), tmp = `${out}.tmp`
      try {
        fs.mkdirSync(outDir, { recursive: true })
        fs.writeFileSync(tmp, lines.join('\n') + '\n')
        fs.renameSync(tmp, out)
      } catch (e) { console.error(`  ! write failed for ${slug} (disk gone?) — will retry next run`); break }
      done++; totalChunks += lines.length
      const t = Object.entries(tally).map(([k, n]) => `${k}:${n}`).join(' ') || '(none)'
      console.log(`  ✓ T${tier} ${slug} → ${field} · ${lines.length} vectors [${t}]`)
    }
  }
  // refresh manifest (count per-course files per field)
  const shards: Record<string, number> = {}
  try {
    for (const field of fs.readdirSync(BRAIN)) {
      const fd = path.join(BRAIN, field)
      try { if (!fs.statSync(fd).isDirectory()) continue } catch { continue }
      shards[field] = fs.readdirSync(fd).filter((f) => f.endsWith('.jsonl')).length
    }
  } catch { /* */ }
  fs.writeFileSync(MANIFEST, JSON.stringify({ embed_model: EMBED_MODEL, dims: 768, courses_built: loadBuilt().size, courses_by_field: shards, updated: new Date().toISOString() }, null, 2))
  console.log(`\n# vectorized ${done} courses this run (${totalChunks} chunks). Brain: ${loadBuilt().size} courses total (local). Re-run to continue.`)
}
main().catch((e) => { console.error(e); process.exit(1) })
