import { useMemo, useRef, useState } from 'react'
import LearningGraph from '../components/LearningGraph'
import LearningMapList from '../components/LearningMapList'
import LearningNodeDetail from '../components/LearningNodeDetail'
import MapCandidateReview from '../components/MapCandidateReview'
import PdfImportWizard from '../components/PdfImportWizard'
import LearningMapEvaluation from '../components/LearningMapEvaluation'
import { LEARNING_STATUSES, NODE_TYPES } from '../learningMap/constants'
import { useLearningMaps } from '../hooks/useLearningMaps'
import { addLearningNode, deleteLearningNode, deserializeLearningMap, duplicateLearningNode, serializeLearningMap } from '../learningMap/mapNodeOperations'

export default function LearningMapPage() {
  const { maps, activeMap, selectMap, upsertMap, updateActiveMap, updateNode, saveState, retrySave } = useLearningMaps()
  const [screen, setScreen] = useState('list')
  const [selectedId, setSelectedId] = useState(null)
  const [mode, setMode] = useState('all')
  const [candidate, setCandidate] = useState(null)
  const [evaluationMap, setEvaluationMap] = useState(null)
  const [operationError, setOperationError] = useState('')
  const importRef = useRef(null)
  const selectedNode = activeMap?.nodes.find((node) => node.id === selectedId)
  const includedNodes = useMemo(() => activeMap?.nodes.filter((node) => node.included !== false) ?? [], [activeMap])
  const progress = useMemo(() => includedNodes.filter((node) => node.status === 'understood').length, [includedNodes])

  function openMap(id) {
    selectMap(id)
    const map = maps.find((item) => item.id === id)
    if (map?.candidateStatus === 'review') { setCandidate(map); setScreen('review') }
    else { setSelectedId(null); setScreen('map') }
  }
  function receiveCandidate(map) { upsertMap(map); setCandidate(map); setScreen('review') }
  function approveCandidate(map) { upsertMap(map); setCandidate(null); setSelectedId(null); setScreen('map') }
  function addNode() {
    if (!activeMap) return
    const result = addLearningNode(activeMap, crypto.randomUUID())
    updateActiveMap(result.map); setSelectedId(result.node.id); setOperationError('')
  }
  function duplicateNode(id) {
    const result = duplicateLearningNode(activeMap, id, crypto.randomUUID())
    updateActiveMap(result.map); setSelectedId(result.node.id); setOperationError('')
  }
  function deleteNode(id) {
    try { updateActiveMap(deleteLearningNode(activeMap, id)); setSelectedId(null); setOperationError('') } catch (error) { setOperationError(error.message) }
  }
  function exportMap() {
    const blob = new Blob([serializeLearningMap(activeMap)], { type: 'application/json' })
    const url = URL.createObjectURL(blob), anchor = document.createElement('a')
    anchor.href = url; anchor.download = `${activeMap.name.replace(/[^\p{L}\p{N}_-]+/gu, '-')}.json`; anchor.click(); URL.revokeObjectURL(url)
  }
  async function importMap(event) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    if (file.size > 2 * 1024 * 1024) { setOperationError('2MBを超えるマップJSONは読み込めません。'); return }
    try { const map = deserializeLearningMap(await file.text()); upsertMap(map); setSelectedId(null); setScreen('map'); setOperationError('') } catch (error) { setOperationError(error.message) }
  }

  function openEvaluation(id) { const map = maps.find((item) => item.id === id); if (map) { setEvaluationMap(map); if (map.candidateStatus === 'review') setCandidate(map); setScreen('evaluation') } }
  if (screen === 'list') return <LearningMapList maps={maps} onOpen={openMap} onImport={() => setScreen('import')} onEvaluate={openEvaluation} />
  if (screen === 'import') return <PdfImportWizard onCancel={() => setScreen('list')} onCandidate={receiveCandidate} />
  if (screen === 'evaluation' && evaluationMap) return <LearningMapEvaluation map={evaluationMap} onBack={() => setScreen(evaluationMap.candidateStatus === 'review' ? 'review' : 'list')} />
  if (screen === 'review' && candidate) return <MapCandidateReview map={candidate} onChange={(map) => { setCandidate(map); setEvaluationMap(map); upsertMap(map) }} onBack={() => setScreen('import')} onApprove={approveCandidate} onEvaluate={() => { setEvaluationMap(candidate); setScreen('evaluation') }} />
  if (!activeMap) return null

  return <main className="learning-map-page">
    <header className="map-header"><div className="map-header__title"><button className="map-back-button" onClick={() => { setSelectedId(null); setScreen('list') }}>←</button><span className="map-mark">∑</span><div><span className="eyebrow">{activeMap.sourceLabel}</span><h1>{activeMap.name}</h1><p>{activeMap.goal}</p></div></div><div className="progress-card"><span>基本理解を確認</span><strong>{progress}<small> / {includedNodes.length}</small></strong><div className="progress-track"><span style={{ width: `${includedNodes.length ? progress / includedNodes.length * 100 : 0}%` }} /></div></div></header>
    <div className="demo-notice"><strong>{activeMap.sourceType === 'demo' ? 'デモ用の暫定構成' : activeMap.creationMethod === 'document-structure' ? '文書構造マップ' : 'PDF出典付き・利用者確認済み候補'}</strong><span>{activeMap.sourceType === 'demo' ? '内容は操作検証用です。実際の学習では採用する設定と文献に応じて確認してください。' : activeMap.creationMethod === 'document-structure' ? 'このマップはPDFの目次構造から作成した候補です。数学的な前提関係を保証するものではありません。' : `『${activeMap.pdf?.title}』のアウトラインと対象ページに基づく候補です。本文抽出の文字化け箇所は根拠に使用していません。`}</span></div>
    <section className="map-workspace"><div className="map-toolbar"><div className="view-toggle" aria-label="表示範囲"><button className={mode === 'all' ? 'active' : ''} onClick={() => setMode('all')}>全体表示</button><button className={mode === 'minimal' ? 'active' : ''} onClick={() => setMode('minimal')}>必要最小限の経路</button></div><div className="map-actions"><button className="btn btn--ghost" onClick={addNode}>＋ ノード</button><button className="btn btn--ghost" onClick={exportMap}>書き出し</button><button className="btn btn--ghost" onClick={() => importRef.current?.click()}>読み込み</button><input ref={importRef} className="visually-hidden" type="file" accept="application/json,.json" onChange={importMap} /></div><div className="map-legend"><span className="legend-route">━ 推奨経路</span><span>┄ 未確認の関係</span><span>⚠ 未完了の前提あり</span><span>● メモあり</span><span className="scroll-hint">横にスクロール →</span></div></div>
      {operationError && <p className="map-operation-error" role="alert">{operationError}</p>}
      <LearningGraph goal={activeMap.goal} nodes={activeMap.nodes} edges={activeMap.edges} selectedId={selectedId} mode={mode} onSelect={setSelectedId} />
      <div className="legend-row"><div className="legend-group"><b>状態</b>{Object.entries(LEARNING_STATUSES).map(([key, item]) => <span className={`legend-status status-${key}`} key={key}>{item.symbol} {item.label}</span>)}</div><div className="legend-group"><b>種類</b>{Object.values(NODE_TYPES).map((item) => <span key={item.label}>{item.icon} {item.label}</span>)}</div><div className="legend-group"><b>採用区分</b><span>必須</span><span>推奨</span><span>補助</span></div></div>
    </section>
    {selectedNode && <LearningNodeDetail node={selectedNode} nodes={activeMap.nodes} edges={activeMap.edges} isDemo={activeMap.sourceType === 'demo'} saveState={saveState} onRetrySave={retrySave} onClose={() => setSelectedId(null)} onUpdate={(updates) => updateNode(selectedNode.id, updates)} onDuplicate={() => duplicateNode(selectedNode.id)} onDelete={() => deleteNode(selectedNode.id)} />}
  </main>
}
