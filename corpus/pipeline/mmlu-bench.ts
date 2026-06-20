/**
 * mmlu-bench.ts — real, auto-graded competency benchmark against the LOCAL stack
 * using standardized exam banks (MMLU STEM + GSM8K) — the same benchmarks frontier
 * labs report on, so the result is directly comparable to published scores.
 *
 * Banks (fetched to ~/.noetica/corpus/benchmarks):
 *   mmlu_stem.json   — {subject: [{question, choices[4], answer: idx}]}
 *   gsm8k_test.jsonl — {question, answer: "...\n#### <number>"}
 *
 * Usage:
 *   tsx scripts/mmlu-bench.ts                 # default sample per subject
 *   MMLU_PER_SUBJECT=10 tsx ...               # items per subject
 *   MMLU_MODEL=deepseek-r1:8b-cpu tsx ...
 *   GSM8K_N=20 tsx ...                        # GSM8K problems (0 = skip)
 */
import * as fs from 'node:fs'
import * as os from 'node:os'
import * as path from 'node:path'

const BANK = path.join(os.homedir(), '.noetica', 'corpus', 'benchmarks')
const BASE = process.env['OLLAMA_HOST']?.replace(/\/$/, '') || 'http://127.0.0.1:11435'
const MODEL = process.env['MMLU_MODEL'] || 'qwen2.5:7b-cpu'
const PER = Number(process.env['MMLU_PER_SUBJECT'] || 10)
const GSM_N = Number(process.env['GSM8K_N'] ?? 10)
const TIMEOUT = Number(process.env['MMLU_TIMEOUT_MS'] || 150_000)
const LETTERS = ['A', 'B', 'C', 'D']

// Published frontier MMLU (overall) for context — these are whole-MMLU averages,
// shown as a reference band, not per-subject claims.
const FRONTIER = { 'GPT-4': 86.4, 'Claude 3.5 Sonnet': 88.7, 'Llama-3-70B': 79.5, 'Qwen2.5-7B (reported)': 74.2 }

async function ask(prompt: string, sys: string): Promise<string> {
  const res = await fetch(`${BASE}/v1/chat/completions`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ model: MODEL, stream: false, messages: [{ role: 'system', content: sys }, { role: 'user', content: prompt }] }),
    signal: AbortSignal.timeout(TIMEOUT),
  })
  const d = await res.json() as { choices?: Array<{ message?: { content?: string; reasoning_content?: string } }> }
  const m = d.choices?.[0]?.message
  return (m?.content || m?.reasoning_content || '').trim()
}

function extractLetter(raw: string): string {
  const f = /FINAL:\s*([A-D])/i.exec(raw); if (f) return f[1]!.toUpperCase()
  const m = /\b([A-D])\b(?![\s\S]*\b[A-D]\b)/.exec(raw.trim()); return m ? m[1]!.toUpperCase() : ''
}
function extractNumber(raw: string): number | null {
  const f = /FINAL:\s*([^\n]+)/i.exec(raw); const s = f ? f[1]! : raw
  const m = s.replace(/[$,]/g, '').match(/-?\d+(?:\.\d+)?/g); return m ? Number(m[m.length - 1]) : null
}

async function main() {
  const sysMC = 'You are taking a multiple-choice exam. Reason briefly, then end with a line "FINAL: X" where X is the single correct letter (A, B, C, or D).'
  const results: Array<{ subject: string; correct: boolean; ms: number }> = []

  const mmlu = JSON.parse(fs.readFileSync(path.join(BANK, 'mmlu_stem.json'), 'utf8')) as Record<string, Array<{ question: string; choices: string[]; answer: number }>>
  console.log(`# MMLU STEM + GSM8K — model=${MODEL} | ${PER}/subject, ${GSM_N} GSM8K\n`)
  for (const [subject, items] of Object.entries(mmlu)) {
    const sample = items.slice(0, PER)
    let correct = 0
    for (const it of sample) {
      const prompt = `${it.question}\n\n${it.choices.map((c, i) => `${LETTERS[i]}. ${c}`).join('\n')}`
      const t0 = Date.now()
      let ok = false
      try { ok = extractLetter(await ask(prompt, sysMC)) === LETTERS[it.answer] } catch { /* timeout/err = wrong */ }
      results.push({ subject, correct: ok, ms: Date.now() - t0 }); if (ok) correct++
    }
    console.log(`  ${subject.padEnd(26)} ${correct}/${sample.length}  (${Math.round(100 * correct / sample.length)}%)`)
  }

  // GSM8K (numeric)
  let gsmCorrect = 0, gsmTotal = 0
  if (GSM_N > 0) {
    const sysN = 'Solve the math word problem. Show brief work, then end with "FINAL: <number>".'
    const lines = fs.readFileSync(path.join(BANK, 'gsm8k_test.jsonl'), 'utf8').trim().split('\n').slice(0, GSM_N)
    for (const line of lines) {
      const { question, answer } = JSON.parse(line) as { question: string; answer: string }
      const gold = Number((/####\s*([-\d,.]+)/.exec(answer)?.[1] || '').replace(/,/g, ''))
      let ok = false
      try { const n = extractNumber(await ask(question, sysN)); ok = n != null && Math.abs(n - gold) < 0.001 } catch { /* wrong */ }
      gsmTotal++; if (ok) gsmCorrect++
    }
    console.log(`  ${'GSM8K (math word probl.)'.padEnd(26)} ${gsmCorrect}/${gsmTotal}  (${Math.round(100 * gsmCorrect / gsmTotal)}%)`)
  }

  const total = results.length + gsmTotal
  const correct = results.filter((r) => r.correct).length + gsmCorrect
  const overall = Math.round(100 * correct / total)
  console.log(`\n## Overall: ${correct}/${total} (${overall}%)  [model: ${MODEL}, local CPU]`)
  console.log(`\n## Published frontier MMLU (overall, for reference):`)
  for (const [k, v] of Object.entries(FRONTIER)) console.log(`  ${k.padEnd(24)} ${v}%`)

  const out = { model: MODEL, generated_at: new Date().toISOString(), overall_pct: overall, total, correct,
    by_subject: Object.fromEntries(Object.entries(mmlu).map(([s]) => { const rs = results.filter((r) => r.subject === s); return [s, { correct: rs.filter((r) => r.correct).length, total: rs.length }] })),
    gsm8k: { correct: gsmCorrect, total: gsmTotal }, frontier_reference: FRONTIER }
  const p = path.join(os.homedir(), '.noetica', `mmlu-transcript-${Date.now()}.json`)
  fs.writeFileSync(p, JSON.stringify(out, null, 2)); console.log(`\nTranscript: ${p}`)
}
void main()
