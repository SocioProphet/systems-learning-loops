#!/usr/bin/env -S node --import tsx
/**
 * fetch-ocw — pull MIT OpenCourseWare course archives for the MMLU-aligned subjects.
 * For each course slug it scrapes the course's /download/ page for the .zip href and
 * fetches it (dupes across subjects are fine — more sampled corpora + exam banks). A
 * slug that 404s is logged, not fatal, so the run completes and reports the misses to
 * resolve by hand. Pure I/O — never loads a model, so it can't thrash the box.
 *
 * Usage:  npx tsx scripts/fetch-ocw.ts [subject ...]   (default: all)
 *         OCW_DEST=~/Downloads/MIT\ OCW npx tsx scripts/fetch-ocw.ts physics
 */
import * as fs from 'node:fs'
import * as os from 'node:os'
import * as path from 'node:path'
import { execFileSync } from 'node:child_process'

const DEST = (process.env['OCW_DEST'] || path.join(os.homedir(), 'Downloads', 'MIT OCW')).replace(/^~/, os.homedir())

// MMLU STEM subjects → OCW flagship courses (curriculum-ordered within subject).
const CATALOG: Record<string, string[]> = {
  physics: [
    '8-01sc-classical-mechanics-fall-2016',
    '8-02t-electricity-and-magnetism-spring-2005',
    '8-03sc-physics-iii-vibrations-and-waves-fall-2016',
  ],
  chemistry: [
    '5-111sc-principles-of-chemical-science-fall-2014',
    '5-112-principles-of-chemical-science-fall-2005',
    '5-60-thermodynamics-kinetics-spring-2008',
  ],
  statistics: [
    '18-05-introduction-to-probability-and-statistics-spring-2022',
    '6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013',
    '18-650-statistics-for-applications-fall-2016',
  ],
  algebra: [
    '18-701-algebra-i-fall-2010',
    '18-702-algebra-ii-spring-2011',
    '18-703-modern-algebra-spring-2013',
  ],
  cs: [
    '6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016',
    '6-006-introduction-to-algorithms-spring-2020',
    '6-046j-design-and-analysis-of-algorithms-spring-2015',
  ],
  ee: [
    '6-002-circuits-and-electronics-spring-2007',
    '6-003-signals-and-systems-fall-2011',
  ],
  astronomy: [
    '8-282j-introduction-to-astronomy-spring-2006',
    '8-901-astrophysics-i-spring-2006',
  ],
  machine_learning: [
    '6-867-machine-learning-fall-2006',
    '9-520-statistical-learning-theory-and-applications-spring-2006',
    '6-034-artificial-intelligence-fall-2010',
  ],
  computer_security: [
    '6-858-computer-systems-security-fall-2014',
    '6-857-network-and-computer-security-spring-2014',
  ],
}

const UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'

/** curl text (follow redirects), empty string on failure. */
function get(url: string): string {
  try { return execFileSync('curl', ['-sL', '-m', '40', '-A', UA, url], { encoding: 'utf8', maxBuffer: 32 * 1024 * 1024 }) } catch { return '' }
}

/** Find the course archive .zip URL from the /download/ page. */
function zipUrl(slug: string): string | null {
  const page = get(`https://ocw.mit.edu/courses/${slug}/download/`)
  const m = page.match(/https:\/\/ocw\.mit\.edu\/courses\/[^"']*?\.zip/i)
  return m ? m[0] : null
}

function download(url: string, dest: string): boolean {
  try {
    execFileSync('curl', ['-sL', '-m', '600', '-A', UA, '-o', dest, url], { stdio: 'ignore' })
    const sz = fs.existsSync(dest) ? fs.statSync(dest).size : 0
    if (sz < 100_000) { try { fs.rmSync(dest) } catch { /* */ }; return false } // too small = error page
    return true
  } catch { return false }
}

function main() {
  const want = process.argv.slice(2).filter((a) => !a.startsWith('-'))
  const subjects = want.length ? want : Object.keys(CATALOG)
  fs.mkdirSync(DEST, { recursive: true })
  console.log(`# fetching OCW → ${DEST}\n# subjects: ${subjects.join(', ')}\n`)

  const got: string[] = [], missed: string[] = []
  for (const subj of subjects) {
    const courses = CATALOG[subj]
    if (!courses) { console.log(`  ? unknown subject: ${subj}`); continue }
    console.log(`## ${subj}`)
    for (const slug of courses) {
      const out = path.join(DEST, `${slug}.zip`)
      if (fs.existsSync(out) && fs.statSync(out).size > 100_000) { console.log(`  = ${slug} (already have)`); got.push(slug); continue }
      const url = zipUrl(slug)
      if (!url) { console.log(`  ✗ ${slug} — no zip found (check slug)`); missed.push(slug); continue }
      const ok = download(url, out)
      const mb = ok ? (fs.statSync(out).size / 1048576).toFixed(0) : '0'
      console.log(`  ${ok ? '✓' : '✗'} ${slug}${ok ? ` (${mb}MB)` : ' — download failed'}`)
      ;(ok ? got : missed).push(slug)
    }
  }
  console.log(`\n# done: ${got.length} courses present, ${missed.length} missed`)
  if (missed.length) console.log(`# resolve by hand: ${missed.join(' ')}`)
}
main()
