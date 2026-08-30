import { DEMO_NODES } from './demoData.js'
import { LEARNING_MAP_STORAGE_KEY } from './constants.js'

export const MAPS_STORAGE_KEY = 'math-reading-learning-maps-v2'
export const MAPS_STORAGE_VERSION = 4

function migrateMap(map) {
  const aiReview = map.aiReview ? {
    ...map.aiReview,
    issues: (map.aiReview.issues ?? []).map((issue) => ({ resolutionStatus: 'unresolved', resolutionReason: '', resolvedAt: null, ...issue })),
  } : null
  return {
    ...map,
    nodes: (map.nodes ?? []).map((node) => ({ ...node, notes: typeof node.notes === 'string' ? node.notes : '' })),
    originalAiOutput: map.originalAiOutput ?? null,
    modificationHistory: map.modificationHistory ?? [],
    planningTiming: map.planningTiming ?? {},
    evidenceExcerpts: map.evidenceExcerpts ?? [],
    ...(aiReview ? { aiReview } : {}),
  }
}

function demoEdges(nodes) {
  return nodes.flatMap((target) => target.prerequisiteIds.map((sourceId) => ({
    id: `${sourceId}--${target.id}`, sourceId, targetId: target.id, type: '定義の理解に必要', rationale: 'Floerデモの既存依存関係', confirmationStatus: 'confirmed',
  })))
}

export function createFloerDemoMap(savedV1 = null, now = new Date().toISOString()) {
  const savedNodes = savedV1?.nodes ?? {}
  const nodes = DEMO_NODES.map((node) => ({ ...node, ...(savedNodes[node.id] ?? {}), included: true, importance: node.minimal ? 'required' : 'supporting', confirmationStatus: 'confirmed' }))
  return {
    id: 'floer-demo', name: 'Lagrangian Floer複体の基本構成', goal: 'Lagrangian Floer複体の基本構成を理解する',
    sourceType: 'demo', sourceLabel: 'デモ', pdf: null, nodes, edges: demoEdges(nodes), createdAt: now, updatedAt: now, candidateStatus: 'approved',
  }
}

export function migrateLearningMaps(rawV2, rawV1, now = new Date().toISOString()) {
  if ([2, 3, MAPS_STORAGE_VERSION].includes(rawV2?.version) && Array.isArray(rawV2.maps)) {
    return { ...rawV2, version: MAPS_STORAGE_VERSION, maps: rawV2.maps.map(migrateMap) }
  }
  return { version: MAPS_STORAGE_VERSION, activeMapId: 'floer-demo', maps: [createFloerDemoMap(rawV1, now)] }
}

export function loadLearningMaps(storage = localStorage) {
  let rawV2 = null, rawV1 = null
  try { rawV2 = JSON.parse(storage.getItem(MAPS_STORAGE_KEY)) } catch { /* use migration */ }
  try { rawV1 = JSON.parse(storage.getItem(LEARNING_MAP_STORAGE_KEY)) } catch { /* no legacy data */ }
  const migrated = migrateLearningMaps(rawV2, rawV1)
  try { storage.setItem(MAPS_STORAGE_KEY, JSON.stringify(migrated)) } catch { /* surface on the next explicit save */ }
  return migrated
}

export function saveLearningMaps(data, storage = localStorage) {
  storage.setItem(MAPS_STORAGE_KEY, JSON.stringify({ ...data, version: MAPS_STORAGE_VERSION }))
}
