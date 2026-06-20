#!/usr/bin/env -S node --import tsx
/**
 * study-test — sit the MMLU STEM exam ONE QUESTION AT A TIME, drawn at RANDOM WITHOUT
 * REPLACEMENT from the pooled bank, scoring incrementally so a live signal appears
 * immediately and partial results survive a crash (each answer is appended to a
 * transcript before the next draw). No need to wait for a full sweep.
 *
 * Cascade (crash-safe on an 8GB box): attempt with the fast 3B; if it won't commit to a
 * clean answer, ESCALATE to the 7B for that question only. We escalate on UNCERTAINTY
 * (unparseable / uncommitted), never on known-wrongness — peeking at the label to pick a
 * second model would inflate accuracy. Each question records which model answered.
 *
 * Env:
 *   STUDY_N       questions to draw (default 40; 0 = whole bank, shuffled)
 *   STUDY_SEED    RNG seed (default: time-based → fresh draw each run)
 *   BASE          ollama base (default http://127.0.0.1:11434 — the reliable runner)
 *   FAST_MODEL    default llama3.2:3b   · STRONG_MODEL default qwen2.5:7b
 *   STUDY_TIMEOUT_MS per-call timeout (default 120000)
 *
 * Usage:  npx tsx scripts/study-test.ts            # 40 random questions, live
 *         STUDY_N=0 npx tsx scripts/study-test.ts  # the whole bank, shuffled
 */
import * as fs from 'node:fs'
import * as os from 'node:os'
import * as path from 'node:path'

const BANK = path.join(os.homedir(), '.noetica', 'corpus', 'benchmarks')
const BASE = (process.env['BASE'] || 'http://127.0.0.1:11434').replace(/\/$/, '')
const FAST = process.env['FAST_MODEL'] || 'llama3.2:3b'
const STRONG = process.env['STRONG_MODEL'] || 'qwen2.5:7b'
const N = Number(process.env['STUDY_N'] ?? 40)
const SEED = Number(process.env['STUDY_SEED'] ?? (Date.now() % 2147483647))
const TIMEOUT = Number(process.env['STUDY_TIMEOUT_MS'] || 120_000)
const LETTERS = ['A', 'B', 'C', 'D']
const TRANSCRIPT = path.join(os.homedir(), '.noetica', `studytest-${Date.now()}.jsonl`)

// Published frontier MMLU (overall) for reference — not per-subject claims.
const FRONTIER = { 'Qwen2.5-7B (reported)': 74.2, 'Llama-3.2-3B (reported)': 63.4, 'GPT-4': 86.4, 'Claude 3.5 Sonnet': 88.7 }

interface Q { subject: string; question: string; choices: string[]; answer: number }

// Mulberry32 — small seeded PRNG for a reproducible shuffle.
function rng(seed: number): () => number {
  let a = seed >>> 0
  return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296 }
}
function shuffle<T>(arr: T[], rand: () => number): T[] {
  const a = arr.slice()
  for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [a[i], a[j]] = [a[j]!, a[i]!] }
  return a
}

async function ask(model: string, prompt: string): Promise<string> {
  const sys = 'You are taking a multiple-choice exam. Reason in ONE short sentence, then end with a line "FINAL: X" where X is exactly one of A, B, C, or D.'
  try {
    const res = await fetch(`${BASE}/v1/chat/completions`, {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ model, stream: false, messages: [{ role: 'system', content: sys }, { role: 'user', content: prompt }], temperature: 0 }),
      signal: AbortSignal.timeout(TIMEOUT),
    })
    const d = await res.json() as { choices?: Array<{ message?: { content?: string; reasoning_content?: string } }> }
    const m = d.choices?.[0]?.message
    return (m?.content || m?.reasoning_content || '').trim()
  } catch { return '' }
}
function extractLetter(raw: string): string {
  const f = /FINAL:\s*\(?([A-D])\)?/i.exec(raw); if (f) return f[1]!.toUpperCase()
  const m = /\b([A-D])\b(?![\s\S]*\b[A-D]\b)/.exec(raw.trim()); return m ? m[1]!.toUpperCase() : ''
}

function pct(a: number, b: number): string { return b ? (100 * a / b).toFixed(1) : '0.0' }

async function main() {
  const mmlu = JSON.parse(fs.readFileSync(path.join(BANK, 'mmlu_stem.json'), 'utf8')) as Record<string, Q[]>
  const pool: Q[] = []
  for (const [subject, items] of Object.entries(mmlu)) for (const it of items) pool.push({ ...it, subject })
  const rand = rng(SEED)
  const order = shuffle(pool, rand)
  const draw = N > 0 ? order.slice(0, N) : order

  console.log(`# MMLU STEM — random without replacement | seed=${SEED} | drawing ${draw.length}/${pool.length}`)
  console.log(`# cascade: ${FAST} → escalate ${STRONG} on uncertainty | base=${BASE}`)
  console.log(`# transcript: ${TRANSCRIPT}\n`)

  let correct = 0, escalated = 0, strongCorrect = 0, fastCorrect = 0, fastTotal = 0, strongTotal = 0, msTotal = 0
  const bySub: Record<string, { c: number; n: number }> = {}

  process.on('SIGINT', () => { summary(); process.exit(0) })
  function summary() {
    console.log(`\n# ── results (${correct}/${msN()} = ${pct(correct, msN())}%) ──`)
    const subs = Object.entries(bySub).sort((a, b) => a[0].localeCompare(b[0]))
    for (const [s, v] of subs) console.log(`  ${s.padEnd(28)} ${v.c}/${v.n}  (${pct(v.c, v.n)}%)`)
    console.log(`\n  fast ${FAST}: ${fastCorrect}/${fastTotal} (${pct(fastCorrect, fastTotal)}%) · escalated to ${STRONG}: ${escalated} (${strongCorrect}/${strongTotal} = ${pct(strongCorrect, strongTotal)}%)`)
    console.log(`  mean latency: ${(msTotal / Math.max(1, msN()) / 1000).toFixed(1)}s/q`)
    console.log(`\n# reference (published overall MMLU):`)
    for (const [k, v] of Object.entries(FRONTIER)) console.log(`  ${k.padEnd(26)} ${v}%`)
  }
  let answered = 0
  function msN() { return answered }

  for (let i = 0; i < draw.length; i++) {
    const q = draw[i]!
    const prompt = `${q.question}\n\n${q.choices.map((c, j) => `${LETTERS[j]}. ${c}`).join('\n')}`
    const t0 = Date.now()
    let model = FAST, letter = extractLetter(await ask(FAST, prompt)); fastTotal++
    let didEscalate = false
    if (!letter) { // fast model wouldn't commit → escalate
      didEscalate = true; escalated++; strongTotal++; model = STRONG
      letter = extractLetter(await ask(STRONG, prompt))
    }
    const ms = Date.now() - t0; msTotal += ms; answered++
    const ok = letter === LETTERS[q.answer]
    if (ok) {
      correct++
      if (didEscalate) strongCorrect++; else fastCorrect++
    }
    ;(bySub[q.subject] ??= { c: 0, n: 0 }).n++; if (ok) bySub[q.subject]!.c++
    fs.appendFileSync(TRANSCRIPT, JSON.stringify({ i, subject: q.subject, model, escalated: didEscalate, correct: ok, pred: letter || '?', gold: LETTERS[q.answer], ms }) + '\n')
    console.log(`  ${String(i + 1).padStart(4)}. ${ok ? '✓' : '✗'} ${q.subject.slice(0, 22).padEnd(22)} [${didEscalate ? '7B' : '3B'}] pred ${letter || '?'}/${LETTERS[q.answer]}  · running ${pct(correct, answered)}% (${correct}/${answered})`)
  }
  summary()
}
main().catch((e) => { console.error(e); process.exit(1) })
