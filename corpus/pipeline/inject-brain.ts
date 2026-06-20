#!/usr/bin/env -S node --import tsx
/**
 * inject-brain — load a precomputed BRAIN shard (build-corpus.ts output) into the live
 * agent KB WITHOUT re-embedding. Thin CLI over HellGraph's native `importBrainShard`:
 * the vector pipeline lives in the graph now, so this just points it at the shards. A
 * cold agent slurps `mathematics.jsonl` and instantly knows MIT math — the "brain
 * injection," idempotent per (docId, idx).
 *
 * Usage:  npx tsx scripts/inject-brain.ts <shard.jsonl | brain-dir> [--limit N] [--probe "query"]
 */
import * as fs from 'node:fs'
import * as path from 'node:path'
import { importBrainShard, vectorChunkCount } from '@socioprophet/hellgraph'
import { semanticSearch } from '../lib/doc-store.js'

const arg = process.argv[2]
const LIMIT = (() => { const i = process.argv.indexOf('--limit'); return i >= 0 ? Number(process.argv[i + 1]) : undefined })()
const PROBE = (() => { const i = process.argv.indexOf('--probe'); return i >= 0 ? process.argv[i + 1] : '' })()
if (!arg || !fs.existsSync(arg)) { console.error('usage: inject-brain.ts <shard.jsonl|brain-dir> [--limit N] [--probe "q"]'); process.exit(1) }

/** A single shard file, or every per-course/legacy *.jsonl under a brain dir. */
function shards(p: string): string[] {
  if (!fs.statSync(p).isDirectory()) return [p]
  const out: string[] = []
  const walk = (d: string) => {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      if (e.name.startsWith('.') || e.name.startsWith('_')) continue
      const full = path.join(d, e.name)
      if (e.isDirectory()) walk(full)
      else if (e.name.endsWith('.jsonl')) out.push(full)
    }
  }
  walk(p)
  return out
}

async function main() {
  const list = shards(arg)
  const before = vectorChunkCount()
  console.log(`# brain injection — ${list.length} shard(s), vectorized chunks before = ${before}\n`)
  let totalC = 0, totalD = 0, totalS = 0
  for (const s of list) {
    const r = importBrainShard(s, LIMIT != null ? { limit: LIMIT } : {})
    totalC += r.chunks; totalD += r.docs; totalS += r.skipped
    console.log(`  ✓ ${path.basename(s).padEnd(28)} +${r.chunks} vectors · ${r.docs} docs${r.skipped ? ` · ${r.skipped} already present` : ''}`)
  }
  console.log(`\n# injected ${totalC} precomputed vectors across ${totalD} docs (no re-embedding). Vectorized chunks now = ${vectorChunkCount()}`)

  if (PROBE) {
    console.log(`\n# probe: "${PROBE}"`)
    const hits = await semanticSearch(PROBE, 3)
    for (const h of hits) console.log(`  [${h.score.toFixed(3)}] ${h.filename}  ::  ${h.text.replace(/\s+/g, ' ').slice(0, 110)}…`)
    if (!hits.length) console.log('  (no hits — check the embed runner / shard)')
  }
}
main().catch((e) => { console.error(e); process.exit(1) })
