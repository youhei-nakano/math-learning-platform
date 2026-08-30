const clone = (value) => typeof structuredClone === 'function' ? structuredClone(value) : JSON.parse(JSON.stringify(value))

export function createOriginalAiOutput(graph, review) {
  return clone({ nodes: graph.nodes ?? [], edges: graph.edges ?? [], warnings: graph.warnings ?? [], review })
}

export function recordModification(map, change, now = new Date().toISOString()) {
  return { ...map, updatedAt: now, modificationHistory: [...(map.modificationHistory ?? []), { id: `change-${crypto.randomUUID()}`, changedAt: now, ...clone(change) }] }
}

export function calculatePlanningTiming(timing = {}) {
  const diff = (start, end) => start && end ? Math.max(0, new Date(end) - new Date(start)) : null
  return {
    ...timing,
    aiProcessingMs: timing.aiProcessingMs ?? diff(timing.aiCandidateGenerationStartedAt, timing.aiCandidateGenerationCompletedAt),
    humanReviewMs: diff(timing.humanReviewStartedAt, timing.learningMapFinalizedAt),
    totalPlanningMs: diff(timing.pdfAnalysisStartedAt ?? timing.aiCandidateGenerationStartedAt, timing.learningMapFinalizedAt),
  }
}

export function buildEvidenceExcerpts(nodes, edges, pageTexts, maxCharactersPerPage = 900, maxPages = 30) {
  const cited = new Set([
    ...nodes.flatMap((node) => node.sourcePages ?? []),
    ...edges.flatMap((edge) => edge.evidencePages ?? []),
  ].map(Number).filter(Number.isInteger))
  return pageTexts.filter((item) => cited.has(item.page)).slice(0, maxPages).map((item) => ({ page: item.page, text: String(item.text ?? '').trim().slice(0, maxCharactersPerPage) }))
}
