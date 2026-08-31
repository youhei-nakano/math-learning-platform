import test from 'node:test'
import assert from 'node:assert/strict'
import { LINEAR_ALGEBRA_NODES, createLinearAlgebraCandidateMap } from '../src/learningMap/linearAlgebraData.js'
import { migrateLearningMaps } from '../src/learningMap/mapStore.js'
import { validateLearningMap } from '../src/learningMap/mapValidation.js'
import { getReviewedConceptMap, REVIEWED_LINEAR_ALGEBRA_SHA256 } from '../src/learningMap/pdfImportService.js'
import { analyzeExtractedText, classifyTextExtraction, generateDocumentStructureMap, validatePdfSelection } from '../src/learningMap/pdfAnalysisCore.js'

test('既存v1の学習状態とメモをFloerデモへ移行する', () => {
  const migrated = migrateLearningMaps(null, { nodes: { intersection: { status: 'understood', notes: 'legacy memo' } } }, '2026-01-01T00:00:00.000Z')
  assert.equal(migrated.version, 4)
  const node = migrated.maps[0].nodes.find((item) => item.id === 'intersection')
  assert.equal(node.status, 'understood')
  assert.equal(node.notes, 'legacy memo')
})

test('v2保存データを内容を失わず現行形式へ移行する', () => {
  const oldMap = { id: 'old', nodes: [{ id: 'n', notes: '保持する' }], edges: [], aiReview: { issues: [{ id: 'i', severity: 'high' }] } }
  const migrated = migrateLearningMaps({ version: 2, activeMapId: 'old', maps: [oldMap] }, null)
  assert.equal(migrated.version, 4)
  assert.equal(migrated.maps[0].nodes[0].notes, '保持する')
  assert.deepEqual(migrated.maps[0].modificationHistory, [])
  assert.equal(migrated.maps[0].aiReview.issues[0].resolutionStatus, 'unresolved')
})

test('既知ハッシュに対してレビュー済み22ノード候補を返す', () => {
  const map = getReviewedConceptMap({ fileHash: REVIEWED_LINEAR_ALGEBRA_SHA256, extractionQuality: { quality: '一部利用可能' }, outline: [] })
  assert.equal(map.nodes.length, 22)
  assert.ok(map.nodes.some((node) => node.type === 'goal'))
  assert.ok(map.edges.every((edge) => edge.confirmationStatus === 'unconfirmed'))
})

test('テキスト抽出品質を良好・OCR必要に分類する', () => {
  const good = analyzeExtractedText('Vector space basis theorem and example 123 '.repeat(8), 1)
  const empty = analyzeExtractedText('   ', 2)
  assert.equal(classifyTextExtraction([good]).quality, '良好')
  assert.equal(classifyTextExtraction([empty]).quality, 'OCRが必要')
})

test('PDF以外と100MB超のファイルを拒否する', () => {
  assert.match(validatePdfSelection({ name: 'notes.txt', type: 'text/plain', size: 10 }), /PDF以外/)
  assert.match(validatePdfSelection({ name: 'large.pdf', type: 'application/pdf', size: 101 * 1024 * 1024 }), /100MB/)
  assert.equal(validatePdfSelection({ name: 'notes.pdf', type: 'application/pdf', size: 1000 }), null)
})

test('選択目標を中心に最大数以内の文書構造マップを生成する', () => {
  const child = { id: 'same-1', title: '同じ節名', level: 1, parentId: 'chapter', pdfPage: 2, pageLabel: '2', children: [] }
  const child2 = { id: 'same-2', title: '同じ節名', level: 1, parentId: 'chapter', pdfPage: 3, pageLabel: '3', children: [] }
  const inspection = { metadata: { title: 'Test', pageCount: 5 }, outline: [{ id: 'chapter', title: 'Chapter', level: 0, parentId: null, pdfPage: 1, pageLabel: '1', children: [child, child2] }], extractionQuality: { quality: '良好' }, fileHash: 'abc' }
  const map = generateDocumentStructureMap(inspection, { goalOutlineId: 'same-2', maxNodes: 2, previousRange: 2 })
  assert.ok(map.nodes.length <= 2)
  assert.equal(new Set(map.nodes.map((node) => node.id)).size, map.nodes.length)
  assert.ok(map.edges.every((edge) => edge.confirmationStatus === 'unconfirmed' && edge.relationKind === 'document-structure'))
  assert.deepEqual(validateLearningMap(map), [])
})

test('全参照ページがPDF範囲内で、欠落ID・循環がない', () => {
  const map = createLinearAlgebraCandidateMap('2026-01-01T00:00:00.000Z')
  assert.ok(LINEAR_ALGEBRA_NODES.every((node) => node.pdfPage >= 1 && node.pdfPage <= 432))
  assert.deepEqual(validateLearningMap(map), [])
})

test('存在しない前提ノードと循環を検出する', () => {
  const map = createLinearAlgebraCandidateMap()
  const broken = { ...map, edges: [...map.edges, { id: 'missing', sourceId: 'missing-node', targetId: map.nodes[0].id }] }
  assert.ok(validateLearningMap(broken).some((error) => error.includes('存在しないノード')))
  const cyclic = { ...map, edges: [...map.edges, { id: 'cycle', sourceId: 'orthogonal-diagonalization', targetId: 'matrix-product' }] }
  assert.ok(validateLearningMap(cyclic).some((error) => error.includes('循環')))
})
