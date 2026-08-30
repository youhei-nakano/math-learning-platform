const JAPANESE_RE = /[\u3040-\u30ff\u3400-\u9fff]/g
const LATIN_RE = /[A-Za-z]/g
const DIGIT_RE = /[0-9]/g
const REPLACEMENT_RE = /[\ufffd]/g
const SUSPICIOUS_RE = /[^\s\u3040-\u30ff\u3400-\u9fffA-Za-z0-9.,:;!?()[\]{}+\-=×÷∑∫√∞≤≥≠≈∈∉⊂⊆∪∩∀∃→←↔α-ωΑ-Ω\u3000-\u303f]/g

const ratio = (count, total) => total ? Number((count / total).toFixed(3)) : 0

export function analyzeExtractedText(text, pdfPage) {
  const value = text ?? ''
  const nonWhitespace = value.replace(/\s/g, '')
  const total = nonWhitespace.length
  const controlCount = [...value].filter((character) => { const code = character.charCodeAt(0); return (code < 32 && !['\n', '\r', '\t'].includes(character)) || code === 127 }).length
  const replacementCount = (value.match(REPLACEMENT_RE) ?? []).length
  const suspiciousCount = (nonWhitespace.match(SUSPICIOUS_RE) ?? []).length
  const metrics = {
    pdfPage, characterCount: value.length, nonWhitespaceCount: total,
    japaneseRatio: ratio((nonWhitespace.match(JAPANESE_RE) ?? []).length, total),
    latinRatio: ratio((nonWhitespace.match(LATIN_RE) ?? []).length, total),
    digitRatio: ratio((nonWhitespace.match(DIGIT_RE) ?? []).length, total),
    controlRatio: ratio(controlCount, Math.max(value.length, 1)),
    suspiciousRatio: ratio(suspiciousCount + replacementCount, Math.max(total, 1)),
  }
  const reasons = []
  if (total < 20) reasons.push('抽出テキストがほぼ空です')
  if (metrics.controlRatio > 0.03) reasons.push('制御文字が多く含まれます')
  if (metrics.suspiciousRatio > 0.3) reasons.push('意味のない記号または文字化けの可能性があります')
  return { ...metrics, success: total >= 20, suspectedGarbled: reasons.length > 0, reasons }
}

export function classifyTextExtraction(samples) {
  if (!samples?.length) return { quality: '判定不能', usableRate: 0, rationale: 'サンプルを取得できませんでした。' }
  const successful = samples.filter((sample) => sample.success)
  const clean = successful.filter((sample) => !sample.suspectedGarbled)
  const usableRate = Number((successful.length / samples.length).toFixed(2))
  if (!successful.length) return { quality: 'OCRが必要', usableRate, rationale: 'すべてのサンプルページで本文テキストを取得できませんでした。' }
  if (clean.length === samples.length) return { quality: '良好', usableRate, rationale: 'すべてのサンプルページから十分なテキストを取得できました。' }
  if (clean.length || usableRate >= 0.6) return { quality: '一部利用可能', usableRate, rationale: 'テキストは取得できましたが、一部ページに空文字または文字化けの疑いがあります。' }
  return { quality: '低品質', usableRate, rationale: '一部のテキストは取得できますが、文字化けまたは抽出不足が多く見られます。' }
}

export function estimateLanguage(samples) {
  const japanese = samples.reduce((sum, sample) => sum + sample.japaneseRatio, 0)
  const latin = samples.reduce((sum, sample) => sum + sample.latinRatio, 0)
  if (japanese > latin && japanese > 0.1) return ['日本語']
  if (latin > 0.2) return samples.some((sample) => sample.suspectedGarbled) ? ['英語', '判定不能'] : ['英語']
  return ['判定不能']
}

export function getSamplePageNumbers(pageCount, firstBodyPage = 1, goalPage = null) {
  const candidates = [firstBodyPage, Math.ceil(pageCount * 0.25), Math.ceil(pageCount * 0.5), Math.ceil(pageCount * 0.75), pageCount, goalPage]
  return [...new Set(candidates.filter((page) => Number.isInteger(page) && page >= 1 && page <= pageCount))]
}

export function validatePdfSelection(file) {
  if (!file) return 'PDFを選択してください。'
  if (file.type !== 'application/pdf' && !file.name?.toLowerCase().endsWith('.pdf')) return 'PDF以外のファイルは解析できません。'
  if (file.size > 100 * 1024 * 1024) return '100MBを超えるPDFはVersion 1の対象外です。'
  return null
}

export function flattenOutline(outline) {
  const result = []
  function walk(items) { for (const item of items ?? []) { result.push(item); walk(item.children) } }
  walk(outline)
  return result
}

export function generateDocumentStructureMap(inspection, options, now = new Date().toISOString()) {
  const { goalOutlineId, understandingLevel = '概要を説明できる', previousRange = 8, maxNodes = 20 } = options
  const flat = flattenOutline(inspection.outline)
  const targetIndex = flat.findIndex((item) => item.id === goalOutlineId)
  if (targetIndex < 0) throw new Error('選択した到達目標がアウトラインにありません。')
  const target = flat[targetIndex]
  const ids = new Set([target.id])
  let parentId = target.parentId
  while (parentId) { ids.add(parentId); parentId = flat.find((item) => item.id === parentId)?.parentId }
  function addDescendants(item) { for (const child of item.children ?? []) { ids.add(child.id); addDescendants(child) } }
  addDescendants(target)
  for (let i = Math.max(0, targetIndex - previousRange); i < targetIndex; i += 1) ids.add(flat[i].id)
  let selected = flat.filter((item) => ids.has(item.id))
  if (selected.length > maxNodes) {
    const priority = [target, ...flat.filter((item) => ids.has(item.id) && item.id !== target.id).sort((a, b) => Math.abs(flat.indexOf(a) - targetIndex) - Math.abs(flat.indexOf(b) - targetIndex))]
    selected = priority.slice(0, maxNodes).sort((a, b) => flat.indexOf(a) - flat.indexOf(b))
  }
  const selectedIds = new Set(selected.map((item) => item.id))
  const nodes = selected.map((item) => ({
    id: `outline-node-${item.id}`, title: item.title, type: item.id === target.id ? 'goal' : 'section',
    reason: '', relation: item.id === target.id ? '選択した到達目標。' : '文書構造上の関連候補。数学的な前提関係は未確認です。',
    level: understandingLevel, completion: '', prerequisiteIds: [], status: 'notStarted', notes: '', references: '', checklist: {}, proofSteps: [], resolvedReviewIds: [],
    included: true, importance: item.id === target.id ? 'required' : 'recommended', confirmationStatus: 'unconfirmed',
    pdfTitle: inspection.metadata.title, pdfPage: item.pdfPage, pageLabel: item.pageLabel, section: item.title,
    extractionSource: 'PDF内部アウトライン', confidence: item.pdfPage ? 'high' : 'low',
    generationRationale: item.id === target.id ? '利用者が到達目標として選択。' : '選択目標の親・子または指定範囲内の前項目。', documentOutlineId: item.id,
  }))
  const edges = selected.filter((item) => item.parentId && selectedIds.has(item.parentId)).map((item) => ({
    id: `outline-edge-${item.parentId}-${item.id}`, sourceId: `outline-node-${item.parentId}`, targetId: `outline-node-${item.id}`,
    type: '文書構造上の親子', rationale: 'PDFアウトラインの親子関係。数学的依存関係ではありません。', confirmationStatus: 'unconfirmed', relationKind: 'document-structure',
  }))
  return {
    id: `document-structure-${Date.now()}`, name: target.title, goal: `${target.title}を理解する`, sourceType: 'document-structure', sourceLabel: '文書構造マップ候補',
    creationMethod: 'document-structure', pdf: { ...inspection.metadata, outline: inspection.outline, extractionQuality: inspection.extractionQuality, fileHash: inspection.fileHash },
    nodes, edges, createdAt: now, updatedAt: now, candidateStatus: 'review',
  }
}

export function generateConceptDependencyCandidate() {
  return { status: 'not-implemented', message: 'AIによる概念依存マップ生成はVersion 1では未接続です。' }
}
