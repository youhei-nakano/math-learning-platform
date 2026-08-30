import test from 'node:test'
import assert from 'node:assert/strict'
import { addLearningNode, deleteLearningNode, deserializeLearningMap, duplicateLearningNode, normalizeNodeNotes, serializeLearningMap } from '../src/learningMap/mapNodeOperations.js'
import { createLinearAlgebraCandidateMap } from '../src/learningMap/linearAlgebraData.js'
import { migrateLearningMaps, saveLearningMaps } from '../src/learningMap/mapStore.js'

test('ノードごとにメモを独立して作成・更新できる', () => {
  const map = createLinearAlgebraCandidateMap()
  const nodes = map.nodes.map((node, index) => ({ ...node, notes: index === 0 ? 'first' : index === 1 ? 'second' : node.notes }))
  assert.equal(nodes[0].notes, 'first')
  assert.equal(nodes[1].notes, 'second')
})

test('新規ノードは空メモ、複製ノードは元メモを保持する', () => {
  const map = createLinearAlgebraCandidateMap()
  map.nodes[0].notes = '複製する $A^T=A$\n<script>text only</script>'
  const added = addLearningNode(map, 'new-id', '2026-01-01T00:00:00.000Z')
  assert.equal(added.node.notes, '')
  const duplicated = duplicateLearningNode(added.map, map.nodes[0].id, 'copy-id', '2026-01-01T00:00:01.000Z')
  assert.equal(duplicated.node.notes, map.nodes[0].notes)
  assert.notEqual(duplicated.node.id, map.nodes[0].id)
})

test('ノード削除でメモを含むノードと接続エッジを同時に除去する', () => {
  const map = createLinearAlgebraCandidateMap()
  const id = 'matrix-product'
  const deleted = deleteLearningNode(map, id)
  assert.ok(!deleted.nodes.some((node) => node.id === id))
  assert.ok(!deleted.edges.some((edge) => edge.sourceId === id || edge.targetId === id))
})

test('古いマップの欠落メモを空文字へ移行する', () => {
  const migrated = migrateLearningMaps({ version: 3, activeMapId: 'old', maps: [{ id: 'old', nodes: [{ id: 'n' }], edges: [] }] }, null)
  assert.equal(migrated.version, 4)
  assert.equal(migrated.maps[0].nodes[0].notes, '')
  assert.equal(normalizeNodeNotes({ nodes: [{ id: 'n', notes: null }] }).nodes[0].notes, '')
})

test('長文・改行・数式・特殊文字・空文字をJSON書き出しと読込で保持する', () => {
  const map = createLinearAlgebraCandidateMap('2026-01-01T00:00:00.000Z')
  const value = `${'長文'.repeat(5000)}\n$$A^T=A$$\n<&>\n`
  map.nodes[0].notes = value
  map.nodes[1].notes = ''
  const restored = deserializeLearningMap(serializeLearningMap(map), '2026-01-02T00:00:00.000Z')
  assert.equal(restored.nodes[0].notes, value)
  assert.equal(restored.nodes[1].notes, '')
})

test('保存失敗を呼び出し側へ通知して再試行可能にする', () => {
  const storage = { setItem() { throw new Error('quota') } }
  assert.throws(() => saveLearningMaps({ maps: [] }, storage), /quota/)
  const retryStorage = { calls: 0, setItem() { this.calls += 1 } }
  saveLearningMaps({ maps: [] }, retryStorage)
  assert.equal(retryStorage.calls, 1)
})
