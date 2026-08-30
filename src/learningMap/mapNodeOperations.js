import { validateLearningMap } from './mapValidation.js'

const emptyNode = (id, title = '新しい学習項目') => ({
  id, title, canonicalName: title, aliases: [], type: 'concept', reason: '', relation: '',
  level: '概要を説明できる', completion: '', status: 'notStarted', notes: '', references: '',
  checklist: {}, proofSteps: [], resolvedReviewIds: [], prerequisiteIds: [], included: true,
  importance: 'recommended', confirmationStatus: 'confirmed', sourceType: 'user-confirmed',
})

export function normalizeNodeNotes(map) {
  return { ...map, nodes: (map.nodes ?? []).map((node) => ({ ...node, notes: typeof node.notes === 'string' ? node.notes : '' })) }
}

export function addLearningNode(map, id, now = new Date().toISOString()) {
  if (!id || map.nodes.some((node) => node.id === id)) throw new Error('新規ノードIDが重複しています。')
  const node = emptyNode(id)
  return { map: { ...map, nodes: [...map.nodes, node], updatedAt: now }, node }
}

export function duplicateLearningNode(map, sourceId, id, now = new Date().toISOString()) {
  const source = map.nodes.find((node) => node.id === sourceId)
  if (!source) throw new Error('複製元のノードが見つかりません。')
  if (!id || map.nodes.some((node) => node.id === id)) throw new Error('複製ノードIDが重複しています。')
  const node = { ...structuredClone(source), id, title: `${source.title}（複製）`, canonicalName: `${source.canonicalName ?? source.title} copy`, type: source.type === 'goal' ? 'concept' : source.type, prerequisiteIds: [], confirmationStatus: 'confirmed', sourceType: 'user-confirmed' }
  return { map: { ...map, nodes: [...map.nodes, node], updatedAt: now }, node }
}

export function deleteLearningNode(map, id, now = new Date().toISOString()) {
  const target = map.nodes.find((node) => node.id === id)
  if (!target) return map
  if (target.type === 'goal') throw new Error('目標ノードは削除できません。先に別の目標を設定してください。')
  return {
    ...map,
    nodes: map.nodes.filter((node) => node.id !== id),
    edges: map.edges.filter((edge) => edge.sourceId !== id && edge.targetId !== id),
    updatedAt: now,
  }
}

export function serializeLearningMap(map) {
  return JSON.stringify({ format: 'math-learning-map', version: 1, map: normalizeNodeNotes(map) }, null, 2)
}

export function deserializeLearningMap(text, now = new Date().toISOString()) {
  let payload
  try { payload = JSON.parse(text) } catch { throw new Error('JSONとして読み込めませんでした。') }
  if (payload?.format !== 'math-learning-map' || payload?.version !== 1 || !payload.map) throw new Error('対応していない学習マップ形式です。')
  const map = normalizeNodeNotes(payload.map)
  if (!map.id || !Array.isArray(map.nodes) || !Array.isArray(map.edges)) throw new Error('学習マップの必須項目がありません。')
  const errors = validateLearningMap(map)
  if (errors.length) throw new Error(`学習マップが不正です: ${errors.join(' / ')}`)
  return { ...map, id: `${map.id}-import-${Date.now()}`, name: `${map.name}（インポート）`, createdAt: now, updatedAt: now }
}
