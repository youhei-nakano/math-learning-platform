import { NODE_TYPES } from './constants.js'
import { EDGE_TYPES } from './linearAlgebraData.js'

const AI_EDGE_TYPES = ['definition-required', 'theorem-required', 'used-in-proof', 'calculation-required', 'helpful', 'optional-for-goal']
const IMPORTANCE = ['required', 'recommended', 'supporting']

export function validateLearningMap(map, { maxNodes = 30, maxPages = 50 } = {}) {
  const errors = [], includedNodes = (map.nodes ?? []).filter((node) => node.included !== false)
  const nodeCounts = new Map(), edgeCounts = new Map()
  for (const node of map.nodes ?? []) nodeCounts.set(node.id, (nodeCounts.get(node.id) ?? 0) + 1)
  for (const edge of map.edges ?? []) edgeCounts.set(edge.id, (edgeCounts.get(edge.id) ?? 0) + 1)
  for (const [id, count] of nodeCounts) if (count > 1) errors.push(`ノードID重複: ${id}`)
  for (const [id, count] of edgeCounts) if (count > 1) errors.push(`エッジID重複: ${id}`)
  if (includedNodes.length > maxNodes) errors.push(`最大ノード数超過: ${includedNodes.length}/${maxNodes}`)
  const ids = new Set(includedNodes.map((node) => node.id)), pageCount = map.pdf?.pageCount ?? Infinity
  const sentPages = new Set(map.selectedSections?.flatMap((section) => section.pages ?? Array.from({ length: section.endPage - section.startPage + 1 }, (_, index) => section.startPage + index)) ?? [])
  if (sentPages.size > maxPages) errors.push(`最大ページ数超過: ${sentPages.size}/${maxPages}`)
  for (const node of includedNodes) {
    const pages = node.sourcePages ?? (node.pdfPage ? [node.pdfPage] : [])
    if (pages.some((page) => page < 1 || page > pageCount)) errors.push(`参照ページ範囲外: ${node.id}`)
    if (map.creationMethod === 'ai-concept-dependency' && node.sourceType === 'pdf-evidence' && !pages.length) errors.push(`PDF内根拠ページなし: ${node.id}`)
    if (map.creationMethod === 'ai-concept-dependency' && node.sourceType === 'external-prerequisite-suggestion' && node.importance === 'required') errors.push(`PDF外前提を必須として自動採用: ${node.id}`)
    if (!NODE_TYPES[node.type]) errors.push(`無効なノード種別: ${node.id}`)
    if (!IMPORTANCE.includes(node.importance)) errors.push(`無効な採用区分: ${node.id}`)
  }
  const goals = includedNodes.filter((node) => node.type === 'goal')
  if (!goals.length) errors.push('目標ノードがありません')
  if (goals.length > 1) errors.push('目標ノードが複数あります')
  const adjacency = Object.fromEntries([...ids].map((id) => [id, []]))
  for (const edge of map.edges ?? []) {
    if (!ids.has(edge.sourceId) || !ids.has(edge.targetId)) { errors.push(`存在しないノードを参照するエッジ: ${edge.id}`); continue }
    if (edge.sourceId === edge.targetId) errors.push(`自己ループ: ${edge.id}`)
    if (![...EDGE_TYPES, ...AI_EDGE_TYPES].includes(edge.type)) errors.push(`無効な依存関係種別: ${edge.id}`)
    adjacency[edge.sourceId].push(edge.targetId)
  }
  const visiting = new Set(), visited = new Set()
  function visit(id) {
    if (visiting.has(id)) return true
    if (visited.has(id)) return false
    visiting.add(id)
    if (adjacency[id].some(visit)) return true
    visiting.delete(id); visited.add(id); return false
  }
  if ([...ids].some(visit)) errors.push('依存グラフに循環があります')
  if (goals.length === 1) {
    const reverse = Object.fromEntries([...ids].map((id) => [id, []]))
    for (const [source, targets] of Object.entries(adjacency)) for (const target of targets) reverse[target].push(source)
    const reachable = new Set([goals[0].id]), stack = [goals[0].id]
    while (stack.length) for (const source of reverse[stack.pop()]) if (!reachable.has(source)) { reachable.add(source); stack.push(source) }
    for (const node of includedNodes) if (node.importance === 'required' && !reachable.has(node.id)) errors.push(`目標へ到達できない必須ノード: ${node.id}`)
  }
  return [...new Set(errors)]
}
