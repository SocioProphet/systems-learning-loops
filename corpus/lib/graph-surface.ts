/**
 * graph-surface — pure selection of a LEGIBLE, force-graph-ready subgraph from raw
 * HellGraph nodes/edges. Shared by the Next API route (web) and the agent-machine
 * backend route (Tauri desktop) so the two never drift. No imports — takes the node/
 * edge arrays as data, returns {nodes, links, total}.
 *
 * Lenses (`view`): `all` = a diverse named cross-section; `domain`/`document`/`chat` =
 * a CONNECTED subgraph BFS-walked along real edges from typed roots (or a `root` id).
 */

import type { GraphNode, GraphEdge } from '@socioprophet/hellgraph'
type GNode = GraphNode
type GEdge = GraphEdge
export interface SurfaceNode { id: string; label: string; category: string; featured: boolean; degree: number }
export interface SurfaceLink { source: string; target: string; primary: boolean }
export interface SurfaceResult { nodes: SurfaceNode[]; links: SurfaceLink[]; total: { nodes: number; edges: number } }

// label → colour category (docs/learning/technical/trust/deployment palette)
export function categoryFor(label: string): string {
  const l = label.toLowerCase()
  const has = (...ks: string[]) => ks.some((k) => l.includes(k))
  if (has('topic', 'domain', 'glossary', 'concept', 'math', 'formula', 'function', 'variable', 'unit', 'physical', 'quantity', 'learningstate')) return 'learning'
  if (has('document', 'chunk', 'record', 'source', 'evidence', 'episode', 'interaction', 'proof', 'semanticmemory', 'claim')) return 'docs'
  if (has('artifact', 'feature', 'vector', 'model', 'provider', 'repo', 'tool', 'action', 'candidate', 'checkpoint', 'attention')) return 'technical'
  if (has('entity', 'canonical', 'person', 'org', 'role', 'trust', 'attest', 'decision', 'ledger', 'concordance', 'remediation', 'shacl')) return 'trust'
  if (has('session', 'dispatch', 'event', 'run', 'self', 'loc')) return 'deployment'
  return 'other'
}

function isHashy(s: string): boolean {
  const t = s.trim()
  if (t.length < 2) return true
  const compact = t.replace(/[\s\-_]/g, '')
  if (/^[0-9a-f]{6,}$/i.test(compact)) return true
  const hex = (compact.match(/[0-9a-f]/gi) ?? []).length
  return compact.length >= 8 && hex / compact.length > 0.7
}
function isProse(s: string): boolean {
  if (/[#>]|\.\.\./.test(s)) return true
  if (/[.;:,]\s/.test(s)) return true
  if (s.trim().split(/\s+/).length > 4) return true
  return false
}
export function cleanLabel(n: GNode): string | null {
  for (const key of ['title', 'name', 'surface', 'normalised', 'filename']) {
    const v = n.properties[key]
    if (v == null) continue
    const s = String(v)
      .replace(/\s+/g, ' ')
      .replace(/^\[[^\]]*\]\s*/, '')
      .replace(/\.(pdf|txt|md|json|vtt|srt|docx|pptx|xlsx|csv|html?)$/i, '')
      .replace(/^[#>.\-\s]+/, '')
      .trim()
    if (s && !isHashy(s) && !isProse(s)) return s.slice(0, 22)
  }
  const last = (n.id.split(':').pop() ?? '').replace(/-[0-9a-f]{4,}$/i, '').replace(/-/g, ' ').trim()
  return last && !isHashy(last) && !isProse(last) ? last.slice(0, 22) : null
}

const VIEW_ROOTS: Record<string, (label: string) => boolean> = {
  domain: (l) => l === 'Domain' || l === 'Topic' || l === 'GlossaryTerm',
  document: (l) => l === 'Document' || l === 'RECORD',
  chat: (l) => l === 'Conversation' || l === 'Message' || l.endsWith('Message'),
}

export function selectSurface(allNodes: GNode[], allEdges: GEdge[], opts: { view?: string; limit?: number; root?: string } = {}): SurfaceResult {
  const limit = Math.min(120, Math.max(10, opts.limit ?? 34))
  const view = opts.view ?? 'all'
  const root = opts.root ?? ''

  const degree = new Map<string, number>()
  const adj = new Map<string, Set<string>>()
  for (const e of allEdges) {
    degree.set(e.from, (degree.get(e.from) ?? 0) + 1)
    degree.set(e.to, (degree.get(e.to) ?? 0) + 1)
    ;(adj.get(e.from) ?? adj.set(e.from, new Set()).get(e.from)!).add(e.to)
    ;(adj.get(e.to) ?? adj.set(e.to, new Set()).get(e.to)!).add(e.from)
  }
  const labeled = allNodes.filter((n) => cleanLabel(n) !== null)
  const byId = new Map(labeled.map((n) => [n.id, n]))

  let picked: GNode[]
  const rootMatch = VIEW_ROOTS[view]
  if (rootMatch) {
    const roots = (root && byId.has(root) ? [byId.get(root)!] : labeled.filter((n) => rootMatch(n.labels[0] ?? '')))
      .sort((a, b) => (degree.get(b.id) ?? 0) - (degree.get(a.id) ?? 0))
    const seen = new Set<string>()
    const queue: string[] = []
    for (const r of roots) { if (seen.size >= limit) break; if (!seen.has(r.id)) { seen.add(r.id); queue.push(r.id) } }
    while (queue.length && seen.size < limit) {
      const id = queue.shift()!
      for (const nb of adj.get(id) ?? []) {
        if (seen.size >= limit) break
        if (!seen.has(nb) && byId.has(nb)) { seen.add(nb); queue.push(nb) }
      }
    }
    picked = [...seen].map((id) => byId.get(id)!).filter(Boolean)
  } else {
    const ranked = labeled.slice().sort((a, b) => (degree.get(b.id) ?? 0) - (degree.get(a.id) ?? 0) || Number(b.createdAt ?? 0) - Number(a.createdAt ?? 0))
    const byLabel = new Map<string, GNode[]>()
    for (const n of ranked) { const l = n.labels[0] ?? 'node'; const arr = byLabel.get(l); if (arr) arr.push(n); else byLabel.set(l, [n]) }
    picked = []
    let progress = true
    while (picked.length < limit && progress) {
      progress = false
      for (const arr of byLabel.values()) { const n = arr.shift(); if (n) { picked.push(n); progress = true; if (picked.length >= limit) break } }
    }
  }

  const keep = new Set(picked.map((n) => n.id))
  const maxDeg = Math.max(1, ...picked.map((n) => degree.get(n.id) ?? 0))
  const nodes: SurfaceNode[] = picked.map((n) => {
    const lbl = n.labels[0] ?? 'node'
    const deg = degree.get(n.id) ?? 0
    return { id: n.id, label: cleanLabel(n) ?? lbl, category: categoryFor(lbl), featured: deg >= maxDeg * 0.6, degree: deg }
  })

  const shown = new Map<string, number>()
  const CAP = 3
  const links: SurfaceLink[] = []
  for (const e of allEdges) {
    if (!keep.has(e.from) || !keep.has(e.to) || e.from === e.to) continue
    if ((shown.get(e.from) ?? 0) >= CAP || (shown.get(e.to) ?? 0) >= CAP) continue
    shown.set(e.from, (shown.get(e.from) ?? 0) + 1)
    shown.set(e.to, (shown.get(e.to) ?? 0) + 1)
    links.push({ source: e.from, target: e.to, primary: (degree.get(e.from) ?? 0) >= maxDeg * 0.6 || (degree.get(e.to) ?? 0) >= maxDeg * 0.6 })
  }

  return { nodes, links, total: { nodes: allNodes.length, edges: allEdges.length } }
}
