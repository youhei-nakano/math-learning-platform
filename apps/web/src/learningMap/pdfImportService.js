import { createLinearAlgebraCandidateMap } from './linearAlgebraData.js'
import { generateConceptDependencyCandidate, generateDocumentStructureMap } from './pdfAnalysisCore.js'

export const REVIEWED_LINEAR_ALGEBRA_SHA256 = 'b73df53a7a4bcb9c255c3f7eabd6ea2594db9f734d3351b8dc21a6cb1689c073'

export async function inspectPdf(file, options = {}) {
  const { inspectPdfWithPdfJs } = await import('./pdfjsAdapter.js')
  const inspection = await inspectPdfWithPdfJs(file, options)
  return { ...inspection, reviewedConceptMapAvailable: inspection.fileHash === REVIEWED_LINEAR_ALGEBRA_SHA256 }
}

export function extractDocumentStructure(inspection) {
  return { outline: inspection.outline, pageCount: inspection.metadata.pageCount, extractionQuality: inspection.extractionQuality }
}

export function generateDocumentStructureMapCandidate(inspection, options) {
  return generateDocumentStructureMap(inspection, options)
}

export function getReviewedConceptMap(inspection) {
  if (inspection.fileHash !== REVIEWED_LINEAR_ALGEBRA_SHA256) throw new Error('このPDFに対応するレビュー済み概念依存マップはありません。')
  const map = createLinearAlgebraCandidateMap()
  return { ...map, sourceType: 'known-reviewed-data', sourceLabel: 'レビュー済みの初期データ', creationMethod: 'known-reviewed-data', pdf: { ...map.pdf, fileHash: inspection.fileHash, extractionQuality: inspection.extractionQuality, outline: inspection.outline } }
}

export { generateConceptDependencyCandidate }

// 旧呼び出し名を残し、既存コードや保存済み操作との互換性を保つ。
export const inspectSelectedPdf = inspectPdf
