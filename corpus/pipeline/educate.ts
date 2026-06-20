#!/usr/bin/env -S node --import tsx
/**
 * educate — take an MIT OCW course (a .zip or unpacked dir) the way a student does.
 * It CLASSIFIES every file by the OCW material taxonomy, reads the substance (PDF
 * lecture notes + the .vtt/.srt LECTURE TRANSCRIPTS — the professor's spoken teaching),
 * and skips the chrome (raw video, JS/CSS/HTML). Each ingested doc is tagged with its
 * material type so the learning loop can later: read the lectures, attempt the problem
 * sets, grade against the solutions, and sit the exams.
 *
 *   syllabus   → background / prerequisites (find a parity reference for what's assumed)
 *   lecture    → READ (notes + transcripts) — grounded into the basis
 *   assignment → ATTEMPT (problem sets)
 *   solution   → GRADE against (self-mark; wrong answers get crystallized as corrections)
 *   exam       → SIT (the real evaluation, not just MMLU)
 *
 * Usage:  npx tsx scripts/educate.ts <course.zip|dir> [courseTag]
 */
import * as fs from 'node:fs'
import * as os from 'node:os'
import * as path from 'node:path'
import { execFileSync } from 'node:child_process'
import { ingestDocument } from '../lib/doc-store.js'

const arg = process.argv[2]
const courseTag = process.argv[3] || (arg ? path.basename(arg).replace(/\.zip$/, '').slice(0, 24) : '')
if (!arg || !fs.existsSync(arg)) { console.error('usage: educate.ts <course.zip|dir> [courseTag]'); process.exit(1) }

type Material = 'syllabus' | 'lecture' | 'assignment' | 'solution' | 'exam' | 'recitation' | 'reference'

// Ground-truth OCW taxonomy → our learning-loop roles (from `learning_resource_types`).
const LRT: Record<string, Material> = {
  'Lecture Notes': 'lecture', 'Lecture Videos': 'lecture', 'Readings': 'lecture',
  'Problem-solving Videos': 'recitation', 'Recitation Notes': 'recitation', 'Recitation Videos': 'recitation',
  'Problem Sets': 'assignment', 'Assignments': 'assignment',
  'Problem Set Solutions': 'solution', 'Exam Solutions': 'solution',
  'Exams': 'exam', 'Supplemental Exam Materials': 'exam',
}

/** Build basename → Material from the OCW JSON metadata (the authoritative taxonomy).
 *  Each content node carries `file` (the hash-named resource) + `learning_resource_types`. */
function buildClassifier(root: string): Map<string, Material> {
  const m = new Map<string, Material>()
  for (const j of walk(root).filter((f) => f.endsWith('.json'))) {
    try {
      const d = JSON.parse(fs.readFileSync(j, 'utf8')) as { file?: string; learning_resource_types?: string[]; title?: string }
      const types = d.learning_resource_types
      if (!d.file || !types?.length) continue
      const mat = types.map((t) => LRT[t]).find(Boolean)
      if (mat) m.set(path.basename(d.file), mat)
    } catch { /* skip */ }
  }
  return m
}

function classify(file: string, byMeta: Map<string, Material>): Material {
  const meta = byMeta.get(path.basename(file)); if (meta) return meta   // authoritative
  const p = file.toLowerCase()                                          // fallback (path keywords)
  if (p.includes('syllabus')) return 'syllabus'
  if (p.includes('solution')) return 'solution'
  if (/exam|quiz|midterm|\bfinal\b/.test(p)) return 'exam'
  if (/problem-set|assignment|\bpset\b/.test(p)) return 'assignment'
  if (/recitation/.test(p)) return 'recitation'
  if (/lecture|unit-\d|notes|reading|session/.test(p)) return 'lecture'
  return 'reference'
}

/** Clean a WebVTT/SRT transcript to prose: drop WEBVTT, cue numbers, timestamp lines,
 *  the CC boilerplate, and de-dupe the wrapped lines into running text. */
function transcriptText(raw: string): string {
  const lines = raw.split(/\r?\n/)
  const out: string[] = []
  for (let l of lines) {
    l = l.trim()
    if (!l || l === 'WEBVTT' || l.includes('-->') || /^\d+$/.test(l)) continue
    out.push(l)
  }
  let t = out.join(' ').replace(/\s+/g, ' ')
  t = t.replace(/The following content is provided under a Creative Commons license\.[^.]*free\.?/i, '')
  return t.trim()
}

function pdfText(file: string): string {
  try {
    return execFileSync('python3', ['-c', "from pypdf import PdfReader;import sys;print('\\n'.join((p.extract_text() or '') for p in PdfReader(sys.argv[1]).pages))", file], { encoding: 'utf8', maxBuffer: 128 * 1024 * 1024 })
  } catch { return '' }
}

async function extract(file: string): Promise<string> {
  const ext = path.extname(file).toLowerCase()
  if (ext === '.pdf') return pdfText(file)
  if (ext === '.vtt' || ext === '.srt') return transcriptText(fs.readFileSync(file, 'utf8'))
  if (['.txt', '.md', '.tex'].includes(ext)) return fs.readFileSync(file, 'utf8')
  return ''
}

function walk(d: string): string[] {
  return fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)])
}

async function main() {
  // From a zip, extract ONLY content files (skip the 188MB of HTML/JS chrome + raw video).
  let root = arg
  let tmp = ''
  if (arg.endsWith('.zip')) {
    tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'educate-'))
    // .json = OCW metadata (the authoritative taxonomy); the rest is the substance.
    try { execFileSync('unzip', ['-o', '-qq', arg, '*.pdf', '*.vtt', '*.srt', '*.txt', '*.md', '*.tex', '*.json', '-d', tmp]) } catch { /* some patterns may match nothing */ }
    root = tmp
  }
  const byMeta = buildClassifier(root)
  const files = walk(root).filter((f) => ['.pdf', '.vtt', '.srt', '.txt', '.md', '.tex'].includes(path.extname(f).toLowerCase()))
  console.log(`# educating on ${courseTag} — ${files.length} content files · ${byMeta.size} metadata-classified (chrome + video skipped)\n`)

  const tally: Record<string, { docs: number; chunks: number; chars: number }> = {}
  for (const f of files) {
    const mat = classify(f, byMeta)
    const text = await extract(f)
    if (text.trim().length < 150) continue
    const name = `[${courseTag}/${mat}] ${path.basename(f)}`.slice(0, 90)
    try {
      const r = await ingestDocument(name, text)
      const t = (tally[mat] ??= { docs: 0, chunks: 0, chars: 0 })
      t.docs++; t.chunks += r.chunks; t.chars += text.length
    } catch { /* skip unreadable */ }
  }
  if (tmp) try { fs.rmSync(tmp, { recursive: true, force: true }) } catch { /* best-effort */ }

  console.log('# ingested by material type:')
  for (const m of ['syllabus', 'lecture', 'recitation', 'assignment', 'solution', 'exam', 'reference'] as Material[]) {
    const t = tally[m]; if (t) console.log(`  ${m.padEnd(11)} ${String(t.docs).padStart(3)} docs · ${String(t.chunks).padStart(4)} chunks · ${(t.chars / 1000 | 0)}k chars`)
  }
  const a = tally['assignment'], s = tally['solution'], e = tally['exam']
  console.log(`\n# the agent has READ ${courseTag}. ${a ? `${a.docs} assignments` : 'no assignments'} to attempt, ${s ? `${s.docs} solution sets` : 'no solutions'} to grade against, ${e ? `${e.docs} exams` : 'no exams'} to sit.`)
}
main().catch((e) => { console.error(e); process.exit(1) })
