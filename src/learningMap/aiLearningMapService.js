import { buildEvidenceExcerpts, createOriginalAiOutput } from './candidateAudit.js'

// macOSではlocalhostが::1 (IPv6)へ解決されることがある一方、
// Uvicornの既定待受は127.0.0.1 (IPv4) のため、開発時の接続先を明示する。
const API_BASE = import.meta.env?.VITE_LEARNING_MAP_API_URL || 'http://127.0.0.1:8000'

async function request(path, options = {}) {
  let response
  try {
    const headers = options.body ? { 'Content-Type': 'application/json', ...(options.headers ?? {}) } : options.headers
    response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new Error('AIバックエンドへ接続できません。起動状態またはCORS設定を確認してください。')
  }
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = Array.isArray(data?.detail)
      ? data.detail.map((item) => typeof item === 'string' ? item : `${item.loc?.slice(1).join('.') || 'request'}: ${item.msg || JSON.stringify(item)}`).join(' / ')
      : data?.detail
    if (response.status === 429) throw new Error('OpenAI APIの利用上限に達しました。時間をおいて再試行してください。')
    throw new Error(detail || `AI処理に失敗しました (${response.status})`)
  }
  return data
}

export function getAiAvailability(signal) { return request('/health', { method: 'GET', signal }) }
export function selectRelevantSections(payload, signal) { return request('/api/learning-map/select-sections', { method: 'POST', body: JSON.stringify(payload), signal }) }
export function generateLearningGraph(payload, signal) { return request('/api/learning-map/generate', { method: 'POST', body: JSON.stringify(payload), signal }) }
export function reviewLearningGraph(payload, signal) { return request('/api/learning-map/review', { method: 'POST', body: JSON.stringify(payload), signal }) }

export function toApiPageTexts(pages) {
  return pages.map(({ page, text }) => ({ page, text }))
}

export function confirmCandidatesForTab(map, tab) {
  const updatedAt = new Date().toISOString()
  if (tab === 'edges') {
    return { ...map, updatedAt, edges: map.edges.map((edge) => ({ ...edge, confirmationStatus: 'confirmed' })) }
  }
  return {
    ...map,
    updatedAt,
    nodes: map.nodes.map((node) => node.included === false ? node : { ...node, confirmationStatus: 'confirmed' }),
  }
}

export function normalizeSelectedSections(sections, pageCount, maxPages = 50) {
  const used = new Set(), normalized = []
  for (const section of sections) {
    const startPage = Math.max(1, Math.min(pageCount, section.startPage))
    const endPage = Math.max(startPage, Math.min(pageCount, section.endPage))
    const pages = []
    for (let page = startPage; page <= endPage && used.size < maxPages; page += 1) {
      if (!used.has(page)) { used.add(page); pages.push(page) }
    }
    if (pages.length) normalized.push({ ...section, startPage: pages[0], endPage: pages.at(-1), pages })
  }
  return { sections: normalized, pageNumbers: [...used].sort((a, b) => a - b), truncated: used.size === maxPages && sections.some((section) => section.endPage > Math.max(...used)) }
}

export function toCandidateMap(graph, review, inspection, goal, understandingLevel, sections, options = {}) {
  const now = typeof options === 'string' ? options : options.now ?? new Date().toISOString()
  const pageTexts = typeof options === 'string' ? [] : options.pageTexts ?? []
  const planningTiming = typeof options === 'string' ? {} : options.planningTiming ?? {}
  const nodes = graph.nodes.map((node) => ({
    ...node,
    relation: node.relationToGoal,
    level: node.understandingLevel || understandingLevel,
    completion: node.completionCriteria,
    status: 'notStarted', notes: '', references: '', checklist: {}, proofSteps: [], resolvedReviewIds: [], prerequisiteIds: [],
    pdfTitle: inspection.metadata.title,
    pdfPage: node.sourcePages[0] ?? null,
    section: node.sourceSections.join(' / '),
    extractionSource: node.sourceType === 'pdf-evidence' ? '利用者が確認したPDF抽出本文' : 'PDF外前提候補（未採用）',
    generationRationale: node.evidence.map((item) => `${item.page ? `p.${item.page}` : 'PDF外'} ${item.description}`).join(' / '),
    confirmationStatus: 'unconfirmed',
    included: node.sourceType === 'external-prerequisite-suggestion' ? false : node.included,
  }))
  const includedIds = new Set(nodes.filter((node) => node.included !== false).map((node) => node.id))
  const excludedEdges = graph.edges.filter((edge) => !includedIds.has(edge.sourceId) || !includedIds.has(edge.targetId))
  return {
    id: `ai-learning-map-${Date.now()}`, name: goal, goal, sourceType: 'ai-generated-candidate', sourceLabel: 'AI生成候補（未確認）', creationMethod: 'ai-concept-dependency',
    pdf: { ...inspection.metadata, fileHash: inspection.fileHash, extractionQuality: inspection.extractionQuality },
    selectedSections: sections, nodes,
    edges: graph.edges.filter((edge) => includedIds.has(edge.sourceId) && includedIds.has(edge.targetId)).map((edge) => ({ ...edge, confirmationStatus: 'unconfirmed', relationKind: 'ai-concept-dependency' })),
    aiReview: { ...review, issues: (review.issues ?? []).map((issue) => ({ ...issue, resolutionStatus: 'unresolved', resolutionReason: '', resolvedAt: null })) },
    originalAiOutput: createOriginalAiOutput(graph, review), modificationHistory: [],
    evidenceExcerpts: buildEvidenceExcerpts(graph.nodes, graph.edges, pageTexts), planningTiming,
    generationWarnings: [...graph.warnings, ...(excludedEdges.length ? [`未採用または存在しないノードを参照する依存関係を除外: ${excludedEdges.map((edge) => edge.id).join(', ')}`] : [])],
    createdAt: now, updatedAt: now, candidateStatus: 'review',
  }
}
