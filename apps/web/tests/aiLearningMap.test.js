import test from 'node:test'
import assert from 'node:assert/strict'
import { confirmCandidatesForTab, normalizeSelectedSections, toApiPageTexts, toCandidateMap } from '../src/learningMap/aiLearningMapService.js'
import { validateLearningMap } from '../src/learningMap/mapValidation.js'

test('関連章節の重複ページを除き50ページで制限する', () => {
  const result = normalizeSelectedSections([
    { outlineId: 'a', title: 'A', startPage: 1, endPage: 30 },
    { outlineId: 'b', title: 'B', startPage: 20, endPage: 60 },
  ], 100, 50)
  assert.equal(result.pageNumbers.length, 50)
  assert.equal(new Set(result.pageNumbers).size, 50)
})

test('既定運用の12ページ上限でも章節範囲を正規化する', () => {
  const result = normalizeSelectedSections([
    { outlineId: 'a', title: 'A', startPage: 1, endPage: 20 },
  ], 100, 12)
  assert.deepEqual(result.pageNumbers, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
  assert.equal(result.sections[0].endPage, 12)
  assert.equal(result.truncated, true)
})

test('APIへはページ番号と本文だけを送る', () => {
  assert.deepEqual(toApiPageTexts([{ page: 2, text: 'body', characterCount: 4 }]), [{ page: 2, text: 'body' }])
})

test('一括確認は表示中タブの候補だけを確認する', () => {
  const map = {
    nodes: [{ id: 'n1', included: true, confirmationStatus: 'unconfirmed' }],
    edges: [{ id: 'e1', confirmationStatus: 'unconfirmed' }],
  }
  const nodesConfirmed = confirmCandidatesForTab(map, 'nodes')
  assert.equal(nodesConfirmed.nodes[0].confirmationStatus, 'confirmed')
  assert.equal(nodesConfirmed.edges[0].confirmationStatus, 'unconfirmed')
  const edgesConfirmed = confirmCandidatesForTab(map, 'edges')
  assert.equal(edgesConfirmed.nodes[0].confirmationStatus, 'unconfirmed')
  assert.equal(edgesConfirmed.edges[0].confirmationStatus, 'confirmed')
})

test('AI候補は未確認でPDF外前提を自動採用しない', () => {
  const graph = { nodes: [
    { id: 'external', title: '外部', canonicalName: '外部', aliases: [], type: 'concept', reason: 'r', relationToGoal: 'r', understandingLevel: '概要を説明できる', completionCriteria: 'c', importance: 'supporting', sourcePages: [], sourceSections: [], evidence: [{ page: null, section: null, description: 'outside' }], confidence: 'low', confirmationStatus: 'unconfirmed', included: true, sourceType: 'external-prerequisite-suggestion' },
    { id: 'goal', title: 'Goal', canonicalName: 'Goal', aliases: [], type: 'goal', reason: 'r', relationToGoal: 'goal', understandingLevel: '概要を説明できる', completionCriteria: 'c', importance: 'required', sourcePages: [2], sourceSections: ['S'], evidence: [{ page: 2, section: 'S', description: 'e' }], confidence: 'high', confirmationStatus: 'unconfirmed', included: true, sourceType: 'pdf-evidence' },
  ], edges: [], warnings: [] }
  const map = toCandidateMap(graph, { issues: [], summary: '', warnings: [] }, { metadata: { title: 'B', pageCount: 10 }, fileHash: 'x', extractionQuality: {} }, 'Goal', '概要を説明できる', [{ startPage: 2, endPage: 2, pages: [2] }])
  assert.equal(map.nodes[0].included, false)
  assert.equal(map.edges.length, 0)
  assert.deepEqual(validateLearningMap(map), [])
})

test('重複・自己ループ・複数目標を検出し、利用者のエッジ確認は許可する', () => {
  const node = { id: 'x', type: 'goal', importance: 'required', included: true, pdfPage: 1, sourcePages: [1], sourceType: 'pdf-evidence' }
  const map = { creationMethod: 'ai-concept-dependency', candidateStatus: 'review', pdf: { pageCount: 3 }, nodes: [node, { ...node }], edges: [{ id: 'e', sourceId: 'x', targetId: 'x', type: 'helpful', confirmationStatus: 'confirmed', relationKind: 'user-confirmed' }] }
  const errors = validateLearningMap(map)
  assert.ok(errors.some((item) => item.includes('ノードID重複')))
  assert.ok(errors.some((item) => item.includes('自己ループ')))
  assert.ok(errors.some((item) => item.includes('目標ノードが複数')))
  assert.ok(!errors.some((item) => item.includes('自動承認')))
})

test('未採用ノードを参照するAIエッジを除外して警告する', () => {
  const baseNode = { title: 'N', canonicalName: 'N', aliases: [], reason: 'r', relationToGoal: 'r', understandingLevel: '概要を説明できる', completionCriteria: 'c', importance: 'supporting', sourceSections: [], evidence: [], confidence: 'low', confirmationStatus: 'unconfirmed', included: true }
  const graph = {
    nodes: [
      { ...baseNode, id: 'external', type: 'concept', sourcePages: [], sourceType: 'external-prerequisite-suggestion' },
      { ...baseNode, id: 'goal', type: 'goal', importance: 'required', sourcePages: [2], sourceSections: ['S'], evidence: [{ page: 2, section: 'S', description: 'e' }], sourceType: 'pdf-evidence' },
    ],
    edges: [{ id: 'e1', sourceId: 'external', targetId: 'goal', type: 'helpful', rationale: 'r', evidencePages: [], confidence: 'low', confirmationStatus: 'unconfirmed', relationKind: 'ai-concept-dependency' }], warnings: [],
  }
  const map = toCandidateMap(graph, { issues: [], summary: '', warnings: [] }, { metadata: { title: 'B', pageCount: 10 }, fileHash: 'x', extractionQuality: {} }, 'Goal', '概要を説明できる', [])
  assert.deepEqual(map.edges, [])
  assert.match(map.generationWarnings[0], /e1/)
  assert.deepEqual(validateLearningMap(map), [])
})

test('AI元出力と送信済みページの限定抜粋を候補へ分離保存する', () => {
  const graph = { nodes: [{ id: 'goal', title: 'Goal', canonicalName: 'Goal', aliases: [], type: 'goal', reason: 'r', relationToGoal: 'r', understandingLevel: '概要を説明できる', completionCriteria: 'c', importance: 'required', sourcePages: [2], sourceSections: ['S'], evidence: [{ page: 2, section: 'S', description: 'AI説明' }], confidence: 'high', included: true, sourceType: 'pdf-evidence' }], edges: [], warnings: [] }
  const map = toCandidateMap(graph, { issues: [], summary: '' }, { metadata: { title: 'B', pageCount: 10 }, fileHash: 'x', extractionQuality: {} }, 'Goal', '概要を説明できる', [], { pageTexts: [{ page: 2, text: '送信した本文' }, { page: 3, text: '未引用ページ' }] })
  map.nodes[0].title = '利用者編集'
  assert.equal(map.originalAiOutput.nodes[0].title, 'Goal')
  assert.deepEqual(map.evidenceExcerpts, [{ page: 2, text: '送信した本文' }])
})
