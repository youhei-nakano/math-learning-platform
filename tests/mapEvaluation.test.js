import test from 'node:test'
import assert from 'node:assert/strict'
import { evaluateLearningMap, matchConcepts, normalizeConceptName } from '../src/learningMap/mapEvaluation.js'
import { buildEvidenceExcerpts, calculatePlanningTiming, createOriginalAiOutput, recordModification } from '../src/learningMap/candidateAudit.js'

const baseline = {
  nodes: [
    { id: 'b1', title: 'ベクトル空間', canonicalName: 'vector space', aliases: ['線形空間'], importance: 'required', sourcePages: [10], sourceSections: ['第1節'], included: true },
    { id: 'b2', title: '基底', canonicalName: 'basis', aliases: ['基底'], importance: 'required', sourcePages: [20], sourceSections: ['第2節'], included: true },
  ],
  edges: [{ id: 'be', sourceId: 'b1', targetId: 'b2' }],
}

test('ノード名をUnicode・空白・記号を含めて正規化する', () => {
  assert.equal(normalizeConceptName(' Ｖector-Space '), 'vectorspace')
})

test('aliasで概念を照合する', () => {
  const result = matchConcepts([{ id: 'a', title: '線形空間', included: true }], baseline.nodes)
  assert.equal(result.matches[0].baseline.id, 'b1')
})

test('ページと節だけが近い不確かな概念は自動一致させない', () => {
  const result = matchConcepts([{ id: 'a', title: '空間の準備', sourcePages: [10], sourceSections: ['第1節'], included: true }], baseline.nodes)
  assert.equal(result.matches.length, 0)
  assert.equal(result.needsHumanMatch.length, 1)
})

test('概念・依存関係・ページの評価指標を計算する', () => {
  const candidate = {
    nodes: [
      { id: 'a1', title: 'Vector Space', canonicalName: 'vector space', included: true, sourcePages: [10] },
      { id: 'a2', title: 'Basis', canonicalName: 'basis', included: true, sourcePages: [21] },
      { id: 'extra', title: '余分', included: true, sourcePages: [30] },
    ],
    edges: [{ id: 'ae', sourceId: 'a1', targetId: 'a2' }, { id: 'extra-edge', sourceId: 'extra', targetId: 'a2' }],
    originalAiOutput: { nodes: [{}, {}, {}] }, modificationHistory: [{ id: 'c' }],
  }
  const result = evaluateLearningMap(candidate, baseline)
  assert.equal(result.metrics.requiredConceptRecall, 1)
  assert.equal(result.metrics.conceptPrecision, 2 / 3)
  assert.equal(result.metrics.unnecessaryConceptRate, 1 / 3)
  assert.equal(result.metrics.dependencyPrecision, 1 / 2)
  assert.equal(result.metrics.dependencyRecall, 1)
  assert.equal(result.metrics.sourcePageAccuracy, 1 / 2)
  assert.equal(result.metrics.aiNodeCount, 3)
  assert.equal(result.metrics.humanCorrectionCount, 1)
})

test('修正履歴を記録して元AI出力を分離する', () => {
  const graph = { nodes: [{ id: 'n', title: 'AI title' }], edges: [], warnings: [] }
  const originalAiOutput = createOriginalAiOutput(graph, { issues: [] })
  const changed = recordModification({ nodes: [{ id: 'n', title: 'edited' }], originalAiOutput }, { type: 'node-title', targetId: 'n', before: 'AI title', after: 'edited' }, '2026-01-01T00:00:00.000Z')
  assert.equal(changed.modificationHistory[0].type, 'node-title')
  assert.equal(changed.modificationHistory[0].changedAt, '2026-01-01T00:00:00.000Z')
  assert.equal(changed.originalAiOutput.nodes[0].title, 'AI title')
})

test('時刻がない既存データと限定根拠抜粋を安全に扱う', () => {
  assert.equal(calculatePlanningTiming({}).totalPlanningMs, null)
  const excerpts = buildEvidenceExcerpts([{ sourcePages: [2, 9] }], [], [{ page: 2, text: 'sent' }, { page: 3, text: 'not sent' }])
  assert.deepEqual(excerpts, [{ page: 2, text: 'sent' }])
})
