import { DEMO_NODES, DEMO_REVIEWS } from './demoData'

// 将来は同じ戻り値の形を保ったAPI実装へ差し替える境界。
export async function generateLearningGraph() {
  return structuredClone(DEMO_NODES)
}

export async function reviewConceptUnderstanding() {
  return { status: 'not-implemented', message: 'このプロトタイプではAI理解レビューを実行しません。' }
}

export async function reviewProofSteps(nodeId) {
  return structuredClone(DEMO_REVIEWS[nodeId] ?? [])
}

export async function searchReferences() {
  return { status: 'not-implemented', results: [] }
}
