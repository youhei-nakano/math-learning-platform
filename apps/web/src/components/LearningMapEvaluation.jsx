import { createLinearAlgebraCandidateMap } from '../learningMap/linearAlgebraData'
import { evaluateLearningMap } from '../learningMap/mapEvaluation'
import { calculatePlanningTiming } from '../learningMap/candidateAudit'

const percent = (value) => `${(value * 100).toFixed(1)}%`
const metricLabels = {
  requiredConceptRecall: '必須概念再現率', conceptPrecision: '概念適合率', unnecessaryConceptRate: '不要概念率',
  dependencyPrecision: '依存関係適合率', dependencyRecall: '依存関係再現率', sourcePageAccuracy: '出典ページ正確率',
  cycleCount: '循環数', externalPrerequisiteCount: 'PDF外前提候補数', aiNodeCount: 'AI出力ノード数', humanCorrectionCount: '人間による修正数',
}

const name = (node) => node?.title ?? node?.id ?? '不明'
const edgeName = (edge, nodes) => `${name(nodes.find((node) => node.id === edge.sourceId))} → ${name(nodes.find((node) => node.id === edge.targetId))}`

function DetailList({ title, items, render, empty = '該当なし' }) {
  return <section className="evaluation-detail"><h2>{title} <small>{items.length}</small></h2>{items.length ? <ul>{items.map((item, index) => <li key={item.candidate?.id ?? item.id ?? index}>{render(item)}</li>)}</ul> : <p>{empty}</p>}</section>
}

export default function LearningMapEvaluation({ map, onBack }) {
  const baseline = createLinearAlgebraCandidateMap('2026-01-01T00:00:00.000Z')
  const result = evaluateLearningMap(map, baseline)
  const timing = calculatePlanningTiming(map.planningTiming)
  return <section className="evaluation-page"><button className="back-link" onClick={onBack}>← 戻る</button>
    <header className="evaluation-header"><span className="eyebrow">LEARNING MAP EVALUATION</span><h1>概念依存マップの比較評価</h1><p>評価対象: <b>{map.name}</b></p><p>基準: <b>{baseline.name}（人間が確認した22ノード）</b></p><p className="evaluation-disclaimer">名称・別名の正規化完全一致を自動照合に使います。ページや節が近いだけの候補は、誤照合を避けるため人間による照合が必要として表示します。</p></header>
    <div className="planning-timing"><b>計画作成記録</b><span>PDF解析開始: {timing.pdfAnalysisStartedAt ? new Date(timing.pdfAnalysisStartedAt).toLocaleString('ja-JP') : '記録なし'}</span><span>AI生成開始: {timing.aiCandidateGenerationStartedAt ? new Date(timing.aiCandidateGenerationStartedAt).toLocaleString('ja-JP') : '記録なし'}</span><span>AI生成完了: {timing.aiCandidateGenerationCompletedAt ? new Date(timing.aiCandidateGenerationCompletedAt).toLocaleString('ja-JP') : '記録なし'}</span><span>人による確認開始: {timing.humanReviewStartedAt ? new Date(timing.humanReviewStartedAt).toLocaleString('ja-JP') : '記録なし'}</span><span>マップ確定: {timing.learningMapFinalizedAt ? new Date(timing.learningMapFinalizedAt).toLocaleString('ja-JP') : '記録なし'}</span></div>
    <div className="metric-grid">{Object.entries(result.metrics).map(([key, value]) => <article key={key}><span>{metricLabels[key]}</span><strong>{key.endsWith('Rate') || key.endsWith('Recall') || key.endsWith('Precision') || key.endsWith('Accuracy') ? percent(value) : value}</strong></article>)}</div>
    <div className="evaluation-columns">
      <DetailList title="一致した概念" items={result.matches} render={(item) => <><b>{name(item.candidate)}</b> ⇔ {name(item.baseline)} <small>canonicalName／alias一致</small></>} />
      <DetailList title="基準にありAI出力にない概念" items={result.missingBaseline} render={(item) => <><b>{name(item)}</b> · {item.importance}</>} />
      <DetailList title="AI出力だけの概念" items={result.candidateOnly} render={(item) => <><b>{name(item)}</b> · {item.sourceType === 'external-prerequisite-suggestion' ? 'PDF外前提' : 'PDF内候補'}</>} />
      <DetailList title="人間による照合が必要" items={result.needsHumanMatch} render={(item) => <><b>{name(item.candidate)}</b><span>候補: {item.possibleBaselines.map(name).join(' / ')}</span><small>{item.reason}</small></>} />
      <DetailList title="一致した依存関係" items={result.matchedEdges} render={(item) => edgeName(item.candidate, map.nodes)} />
      <DetailList title="不一致の依存関係" items={result.unmatchedEdges} render={(item) => edgeName(item, map.nodes)} />
      <DetailList title="不足している依存関係" items={result.missingEdges} render={(item) => edgeName(item, baseline.nodes)} />
      <DetailList title="出典ページの不一致" items={result.pageMismatches} render={(item) => <><b>{name(item.candidate)}</b><span>AI: {(item.candidate.sourcePages ?? [item.candidate.pdfPage]).filter(Boolean).join(', ')} / 基準: {(item.baseline.sourcePages ?? [item.baseline.pdfPage]).filter(Boolean).join(', ')}</span></>} />
    </div>
  </section>
}
