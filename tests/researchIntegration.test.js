import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import { validateCitation, validateResearchResponse } from '../src/research/researchApi.js'

const citation = { number: 1, documentId: 'doc', documentTitle: '資料', documentVersion: 'a'.repeat(64), pageNumber: 2, chunkId: 'doc:a:2:0', text: '日本語 $x^2$ <script>unsafe()</script>', score: 0.9, sourceUrl: null, retrievalMethod: 'hybrid+rerank', ocrDerived: false }

test('正常な検索応答で回答と文書・ページ・チャンクを対応付ける', () => {
  const result = validateResearchResponse({ status: 'success', answer: '根拠 [1]', citations: [citation] })
  assert.equal(result.citations[0].pageNumber, 2)
  assert.equal(result.citations[0].chunkId, 'doc:a:2:0')
})

test('回答中の存在しない引用番号を拒否する', () => {
  assert.throws(() => validateResearchResponse({ status: 'success', answer: '根拠 [2]', citations: [citation] }), /存在しない引用/)
})

test('不正なページと空の文書IDを拒否する', () => {
  assert.throws(() => validateCitation({ ...citation, pageNumber: 0 }), /引用位置/)
  assert.throws(() => validateCitation({ ...citation, documentId: '' }), /documentId/)
})

test('根拠0件の明示応答を許可する', () => {
  const result = validateResearchResponse({ status: 'no_evidence', answer: '資料内では確認できません。', citations: [] })
  assert.equal(result.citations.length, 0)
})

test('特殊文字は文字列のまま保持しHTMLへ変換しない', () => {
  assert.equal(validateCitation(citation).text, '日本語 $x^2$ <script>unsafe()</script>')
})

test('実LLM未実行をゼロ件の実測として表示しない', async () => {
  const status = JSON.parse(await readFile(new URL('../public/live-evaluation-status.json', import.meta.url), 'utf8'))
  assert.equal(status.status, 'not_run')
  assert.match(status.reason, /未実行/)
  assert.deepEqual(status.experiments, [])
})
