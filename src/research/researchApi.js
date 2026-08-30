const QUERY_ENDPOINT = '/api/research/query'

function isFiniteNumber(value) { return typeof value === 'number' && Number.isFinite(value) }

export function validateCitation(value) {
  if (!value || !Number.isInteger(value.number) || value.number < 1) throw new Error('引用番号が不正です。')
  for (const key of ['documentId', 'documentTitle', 'documentVersion', 'chunkId', 'text', 'retrievalMethod']) {
    if (typeof value[key] !== 'string' || !value[key]) throw new Error(`引用の${key}が不正です。`)
  }
  if (!Number.isInteger(value.pageNumber) || value.pageNumber < 1 || !isFiniteNumber(value.score)) throw new Error('引用位置またはスコアが不正です。')
  return { ...value, sourceUrl: typeof value.sourceUrl === 'string' ? value.sourceUrl : null, ocrDerived: value.ocrDerived === true }
}

export function validateResearchResponse(value) {
  if (!value || !['success', 'no_evidence'].includes(value.status) || typeof value.answer !== 'string') throw new Error('検索バックエンドから不正な応答を受信しました。')
  if (!Array.isArray(value.citations)) throw new Error('引用一覧が不正です。')
  const citations = value.citations.map(validateCitation)
  const numbers = new Set(citations.map((item) => item.number))
  for (const match of value.answer.matchAll(/\[(\d+)\]/g)) {
    if (!numbers.has(Number(match[1]))) throw new Error('回答が存在しない引用を参照しています。')
  }
  return { ...value, citations }
}

export async function queryResearch({ question, mode, signal }) {
  const response = await fetch(QUERY_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, mode, retrieval: 'hybrid', rerank: true, topK: 3 }),
    signal,
  }).catch((error) => {
    if (error.name === 'AbortError') throw error
    throw new Error('検索サービスへ接続できません。両方のローカルサーバーを確認してください。')
  })
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    if (response.status === 408 || response.status === 504) throw new Error('検索がタイムアウトしました。再試行してください。')
    if (response.status === 401 || response.status === 403) throw new Error('検索サービスの認証に失敗しました。')
    throw new Error(payload?.error?.message || '検索・回答処理に失敗しました。')
  }
  return validateResearchResponse(payload)
}
