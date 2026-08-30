import { useState } from 'react'
import { EDGE_TYPES } from '../learningMap/linearAlgebraData'
import { NODE_TYPES, UNDERSTANDING_LEVELS } from '../learningMap/constants'
import { validateLearningMap } from '../learningMap/mapValidation'
import { confirmCandidatesForTab } from '../learningMap/aiLearningMapService'
import { calculatePlanningTiming, recordModification } from '../learningMap/candidateAudit'

const IMPORTANCE = { required: '必須', recommended: '推奨', supporting: '補助' }
const AI_EDGE_TYPES = {
  'definition-required': '定義の理解に必要', 'theorem-required': '定理の主張に必要', 'used-in-proof': '証明で使用',
  'calculation-required': '計算に必要', helpful: '理解を助ける補助', 'optional-for-goal': '今回の目標では省略可能',
}

const NODE_CHANGE_TYPES = { included: 'node-inclusion', title: 'node-title', importance: 'node-importance', type: 'node-type', pdfPage: 'node-source-page' }
const EDGE_CHANGE_TYPES = { sourceId: 'edge-direction', targetId: 'edge-direction', type: 'edge-type' }
const formatDuration = (ms) => ms == null ? '記録なし' : `${Math.floor(ms / 60000)}分 ${Math.round((ms % 60000) / 1000)}秒`
const formatTimestamp = (value) => value ? new Date(value).toLocaleString('ja-JP') : '記録なし'

export default function MapCandidateReview({ map, onChange, onBack, onApprove, onEvaluate }) {
  const [tab, setTab] = useState('nodes')
  const [selectedId, setSelectedId] = useState(map.nodes[0]?.id)
  const [evidencePage, setEvidencePage] = useState(null)
  const selected = map.nodes.find((node) => node.id === selectedId)
  const errors = validateLearningMap(map)
  const unconfirmedNodes = map.nodes.filter((node) => node.included !== false && node.confirmationStatus === 'unconfirmed').length
  const unconfirmedEdges = map.edges.filter((edge) => edge.confirmationStatus === 'unconfirmed').length
  const unresolvedHigh = (map.aiReview?.issues ?? []).filter((issue) => issue.severity === 'high' && (!issue.resolutionStatus || issue.resolutionStatus === 'unresolved'))
  const timing = calculatePlanningTiming(map.planningTiming)
  function updateNode(id, updates) {
    const current = map.nodes.find((node) => node.id === id)
    let next = { ...map, nodes: map.nodes.map((node) => node.id === id ? { ...node, ...updates } : node) }
    for (const [field, after] of Object.entries(updates)) if (NODE_CHANGE_TYPES[field] && current?.[field] !== after) next = recordModification(next, { type: NODE_CHANGE_TYPES[field], targetKind: 'node', targetId: id, field, before: current?.[field] ?? null, after })
    onChange(next)
  }
  function updateEdge(id, updates) {
    const current = map.edges.find((edge) => edge.id === id)
    let next = { ...map, edges: map.edges.map((edge) => edge.id === id ? { ...edge, ...updates } : edge) }
    for (const [field, after] of Object.entries(updates)) if (EDGE_CHANGE_TYPES[field] && current?.[field] !== after) next = recordModification(next, { type: EDGE_CHANGE_TYPES[field], targetKind: 'edge', targetId: id, field, before: current?.[field] ?? null, after })
    onChange(next)
  }
  function addEdge() {
    const sourceId = map.nodes[0]?.id, targetId = map.nodes[1]?.id
    if (!sourceId || !targetId) return
    const edge = { id: crypto.randomUUID(), sourceId, targetId, type: EDGE_TYPES[0], rationale: '利用者が追加した関係', confirmationStatus: 'confirmed' }
    onChange(recordModification({ ...map, edges: [...map.edges, edge] }, { type: 'edge-add', targetKind: 'edge', targetId: edge.id, before: null, after: edge }))
  }
  function approve() {
    if (errors.length) return
    const finalizedAt = new Date().toISOString()
    onApprove({ ...map, candidateStatus: 'approved', originalSourceType: map.sourceType, sourceType: 'user-confirmed', sourceLabel: map.creationMethod === 'document-structure' ? '文書構造（利用者確認済み）' : '概念依存（利用者確認済み）', nodes: map.nodes.filter((node) => node.included !== false).map((node) => ({ ...node, sourceType: 'user-confirmed', confirmationStatus: 'confirmed', prerequisiteIds: map.edges.filter((edge) => edge.targetId === node.id).map((edge) => edge.sourceId) })), edges: map.edges.map((edge) => ({ ...edge, sourceType: 'user-confirmed', relationKind: 'user-confirmed', confirmationStatus: 'confirmed' })), planningTiming: calculatePlanningTiming({ ...map.planningTiming, learningMapFinalizedAt: finalizedAt }), updatedAt: finalizedAt })
  }
  function resolveIssue(id, resolutionStatus, resolutionReason = '') {
    const resolvedAt = resolutionStatus === 'unresolved' ? null : new Date().toISOString()
    onChange({ ...map, aiReview: { ...map.aiReview, issues: map.aiReview.issues.map((issue) => issue.id === id ? { ...issue, resolutionStatus, resolutionReason, resolvedAt } : issue) }, updatedAt: new Date().toISOString() })
  }
  function confirmAll() {
    onChange(confirmCandidatesForTab(map, tab))
  }
  return <section className="candidate-page"><button className="back-link" onClick={onBack}>← PDF情報へ戻る</button><div className="candidate-header"><div><span className="eyebrow">CANDIDATE REVIEW · {map.creationMethod === 'document-structure' ? 'DOCUMENT STRUCTURE' : 'CONCEPT DEPENDENCY'}</span><h1>学習フローチャート候補を確認</h1><p>自動確定ではありません。採否・出典・依存関係を確認して保存してください。</p>{map.creationMethod === 'document-structure' && <p className="structure-disclaimer">このマップはPDFの目次構造から作成した候補です。数学的な前提関係を保証するものではありません。内容と依存関係を確認・編集してから使用してください。</p>}{map.creationMethod === 'ai-concept-dependency' && <div className="ai-review-banner"><b>AI生成 · AIレビュー済み · 未確認</b><p>AIは候補を生成しますが、数学的な正しさや完全性を保証しません。指摘がないことも、必要な前提がすべて含まれることを保証しません。</p></div>}</div><div className="candidate-summary"><span>未確認ノード <b>{unconfirmedNodes}</b></span><span>未確認関係 <b>{unconfirmedEdges}</b></span>{onEvaluate && <button className="btn btn--ghost" onClick={onEvaluate}>基準マップと評価</button>}</div></div>
    <div className="planning-timing"><b>計画作成時間</b><span>PDF解析開始: {formatTimestamp(timing.pdfAnalysisStartedAt)}</span><span>AI候補生成開始: {formatTimestamp(timing.aiCandidateGenerationStartedAt)}</span><span>AI候補生成完了: {formatTimestamp(timing.aiCandidateGenerationCompletedAt)}</span><span>人による確認開始: {formatTimestamp(timing.humanReviewStartedAt)}</span><span>マップ確定: {formatTimestamp(timing.learningMapFinalizedAt)}</span><span>AI処理: {formatDuration(timing.aiProcessingMs)}</span><span>人による確認: {formatDuration(timing.humanReviewMs)}</span><span>全体: {formatDuration(timing.totalPlanningMs)}</span></div>
    {map.generationWarnings?.length > 0 && <div className="review-alert"><b>生成時の警告</b>{map.generationWarnings.map((warning) => <p key={warning}>• {warning}</p>)}</div>}
    {map.aiReview && <details className="review-alert" open><summary>AIレビューの指摘 ({map.aiReview.issues.length})</summary><p>{map.aiReview.summary}</p>{unresolvedHigh.length > 0 && <p className="high-review-warning">高重要度の指摘が未判断です。保存前に「修正した・問題なし・保留」のいずれかを記録してください。</p>}{map.aiReview.issues.map((issue) => <div className={`review-issue severity-${issue.severity}`} key={issue.id}><b>{issue.type} · {issue.targetKind}: {issue.targetId}</b><span>{issue.description}</span><small>確認: {issue.check}</small><label>判断<select value={issue.resolutionStatus ?? 'unresolved'} onChange={(event) => resolveIssue(issue.id, event.target.value, issue.resolutionReason)}><option value="unresolved">未判断</option><option value="fixed">修正した</option><option value="dismissed">問題なしと判断</option><option value="deferred">保留した</option></select></label>{issue.resolutionStatus === 'dismissed' && <label>理由（任意）<input value={issue.resolutionReason ?? ''} onChange={(event) => resolveIssue(issue.id, issue.resolutionStatus, event.target.value)} /></label>}</div>)}</details>}
    <div className="review-tabs"><button className={tab === 'nodes' ? 'active' : ''} onClick={() => setTab('nodes')}>ノード候補 ({map.nodes.length})</button><button className={tab === 'edges' ? 'active' : ''} onClick={() => setTab('edges')}>依存関係 ({map.edges.length})</button></div>
    {tab === 'nodes' ? <div className="candidate-layout"><div className="candidate-list">{map.nodes.map((node) => <button className={`candidate-row${selectedId === node.id ? ' selected' : ''}${!node.included ? ' excluded' : ''}`} key={node.id} onClick={() => { setSelectedId(node.id); setEvidencePage(node.sourcePages?.[0] ?? node.pdfPage ?? null) }}><input type="checkbox" checked={node.included !== false} onChange={(e) => { e.stopPropagation(); updateNode(node.id, { included: e.target.checked }) }} /><span><strong>{node.title}</strong><small>{NODE_TYPES[node.type]?.label ?? node.type} · {node.pdfPage ? `p.${node.pdfPage}` : 'PDF外'} · {IMPORTANCE[node.importance]}</small></span><em>{node.confirmationStatus === 'unconfirmed' ? '未確認' : '確認済み'}</em></button>)}</div>{selected && <div className="candidate-editor"><h2>{selected.title}</h2>{selected.sourceType === 'external-prerequisite-suggestion' ? <p className="source-chip external">PDF外前提候補 · PDF本文による根拠なし</p> : <p className="source-chip">PDF内根拠あり</p>}<label>採用区分<select value={selected.importance} onChange={(e) => updateNode(selected.id, { importance: e.target.value })}>{Object.entries(IMPORTANCE).map(([value,label]) => <option value={value} key={value}>{label}</option>)}</select></label><label>ノード種別<select value={selected.type} onChange={(e) => updateNode(selected.id, { type: e.target.value })}>{Object.entries(NODE_TYPES).map(([value,item]) => <option value={value} key={value}>{item.label}</option>)}</select></label><label>タイトル<input value={selected.title} onChange={(e) => updateNode(selected.id, { title: e.target.value })} /></label><label>学ぶ理由<textarea value={selected.reason} onChange={(e) => updateNode(selected.id, { reason: e.target.value })} /></label><label>到達条件<textarea value={selected.completion} onChange={(e) => updateNode(selected.id, { completion: e.target.value })} /></label><label>理解レベル<select value={selected.level} onChange={(e) => updateNode(selected.id, { level: e.target.value })}>{UNDERSTANDING_LEVELS.map((item) => <option key={item}>{item}</option>)}</select></label><label>参照ページ<input type="number" min="1" max={map.pdf.pageCount} value={selected.pdfPage ?? ''} onChange={(e) => { const page = Number(e.target.value); updateNode(selected.id, { pdfPage: page, sourcePages: [page] }); setEvidencePage(page) }} /></label><div className="candidate-evidence"><b>AIが説明した根拠</b><p>{selected.generationRationale || '説明なし'}</p><span>信頼度: {selected.confidence} · 抽出元: {selected.extractionSource}</span>{selected.sourcePages?.length > 0 && <div className="evidence-pages">{selected.sourcePages.map((page) => <button className={evidencePage === page ? 'active' : ''} key={page} onClick={() => setEvidencePage(page)}>p.{page}</button>)}</div>}<b>実際に送信した抽出テキスト（限定抜粋）</b><p className="evidence-excerpt">{map.evidenceExcerpts?.find((item) => item.page === (evidencePage ?? selected.sourcePages?.[0]))?.text || (selected.sourceType === 'external-prerequisite-suggestion' ? 'PDF本文による根拠なし' : 'この既存候補には抽出テキストが保存されていません。')}</p></div><button className="btn btn--ghost" onClick={() => updateNode(selected.id, { confirmationStatus: 'confirmed' })}>このノードを確認済みにする</button></div>}</div> : <div className="edge-review"><button className="btn btn--ghost" onClick={addEdge}>＋ 依存関係を追加</button>{map.edges.map((edge) => <div className="edge-row" key={edge.id}><select value={edge.sourceId} onChange={(e) => updateEdge(edge.id, { sourceId: e.target.value, confirmationStatus: 'confirmed' })}>{map.nodes.map((node) => <option value={node.id} key={node.id}>{node.title}</option>)}</select><span>→</span><select value={edge.targetId} onChange={(e) => updateEdge(edge.id, { targetId: e.target.value, confirmationStatus: 'confirmed' })}>{map.nodes.map((node) => <option value={node.id} key={node.id}>{node.title}</option>)}</select><select value={edge.type} onChange={(e) => updateEdge(edge.id, { type: e.target.value, confirmationStatus: 'confirmed' })}>{[...EDGE_TYPES, ...Object.keys(AI_EDGE_TYPES)].map((item) => <option value={item} key={item}>{AI_EDGE_TYPES[item] ?? item}</option>)}</select><span className="edge-kind">{edge.relationKind === 'document-structure' ? '文書構造' : '概念依存候補'}</span><span className={edge.confirmationStatus === 'unconfirmed' ? 'edge-unconfirmed' : 'edge-confirmed'}>{edge.confirmationStatus === 'unconfirmed' ? '未確認' : '確認済み'}</span><details className="edge-evidence"><summary>根拠</summary><p><b>AI説明:</b> {edge.rationale || '説明なし'}</p><p><b>ページ:</b> {edge.evidencePages?.length ? edge.evidencePages.map((page) => `p.${page}`).join(', ') : 'PDF本文による根拠なし'}</p></details><button aria-label="依存関係を削除" onClick={() => onChange(recordModification({ ...map, edges: map.edges.filter((item) => item.id !== edge.id) }, { type: 'edge-delete', targetKind: 'edge', targetId: edge.id, before: edge, after: null }))}>×</button></div>)}</div>}
    <div className="approve-bar"><div>{errors.length ? <span className="form-error">{errors.join(' / ')}</span> : unresolvedHigh.length ? <span className="form-error">高重要度のAI指摘について判断を記録してください（保留でも保存できます）。</span> : unconfirmedNodes + unconfirmedEdges > 0 ? <span>内容を確認し、個別または一括で確認済みにしてください。</span> : <span>すべての採用候補と依存関係を確認済みです。</span>}</div><div className="approve-actions">{(tab === 'nodes' ? unconfirmedNodes : unconfirmedEdges) > 0 && <button className="btn btn--ghost" onClick={confirmAll}>{tab === 'nodes' ? `ノード候補 ${unconfirmedNodes}件を一括確認` : `依存関係 ${unconfirmedEdges}件を一括確認`}</button>}<button className="btn btn--primary" disabled={errors.length > 0 || unconfirmedNodes + unconfirmedEdges > 0 || unresolvedHigh.length > 0} onClick={approve}>学習マップとして保存</button></div></div>
  </section>
}
