#!/usr/bin/env -S node --import tsx
/**
 * study — the Alexandrian Academy learning loop. After `educate` has READ a course's
 * lectures into the basis, `study` does what a student does next: ATTEMPT the work,
 * GRADE against the official solutions, and write the ERRORS back into the knowledge
 * base explicitly — so the agent that gets a problem wrong today RECALLS the correction
 * tomorrow (the decidable region expands by exactly the problems it missed).
 *
 *   1. PAIR    each assignment/exam with its official solution (OCW title metadata).
 *   2. ATTEMPT each problem, grounded in the lectures already ingested (open-book, the
 *      way the read-covector tier is supposed to work — retrieve before you generate).
 *   3. GRADE   T1-FIRST: compute the canonical answer with a CAS (cas_grade.py) and
 *      check the student's final for symbolic/numeric equivalence — deterministic and
 *      replayable. Only problems not reducible to a rule (proofs, "explain") fall back
 *      to the T2 LLM-as-judge against the official solution text.
 *   4. CRYSTALLIZE every wrong answer as an attested Correction atom: question = the
 *      problem, answer = the official method. High STI ⇒ the next encounter recalls it.
 *
 * Claim-mode (§1.8): T1-graded problems are a computed measurement (replayable); T2
 * ones are an estimate (local-model judge), and each verdict is tagged with its tier.
 * The write-back is T1 — each correction is a hash-chained dispatch that replays.
 *
 * Usage:  npx tsx scripts/study.ts <course.zip|dir> <courseTag> [--exams-only] [--limit N]
 */
import * as fs from 'node:fs'
import * as os from 'node:os'
import * as path from 'node:path'
import { execFileSync } from 'node:child_process'

// Resolve sibling scripts (cas_grade.py) relative to this file, regardless of cwd.
const SCRIPT_DIR = path.dirname(process.argv[1] || path.join(process.cwd(), 'scripts', 'study.ts'))
import { generateOllamaText } from '../lib/ollama.js'
import { lexicalSearch, semanticSearch } from '../lib/doc-store.js'
import { crystallizeAnswer } from '../lib/crystallize.js'
import { recordDispatch, contentHash } from '../lib/dispatch-ledger.js'

const arg = process.argv[2]
const courseTag = process.argv[3] || (arg ? path.basename(arg).replace(/\.zip$/, '').slice(0, 24) : '')
const EXAMS_ONLY = process.argv.includes('--exams-only')
const LIMIT = (() => { const i = process.argv.indexOf('--limit'); return i >= 0 ? Number(process.argv[i + 1]) : Infinity })()
// Default to the light 3B for attempts — on an 8GB box the 7B-cpu thrashes/OOMs the
// box. Override with NOETICA_STUDY_MODEL=qwen2.5:7b for higher-quality attempts in
// small batches. Grading quality does NOT depend on this: the T1 path computes the
// answer with a CAS regardless of how the student model did.
const MODEL = process.env['NOETICA_STUDY_MODEL'] ?? 'llama3.2:3b'
if (!arg || !fs.existsSync(arg)) { console.error('usage: study.ts <course.zip|dir> <courseTag> [--exams-only] [--limit N]'); process.exit(1) }

type Role = 'assignment' | 'solution' | 'exam' | 'examsol'

// OCW lumps problems with their solutions under the same `learning_resource_type`; the
// real signal is the FILENAME convention — `_prb`/`examN` vs `_sol`/`examNsol`. We pair
// on the shared STEM (the name with the prb/sol suffix and course prefix stripped).
const LRT = new Set(['Problem Sets', 'Assignments', 'Exams', 'Supplemental Exam Materials', 'Problem Set Solutions', 'Exam Solutions'])

/** Pairing key: strip course prefix, prb/sol suffix, "solutions", → bare stem.
 *  exam1.pdf & exam1sol.pdf → "exam1";  ex81prb & ex81sol → "ex81";  Final Exam[ Solutions] → "final exam". */
function stemKey(title: string): string {
  return title.toLowerCase()
    .replace(/\.pdf$/, '')
    .replace(/mit_?18[_.]?01sc(?:f10)?_?|18\.01sc/g, '')
    .replace(/solutions?|answers?/g, '')
    .replace(/(prb|sol)$/, '')
    .replace(/[^a-z0-9]+/g, ' ').trim()
}

/** Role from the filename convention (sol-suffix / "solutions" ⇒ answer side). */
function roleOf(title: string): Role | null {
  const s = title.toLowerCase()
  const isExam = /exam/.test(s) && !/example/.test(s)
  if (/sol\.pdf$/.test(s) || /solutions?/.test(s)) return isExam ? 'examsol' : 'solution'
  if (/prb\.pdf$/.test(s) || /\bpset\d/.test(s)) return 'assignment'
  if (/exam\d?\.pdf$/.test(s) || /final exam$/.test(s)) return 'exam'
  return null
}

interface Doc { file: string; role: Role; title: string; key: string }

/** Read OCW JSON metadata → gradeable docs (problems + solutions), keyed for pairing. */
function gradeables(root: string): Doc[] {
  const out: Doc[] = []
  for (const j of walk(root).filter((f) => f.endsWith('.json'))) {
    try {
      const d = JSON.parse(fs.readFileSync(j, 'utf8')) as { file?: string; learning_resource_types?: string[]; title?: string }
      if (!d.file || !d.title) continue
      if (d.learning_resource_types && !d.learning_resource_types.some((t) => LRT.has(t))) continue
      const role = roleOf(d.title)
      if (!role) continue
      out.push({ file: path.basename(d.file), role, title: d.title, key: stemKey(d.title) })
    } catch { /* skip */ }
  }
  return out
}

/** Pair each problem doc with the solution doc sharing its stem key. */
function pairs(docs: Doc[]): { problem: Doc; solution: Doc | null }[] {
  const sols = docs.filter((d) => d.role === 'solution' || d.role === 'examsol')
  const probs = docs.filter((d) => d.role === 'assignment' || d.role === 'exam')
  return probs
    .filter((p) => !EXAMS_ONLY || p.role === 'exam')
    .map((problem) => {
      const want: Role = problem.role === 'exam' ? 'examsol' : 'solution'
      const solution = sols.find((s) => s.role === want && s.key === problem.key)
        ?? sols.find((s) => s.role === want && (s.key.includes(problem.key) || problem.key.includes(s.key))) ?? null
      return { problem, solution }
    })
}

function pdfText(file: string): string {
  try {
    return execFileSync('python3', ['-c', "from pypdf import PdfReader;import sys;print('\\n'.join((p.extract_text() or '') for p in PdfReader(sys.argv[1]).pages))", file], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 })
  } catch { return '' }
}

/** Split a problem-set PDF into individual problems on common MIT markers. */
function splitProblems(text: string): string[] {
  const parts = text.split(/\n(?=\s*(?:Problem|Exercise|Question)\s+\d+|\s*\d{1,2}[.)]\s)/i)
    .map((s) => s.trim()).filter((s) => s.length > 40)
  return parts.length > 1 ? parts : (text.trim().length > 40 ? [text.trim()] : [])
}

function locate(root: string, basename: string): string | null {
  return walk(root).find((f) => path.basename(f) === basename) ?? null
}

function walk(d: string): string[] {
  return fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)])
}

/** Generate with resilience: the 7B-cpu runner can drop under memory pressure on a
 *  small box. Retry with backoff so a transient drop doesn't abort a long study run. */
async function gen(messages: Array<{ role: string; content: string }>, temperature: number): Promise<string> {
  let lastErr: unknown
  for (let i = 0; i < 4; i++) {
    try {
      const { content } = await generateOllamaText({ model: MODEL, temperature, numCtx: 4096, messages })
      if (content.trim()) return content.trim()
    } catch (e) { lastErr = e }
    await new Promise((r) => setTimeout(r, 4000 * (i + 1))) // let the runner reload
  }
  throw lastErr ?? new Error('empty generation after retries')
}

/** Open-book attempt: retrieve lecture context already in the KB, then solve. */
async function attempt(problem: string): Promise<string> {
  let context = ''
  try {
    const hits = await semanticSearch(problem.slice(0, 300), 4).catch(() => lexicalSearch(problem.slice(0, 300), 4))
    context = hits.map((h, i) => `[${i + 1}] ${h.text.slice(0, 500)}`).join('\n')
  } catch { /* closed-book fallback */ }
  return gen([
    { role: 'system', content: `You are a student sitting an MIT exam. Solve the problem step by step using the lecture notes provided. Be concise. End with a single line "FINAL: <your answer>".` },
    { role: 'user', content: `Lecture notes:\n${context || '(none retrieved)'}\n\nProblem:\n${problem.slice(0, 2000)}` },
  ], 0.2)
}

/** DETERMINISTIC grade (T1): compute the canonical answer with a CAS and check the
 *  student's final for symbolic/numeric equivalence. Returns null when the problem
 *  isn't reducible to a rule (caller falls back to the T2 judge). Replayable. */
function gradeDeterministic(problem: string, studentAns: string): { correct: boolean; why: string } | null {
  try {
    const out = execFileSync('python3', [path.join(SCRIPT_DIR, 'cas_grade.py')], {
      input: JSON.stringify({ problem, student: studentAns }), encoding: 'utf8', timeout: 20_000,
    })
    const r = JSON.parse(out) as { gradeable: boolean; correct?: boolean; type: string; canonical: string | null }
    if (!r.gradeable) return null
    return { correct: !!r.correct, why: `[T1 ${r.type}] computed ${r.canonical}` }
  } catch { return null }
}

/** LLM-as-judge grade against the official solution (T2 fallback). */
async function grade(problem: string, studentAns: string, officialSol: string): Promise<{ correct: boolean; why: string }> {
  const verdict = await gen([
    { role: 'system', content: `You are a strict TA. Compare the STUDENT answer to the OFFICIAL solution. Did the student reach the same final result/method? Reply exactly "CORRECT: <reason>" or "WRONG: <reason>" in one line.` },
    { role: 'user', content: `PROBLEM:\n${problem.slice(0, 1200)}\n\nSTUDENT:\n${studentAns.slice(0, 1200)}\n\nOFFICIAL SOLUTION:\n${officialSol.slice(0, 1800)}` },
  ], 0)
  return { correct: /^correct/i.test(verdict), why: verdict.replace(/^(correct|wrong)\s*:?\s*/i, '').slice(0, 160) }
}

async function main() {
  let root = arg, tmp = ''
  if (arg.endsWith('.zip')) {
    tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'study-'))
    try { execFileSync('unzip', ['-o', '-qq', arg, '*.pdf', '*.json', '-d', tmp]) } catch { /* */ }
    root = tmp
  }
  const docs = gradeables(root)
  const ps = pairs(docs)
  const withSol = ps.filter((p) => p.solution)
  console.log(`# studying ${courseTag} — ${ps.length} problem docs, ${withSol.length} with official solutions${EXAMS_ONLY ? ' (exams only)' : ''}\n`)

  let n = 0, correct = 0, written = 0, t1 = 0, t2 = 0
  for (const { problem, solution } of withSol) {
    if (n >= LIMIT) break
    const pf = locate(root, problem.file), sf = solution ? locate(root, solution.file) : null
    if (!pf || !sf) continue
    const probText = pdfText(pf), solText = pdfText(sf)
    const problems = splitProblems(probText)
    console.log(`\n## ${problem.title} — ${problems.length} problem(s) [sol: ${solution!.title}]`)
    for (const prob of problems) {
      if (n >= LIMIT) break
      n++
      const t0 = Date.now()
      const ans = await attempt(prob)
      // T1 FIRST: compute the answer (deterministic, replayable). T2 judge only if not reducible.
      const det = gradeDeterministic(prob, ans)
      const { correct: ok, why } = det ?? await grade(prob, ans, solText)
      if (det) t1++; else t2++
      const latencyMs = Date.now() - t0
      const head = prob.replace(/\s+/g, ' ').slice(0, 64)
      console.log(`  ${ok ? '✓' : '✗'} [${det ? 'T1' : 'T2'}] ${head}…  ${ok ? '' : '→ ' + why}`)
      if (ok) { correct++; continue }

      // WRITE-BACK: the error becomes attested, recallable knowledge (Alexandrian Academy).
      const q = `[${courseTag}] ${head}`
      const ledger = recordDispatch({
        session: `study:${courseTag}`, requestHash: contentHash(prob.slice(0, 500)),
        action: 'transform', polarity: 'write', tier: 'deliberate', target: 'study', phase: 'crystallize',
        barCleared: true, residual: [], model: MODEL,
        answerHash: contentHash(solText.slice(0, 500)), latencyMs, grounded: true, verdict: 'POS',
      })
      const art = crystallizeAnswer({
        question: q, answer: `Correct approach (from official solution):\n${solText.slice(0, 1500)}`,
        session: `study:${courseTag}`, action: 'transform', attestation: ledger.attestation, worth: 0.9,
      })
      if (art) written++
    }
  }
  if (tmp) try { fs.rmSync(tmp, { recursive: true, force: true }) } catch { /* */ }

  const pct = n ? (100 * correct / n).toFixed(1) : '0'
  const t1pct = n ? (100 * t1 / n).toFixed(0) : '0'
  console.log(`\n# ${courseTag}: ${correct}/${n} correct (${pct}%) · ${written} corrections crystallized into the KB.`)
  console.log(`# grading: ${t1}/${n} deterministic (T1, ${t1pct}% — computed + replayable), ${t2}/${n} LLM-judge (T2).`)
  console.log(`# every correction is an attested dispatch (replayable). Re-running will RECALL them.`)
}
main().catch((e) => { console.error(e); process.exit(1) })
