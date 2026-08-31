import * as pdfjsLib from 'pdfjs-dist'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import { analyzeExtractedText, classifyTextExtraction, estimateLanguage, getSamplePageNumbers, validatePdfSelection } from './pdfAnalysisCore'

pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrl
const sessions = new WeakMap()

async function openPdf(file, signal) {
  let session = sessions.get(file)
  if (!session) {
    session = (async () => {
      const buffer = await file.arrayBuffer()
      const assetBase = import.meta.env.BASE_URL
      const loadingTask = pdfjsLib.getDocument({ data: new Uint8Array(buffer), isEvalSupported: false, cMapUrl: `${assetBase}pdfjs/cmaps/`, cMapPacked: true, standardFontDataUrl: `${assetBase}pdfjs/standard_fonts/` })
      try { return { buffer, pdf: await loadingTask.promise, loadingTask } }
      catch (error) { sessions.delete(file); throw error }
    })()
    sessions.set(file, session)
  }
  if (signal?.aborted) throw new DOMException('解析をキャンセルしました。', 'AbortError')
  return session
}

export async function releasePdfSession(file) {
  const session = sessions.get(file)
  sessions.delete(file)
  if (session) (await session).loadingTask.destroy()
}

async function sha256(buffer) {
  const digest = await crypto.subtle.digest('SHA-256', buffer)
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('')
}

async function resolveDestination(pdf, destination) {
  try {
    const explicit = typeof destination === 'string' ? await pdf.getDestination(destination) : destination
    if (!explicit?.[0]) return null
    return await pdf.getPageIndex(explicit[0]) + 1
  } catch { return null }
}

async function normalizeOutline(pdf, outline, pageLabels) {
  async function walk(items, level = 0, parentId = null, path = 'root') {
    return Promise.all((items ?? []).map(async (item, index) => {
      const id = `outline-${path}-${index}`
      const pdfPage = await resolveDestination(pdf, item.dest)
      const children = await walk(item.items, level + 1, id, `${path}-${index}`)
      return { id, title: item.title?.trim() || '無題', level, parentId, children, destination: typeof item.dest === 'string' ? item.dest : null, pdfPage, pageLabel: pdfPage ? pageLabels?.[pdfPage - 1] ?? String(pdfPage) : null }
    }))
  }
  return walk(outline)
}

export async function inspectPdfWithPdfJs(file, { signal, onProgress, goalPage = null } = {}) {
  const selectionError = validatePdfSelection(file)
  if (selectionError) throw new Error(selectionError)
  onProgress?.('PDFを読み込んでいます…')
  const { buffer, pdf } = await openPdf(file, signal)
  const fileHash = await sha256(buffer)
  try {
    if (!pdf.numPages) throw new Error('ページ数が0のPDFです。')
    onProgress?.('メタデータとアウトラインを解析しています…')
    const [metadataResult, rawOutline, pageLabels] = await Promise.all([pdf.getMetadata(), pdf.getOutline(), pdf.getPageLabels()])
    const outline = await normalizeOutline(pdf, rawOutline, pageLabels)
    const flatOutline = []
    const collect = (items) => items.forEach((item) => { flatOutline.push(item); collect(item.children) })
    collect(outline)
    const resolvedOutlineCount = flatOutline.filter((item) => item.pdfPage).length
    const firstBodyPage = flatOutline.find((item) => item.pdfPage)?.pdfPage ?? 1
    const samplePages = getSamplePageNumbers(pdf.numPages, firstBodyPage, goalPage)
    const samples = []
    onProgress?.('サンプルページのテキスト品質を確認しています…')
    await Promise.all(samplePages.map(async (pageNumber) => {
      if (signal?.aborted) throw new DOMException('解析をキャンセルしました。', 'AbortError')
      try {
        const page = await pdf.getPage(pageNumber)
        const content = await page.getTextContent()
        samples.push(analyzeExtractedText(content.items.map((item) => item.str ?? '').join(' '), pageNumber))
        page.cleanup()
      } catch { samples.push(analyzeExtractedText('', pageNumber)) }
    }))
    samples.sort((a, b) => a.page - b.page)
    const extractionQuality = classifyTextExtraction(samples)
    const info = metadataResult.info ?? {}
    const metadata = {
      fileName: file.name, fileSize: file.size, title: metadataResult.metadata?.get('dc:title') || info.Title || '未設定', author: metadataResult.metadata?.get('dc:creator') || info.Author || '未設定',
      pageCount: pdf.numPages, pdfVersion: info.PDFFormatVersion || '取得不能', outlineAvailable: outline.length > 0, pageLabels: pageLabels ?? null,
    }
    const unsupportedReasons = []
    if (!outline.length) unsupportedReasons.push('アウトラインがありません。')
    if (outline.length && resolvedOutlineCount === 0) unsupportedReasons.push('アウトラインの遷移先ページを解決できません。')
    if (!samples.some((sample) => sample.success)) unsupportedReasons.push('本文テキストを取得できません。スキャンPDFの可能性があります。')
    const warnings = [...new Set(samples.flatMap((sample) => sample.reasons))]
    if (extractionQuality.quality !== '良好') warnings.push(extractionQuality.rationale)
    return { supported: unsupportedReasons.length === 0, unsupportedReasons, metadata, outline, samples, extractionQuality, languageCandidates: estimateLanguage(samples), warnings, fileHash, resolvedOutlineCount, rawOutlineCount: flatOutline.length }
  } catch (error) {
    if (signal?.aborted || error?.name === 'AbortError') throw new DOMException('解析をキャンセルしました。', 'AbortError')
    if (error?.name === 'PasswordException') throw new Error('暗号化またはパスワード保護されたPDFはVersion 1では解析できません。')
    throw new Error(`PDFを解析できませんでした。ファイルが破損または未対応形式の可能性があります。${error?.message ? ` (${error.message})` : ''}`)
  }
}

export async function extractPdfPagesWithPdfJs(file, pageNumbers, { signal, onProgress } = {}) {
  const uniquePages = [...new Set(pageNumbers)].sort((a, b) => a - b)
  if (!uniquePages.length) throw new Error('抽出対象ページがありません。')
  if (uniquePages.length > 50) throw new Error('AIへ送信できるページは最大50ページです。')
  const { pdf } = await openPdf(file, signal)
  try {
    if (uniquePages.some((page) => page < 1 || page > pdf.numPages)) throw new Error('選択されたページ範囲がPDFの範囲外です。')
    let completed = 0
    const extractPage = async (pdfPage) => {
      if (signal?.aborted) throw new DOMException('抽出をキャンセルしました。', 'AbortError')
      const page = await pdf.getPage(pdfPage)
      try {
        const content = await page.getTextContent()
        const text = content.items.map((item) => item.str ?? '').join(' ').replace(/\s+/g, ' ').trim()
        const quality = analyzeExtractedText(text, pdfPage)
        return quality.success && !quality.suspectedGarbled ? { page: pdfPage, text, characterCount: text.length } : null
      } finally {
        page.cleanup(); completed += 1
        onProgress?.(`対象ページを抽出中 (${completed}/${uniquePages.length})`)
      }
    }
    const pages = []
    let cursor = 0
    const workers = Array.from({ length: Math.min(4, uniquePages.length) }, async () => {
      while (cursor < uniquePages.length) {
        const index = cursor++
        const page = await extractPage(uniquePages[index])
        if (page) pages.push(page)
      }
    })
    await Promise.all(workers)
    pages.sort((a, b) => a.page - b.page)
    if (!pages.length) throw new Error('選択範囲から送信可能な本文を抽出できませんでした。文字化けまたはスキャンPDFの可能性があります。')
    return { pages, skippedPages: uniquePages.filter((number) => !pages.some((page) => page.page === number)) }
  } catch (error) {
    if (signal?.aborted || error?.name === 'AbortError') throw new DOMException('抽出をキャンセルしました。', 'AbortError')
    throw error
  }
}
