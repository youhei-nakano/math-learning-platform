const compact = (value) => String(value ?? '')
  .normalize('NFKC')
  .toLocaleLowerCase('ja-JP')
  .replace(/[\s\p{P}\p{S}]+/gu, '')

export function normalizeConceptName(value) {
  return compact(value)
}

function names(node) {
  return [...new Set([node.canonicalName, node.title, ...(node.aliases ?? [])].map(compact).filter(Boolean))]
}

function pages(node) {
  return [...new Set([...(node.sourcePages ?? []), node.pdfPage].map(Number).filter(Number.isInteger))]
}

function sections(node) {
  return [...new Set([...(node.sourceSections ?? []), node.section].map(compact).filter(Boolean))]
}

const intersects = (left, right) => left.some((value) => right.includes(value))
const ratio = (top, bottom) => bottom ? top / bottom : 0

export function matchConcepts(candidateNodes, baselineNodes) {
  const candidates = candidateNodes.filter((node) => node.included !== false)
  const baseline = baselineNodes.filter((node) => node.included !== false)
  const unmatchedCandidateIds = new Set(candidates.map((node) => node.id))
  const matchedBaselineIds = new Set()
  const matches = []

  for (const candidate of candidates) {
    const exact = baseline.filter((item) => !matchedBaselineIds.has(item.id) && intersects(names(candidate), names(item)))
    if (exact.length === 1) {
      const base = exact[0]
      matchedBaselineIds.add(base.id); unmatchedCandidateIds.delete(candidate.id)
      matches.push({ candidate, baseline: base, method: 'canonical-or-alias', pageOverlap: intersects(pages(candidate), pages(base)), sectionOverlap: intersects(sections(candidate), sections(base)) })
    }
  }

  const needsHumanMatch = []
  for (const candidate of candidates.filter((item) => unmatchedCandidateIds.has(item.id))) {
    const possible = baseline.filter((item) => !matchedBaselineIds.has(item.id)).filter((item) => {
      const candidatePages = pages(candidate), baselinePages = pages(item)
      const pageNear = candidatePages.some((page) => baselinePages.some((basePage) => Math.abs(page - basePage) <= 1))
      const sectionOverlap = intersects(sections(candidate), sections(item))
      const left = names(candidate)[0] ?? '', right = names(item)[0] ?? ''
      const titleContainment = left.length >= 4 && right.length >= 4 && (left.includes(right) || right.includes(left))
      return titleContainment || (pageNear && sectionOverlap)
    })
    if (possible.length) needsHumanMatch.push({ candidate, possibleBaselines: possible, reason: '名称の完全一致がなく、ページ・節または部分名称だけが近いため自動一致していません。' })
  }

  return {
    matches,
    missingBaseline: baseline.filter((item) => !matchedBaselineIds.has(item.id)),
    candidateOnly: candidates.filter((item) => unmatchedCandidateIds.has(item.id)),
    needsHumanMatch,
  }
}

function cycleCount(nodes, edges) {
  const ids = new Set(nodes.filter((node) => node.included !== false).map((node) => node.id))
  const adjacency = new Map([...ids].map((id) => [id, []]))
  edges.forEach((edge) => { if (ids.has(edge.sourceId) && ids.has(edge.targetId)) adjacency.get(edge.sourceId).push(edge.targetId) })
  const visiting = new Set(), visited = new Set(), cycles = new Set()
  function visit(id, path) {
    if (visiting.has(id)) { cycles.add(path.slice(path.indexOf(id)).sort().join('|')); return }
    if (visited.has(id)) return
    visiting.add(id)
    for (const next of adjacency.get(id) ?? []) visit(next, [...path, next])
    visiting.delete(id); visited.add(id)
  }
  ids.forEach((id) => visit(id, [id]))
  return cycles.size
}

export function evaluateLearningMap(candidateMap, baselineMap) {
  const concept = matchConcepts(candidateMap.nodes ?? [], baselineMap.nodes ?? [])
  const idMap = new Map(concept.matches.map((match) => [match.candidate.id, match.baseline.id]))
  const baselineEdges = baselineMap.edges ?? []
  const candidateEdges = (candidateMap.edges ?? []).filter((edge) => {
    const included = new Set((candidateMap.nodes ?? []).filter((node) => node.included !== false).map((node) => node.id))
    return included.has(edge.sourceId) && included.has(edge.targetId)
  })
  const baselineEdgeKeys = new Set(baselineEdges.map((edge) => `${edge.sourceId}->${edge.targetId}`))
  const matchedEdges = [], unmatchedEdges = [], matchedBaselineEdgeKeys = new Set()
  for (const edge of candidateEdges) {
    const sourceId = idMap.get(edge.sourceId), targetId = idMap.get(edge.targetId)
    const key = sourceId && targetId ? `${sourceId}->${targetId}` : null
    if (key && baselineEdgeKeys.has(key)) { matchedEdges.push({ candidate: edge, baseline: baselineEdges.find((item) => `${item.sourceId}->${item.targetId}` === key) }); matchedBaselineEdgeKeys.add(key) }
    else unmatchedEdges.push(edge)
  }
  const missingEdges = baselineEdges.filter((edge) => !matchedBaselineEdgeKeys.has(`${edge.sourceId}->${edge.targetId}`))
  const requiredBaseline = (baselineMap.nodes ?? []).filter((node) => node.included !== false && node.importance === 'required')
  const matchedRequired = concept.matches.filter((match) => match.baseline.importance === 'required')
  const pageComparable = concept.matches.filter((match) => pages(match.candidate).length && pages(match.baseline).length)
  const pageMatches = pageComparable.filter((match) => match.pageOverlap)
  const initialNodes = candidateMap.originalAiOutput?.nodes ?? candidateMap.nodes ?? []
  return {
    metrics: {
      requiredConceptRecall: ratio(matchedRequired.length, requiredBaseline.length),
      conceptPrecision: ratio(concept.matches.length, (candidateMap.nodes ?? []).filter((node) => node.included !== false).length),
      unnecessaryConceptRate: ratio(concept.candidateOnly.length, (candidateMap.nodes ?? []).filter((node) => node.included !== false).length),
      dependencyPrecision: ratio(matchedEdges.length, candidateEdges.length),
      dependencyRecall: ratio(matchedEdges.length, baselineEdges.length),
      sourcePageAccuracy: ratio(pageMatches.length, pageComparable.length),
      cycleCount: cycleCount(candidateMap.nodes ?? [], candidateEdges),
      externalPrerequisiteCount: (candidateMap.nodes ?? []).filter((node) => node.sourceType === 'external-prerequisite-suggestion').length,
      aiNodeCount: initialNodes.length,
      humanCorrectionCount: (candidateMap.modificationHistory ?? []).length,
    },
    ...concept,
    matchedEdges, unmatchedEdges, missingEdges,
    pageMismatches: pageComparable.filter((match) => !match.pageOverlap),
  }
}
