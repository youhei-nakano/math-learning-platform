import { useEffect, useMemo, useRef, useState } from 'react'
import { UNDERSTANDING_LEVELS } from '../learningMap/constants'
import { generateDocumentStructureMapCandidate, getReviewedConceptMap, inspectPdf } from '../learningMap/pdfImportService'
import { generateLearningGraph, getAiAvailability, normalizeSelectedSections, reviewLearningGraph, selectRelevantSections, toApiPageTexts, toCandidateMap } from '../learningMap/aiLearningMapService'

const flatten = (items) => items.flatMap((item) => [item, ...flatten(item.children ?? [])])
const formatBytes = (bytes) => bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.ceil(bytes / 1024)} KB`
const DEFAULT_AI_PAGE_LIMIT = 12

function OutlineTree({ items, selectedId, onSelect }) {
  return <ul className="outline-tree">{items.map((item) => <li key={item.id}><div className={`outline-item level-${item.level}`}><label><input type="radio" name="goal-outline" checked={selectedId === item.id} disabled={!item.pdfPage} onChange={() => onSelect(item.id)} /><span>{item.title}</span></label><em>{item.pdfPage ? `p.${item.pdfPage}` : 'ページ未解決'}</em></div>{item.children?.length > 0 && <details open={item.level < 1}><summary>{item.children.length}項目</summary><OutlineTree items={item.children} selectedId={selectedId} onSelect={onSelect} /></details>}</li>)}</ul>
}

export default function PdfImportWizard({ onCancel, onCandidate }) {
  const [inspection, setInspection] = useState(null), [selectedFile, setSelectedFile] = useState(null)
  const [goalId, setGoalId] = useState(''), [level, setLevel] = useState('構成を自力で再現できる')
  const [previousRange, setPreviousRange] = useState(8), [maxNodes, setMaxNodes] = useState(30)
  const [mapMode, setMapMode] = useState('document-structure'), [error, setError] = useState(''), [progress, setProgress] = useState('')
  const [aiStatus, setAiStatus] = useState({ loading: true, available: false }), [selection, setSelection] = useState(null), [metadataConsented, setMetadataConsented] = useState(false), [consented, setConsented] = useState(false)
  const controllerRef = useRef(null)
  const fileRef = useRef(null)
  const timingRef = useRef({})
  const flatOutline = useMemo(() => flatten(inspection?.outline ?? []), [inspection])
  const goalItem = flatOutline.find((item) => item.id === goalId)

  useEffect(() => {
    const controller = new AbortController()
    getAiAvailability(controller.signal).then((value) => setAiStatus({ loading: false, available: value.aiAvailable, model: value.model, configurationError: value.configurationError })).catch(() => setAiStatus({ loading: false, available: false }))
    return () => controller.abort()
  }, [])

  useEffect(() => () => {
    controllerRef.current?.abort()
    if (fileRef.current) import('../learningMap/pdfjsAdapter.js').then(({ releasePdfSession }) => releasePdfSession(fileRef.current)).catch(() => {})
  }, [])

  async function selectFile(event) {
    controllerRef.current?.abort()
    const file = event.target.files?.[0]
    if (fileRef.current && fileRef.current !== file) {
      const previousFile = fileRef.current
      import('../learningMap/pdfjsAdapter.js').then(({ releasePdfSession }) => releasePdfSession(previousFile)).catch(() => {})
    }
    fileRef.current = file ?? null
    setSelectedFile(file ?? null); setInspection(null); setGoalId(''); setSelection(null); setMetadataConsented(false); setConsented(false); setError('')
    if (!file) return
    timingRef.current = { pdfAnalysisStartedAt: new Date().toISOString() }
    const controller = new AbortController(); controllerRef.current = controller
    try {
      const result = await inspectPdf(file, { signal: controller.signal, onProgress: setProgress })
      setInspection(result)
      const items = flatten(result.outline)
      const reviewedGoal = result.reviewedConceptMapAvailable ? items.find((item) => item.title.includes('実対称行列の直交行列による対角化')) : null
      setGoalId(reviewedGoal?.id ?? items.find((item) => item.pdfPage)?.id ?? '')
      setMapMode(result.reviewedConceptMapAvailable ? 'known-reviewed-data' : aiStatus.available ? 'ai' : 'document-structure')
    } catch (reason) { if (reason.name !== 'AbortError') setError(reason.message) } finally { setProgress(''); if (controllerRef.current === controller) controllerRef.current = null }
  }

  async function selectSections() {
    if (!inspection || !goalItem || !metadataConsented) return
    const controller = new AbortController(); controllerRef.current = controller; setError(''); setSelection(null); setConsented(false); setProgress('関連章節を選定中')
    timingRef.current = { ...timingRef.current, aiCandidateGenerationStartedAt: new Date().toISOString() }
    try {
      const result = await selectRelevantSections({ title: inspection.metadata.title, author: inspection.metadata.author, pageCount: inspection.metadata.pageCount, outline: flatOutline.map(({ id, title, level: itemLevel, pdfPage, parentId }) => ({ id, title, level: itemLevel, pdfPage, parentId })), goal: goalItem.title, understandingLevel: level, maxSections: 10, maxPages: DEFAULT_AI_PAGE_LIMIT }, controller.signal)
      setSelection({ ...normalizeSelectedSections(result.sections, inspection.metadata.pageCount, DEFAULT_AI_PAGE_LIMIT), warnings: result.warnings })
    } catch (reason) { if (reason.name !== 'AbortError') setError(reason.message) } finally { setProgress(''); controllerRef.current = null }
  }

  async function createAiCandidate() {
    if (!inspection || !selectedFile || !goalItem || !selection || !consented) return
    const controller = new AbortController(); controllerRef.current = controller; setError('')
    try {
      setProgress('対象ページを抽出中')
      const { extractPdfPagesWithPdfJs } = await import('../learningMap/pdfjsAdapter.js')
      const extraction = await extractPdfPagesWithPdfJs(selectedFile, selection.pageNumbers, { signal: controller.signal, onProgress: setProgress })
      setProgress('概念と依存関係の候補を生成中')
      const apiPages = toApiPageTexts(extraction.pages)
      const base = { title: inspection.metadata.title, author: inspection.metadata.author, pageCount: inspection.metadata.pageCount, goal: goalItem.title, understandingLevel: level, sections: selection.sections.map(({ pages: _pages, ...section }) => section), pages: apiPages }
      const graph = await generateLearningGraph({ ...base, maxNodes, maxPages: DEFAULT_AI_PAGE_LIMIT }, controller.signal)
      setProgress('生成結果を批判的にレビュー中')
      const review = await reviewLearningGraph({ pageCount: inspection.metadata.pageCount, goal: goalItem.title, pages: apiPages, graph }, controller.signal)
      setProgress('候補画面を準備中')
      const warnings = [...graph.warnings, ...(extraction.skippedPages.length ? [`文字品質により未送信: p.${extraction.skippedPages.join(', p.')}`] : [])]
      const completedAt = new Date().toISOString()
      const planningTiming = { ...timingRef.current, aiCandidateGenerationCompletedAt: completedAt, humanReviewStartedAt: completedAt }
      onCandidate(toCandidateMap({ ...graph, warnings }, review, inspection, goalItem.title, level, selection.sections, { pageTexts: apiPages, planningTiming }))
    } catch (reason) { if (reason.name !== 'AbortError') setError(reason.message) } finally { setProgress(''); controllerRef.current = null }
  }

  async function createLocalCandidate() {
    if (!inspection || !selectedFile || !goalItem) return
    const controller = new AbortController(); controllerRef.current = controller; setError('')
    try {
      setProgress('候補画面を準備中')
      onCandidate(mapMode === 'known-reviewed-data' ? getReviewedConceptMap(inspection) : generateDocumentStructureMapCandidate(inspection, { goalOutlineId: goalId, understandingLevel: level, previousRange, maxNodes }))
    } catch (reason) { if (reason.name !== 'AbortError') setError(reason.message) } finally { setProgress(''); controllerRef.current = null }
  }

  return <section className="import-page"><button className="back-link" onClick={onCancel}>← マップ一覧</button>
    <div className="import-header"><span className="eyebrow">PDF IMPORT · AI CANDIDATE</span><h1>PDFから学習マップ候補を作成</h1><p>PDFの基本解析はブラウザ内で行います。PDF全体は送信しません。概念依存マップを生成する場合のみ、利用者が確認した章節の抽出テキストをOpenAI APIへ送信します。</p><p className="version-scope">テキスト層とアウトラインを持つPDFが対象です。OCR・画像理解は未実装です。</p></div>
    <div className="ai-status"><strong>{aiStatus.loading ? 'AI接続を確認中' : aiStatus.available ? 'AI解析を利用できます' : 'AI未接続'}</strong><span>{aiStatus.available ? `サーバー側モデル: ${aiStatus.model}` : aiStatus.configurationError || 'Math Notes、PDF解析、既存マップ、文書構造マップは引き続き利用できます。'}</span></div>
    <div className="import-panel"><label className="file-drop"><span className="file-drop__icon">PDF</span><strong>1. 教材PDFを選択</strong><span>日本語・英語、原則1段組みの教科書・講義ノート</span><input type="file" accept="application/pdf,.pdf" onChange={selectFile} /></label>{progress && <div className="analysis-progress"><span className="spinner" />{progress}<button onClick={() => controllerRef.current?.abort()}>キャンセル</button></div>}{error && <div className="ai-error"><p className="form-error">{error}</p>{inspection?.supported && <button className="btn btn--ghost" onClick={() => { setMapMode('document-structure'); setSelection(null); setError('') }}>文書構造マップへ切り替える</button>}</div>}</div>
    {inspection && <div className="pdf-inspection"><div className="inspection-heading"><h2>2. PDF解析結果を確認</h2><span className={inspection.supported ? 'support-badge supported' : 'support-badge unsupported'}>{inspection.supported ? '対応' : '未対応'}</span></div><div className="pdf-facts pdf-facts--v1"><span><b>ファイル名</b>{inspection.metadata.fileName}</span><span><b>書名</b>{inspection.metadata.title}</span><span><b>著者</b>{inspection.metadata.author}</span><span><b>ページ数</b>{inspection.metadata.pageCount}</span><span><b>サイズ</b>{formatBytes(inspection.metadata.fileSize)}</span><span><b>アウトライン</b>{inspection.rawOutlineCount}項目</span><span><b>テキスト品質</b>{inspection.extractionQuality.quality}</span><span><b>SHA-256</b><code>{inspection.fileHash.slice(0, 12)}…</code></span></div>
      {!inspection.supported && <div className="unsupported-reasons">{inspection.unsupportedReasons.map((reason) => <p key={reason}>• {reason}</p>)}</div>}{inspection.warnings.map((warning) => <p className="extraction-warning" key={warning}>⚠ {warning}</p>)}
      {inspection.outline.length > 0 && <div className="outline-goal-panel"><h3>3. 到達目標を選択</h3><div className="outline-scroll"><OutlineTree items={inspection.outline} selectedId={goalId} onSelect={(id) => { setGoalId(id); setSelection(null); setMetadataConsented(false); setConsented(false) }} /></div></div>}
      {inspection.supported && <div className="goal-options"><div className="reviewed-map-notice"><strong>作成方法</strong>{inspection.reviewedConceptMapAvailable && <label><input type="radio" checked={mapMode === 'known-reviewed-data'} onChange={() => setMapMode('known-reviewed-data')} /> レビュー済み線形代数マップ</label>}<label><input type="radio" checked={mapMode === 'document-structure'} onChange={() => setMapMode('document-structure')} /> 文書構造マップ（AI失敗時のフォールバック）</label><label className={!aiStatus.available ? 'disabled-option' : ''}><input type="radio" disabled={!aiStatus.available} checked={mapMode === 'ai'} onChange={() => setMapMode('ai')} /> AIで概念依存候補を生成</label></div>
        <div className="goal-selection goal-selection--v1"><label>理解レベル<select value={level} onChange={(event) => setLevel(event.target.value)}>{UNDERSTANDING_LEVELS.map((item) => <option key={item}>{item}</option>)}</select></label>{mapMode === 'document-structure' && <label>前項目の範囲<select value={previousRange} onChange={(event) => setPreviousRange(Number(event.target.value))}><option value="3">前3項目</option><option value="8">前8項目</option><option value="15">前15項目</option></select></label>}<label>最大ノード数<select value={maxNodes} onChange={(event) => setMaxNodes(Number(event.target.value))}><option value="10">10</option><option value="20">20</option><option value="30">30</option></select></label>{mapMode === 'ai' ? <><label className="consent-check"><input type="checkbox" checked={metadataConsented} onChange={(event) => { setMetadataConsented(event.target.checked); setSelection(null); setConsented(false) }} />4. 書名・著者・目次・学習目標をOpenAI APIへ送信し、関連章節を選定することに同意します</label><button className="btn btn--primary" disabled={!goalId || !metadataConsented || Boolean(progress)} onClick={selectSections}>5. AIに関連章節を選定させる</button></> : <button className="btn btn--primary" disabled={!goalId || Boolean(progress)} onClick={createLocalCandidate}>候補を確認する →</button>}</div>
        {mapMode === 'ai' && selection && <div className="consent-panel"><h3>6. 送信予定の章節・ページ範囲を確認</h3>{selection.sections.map((section) => <div className="send-section" key={section.outlineId}><strong>{section.title}</strong><span>p.{section.startPage}–{section.endPage} · {section.pages.length}ページ</span><p>{section.rationale}（信頼度: {section.confidence}）</p></div>)}<div className="send-summary"><span>ページ数 <b>{selection.pageNumbers.length}</b></span><span>概算文字数 <b>抽出時に算出</b></span><span>送信目的 <b>候補生成と批判的レビュー</b></span></div>{selection.warnings.map((warning) => <p className="extraction-warning" key={warning}>⚠ {warning}</p>)}<label className="consent-check"><input type="checkbox" checked={consented} onChange={(event) => setConsented(event.target.checked)} />7. 上記ページの抽出テキストをOpenAI APIへ送信することに同意します</label><div className="consent-actions"><button className="btn btn--ghost" onClick={() => { setSelection(null); setConsented(false) }}>キャンセル</button><button className="btn btn--primary" disabled={!consented || Boolean(progress)} onClick={createAiCandidate}>8. 概念依存グラフ候補を生成</button></div><p className="ai-disclaimer">AIはPDFから概念と依存関係の候補を生成します。数学的な正しさや完全性を保証するものではありません。出典と依存関係を確認・編集してから学習マップとして保存してください。指摘や候補がないことは、必要な前提がすべて含まれていることを保証しません。</p></div>}
      </div>}</div>}
  </section>
}
