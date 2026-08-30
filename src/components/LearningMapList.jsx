function formatDate(value) { return value ? new Date(value).toLocaleDateString('ja-JP') : '—' }

export default function LearningMapList({ maps, onOpen, onImport, onEvaluate }) {
  return <section className="map-library">
    <div className="library-header"><div><span className="eyebrow">LEARNING MAP LIBRARY</span><h1>数学学習マップ</h1><p>目標ごとに、前提・到達条件・現在地を管理します。</p></div><button className="btn btn--primary" onClick={onImport}>＋ PDFから作成</button></div>
    <div className="research-dashboard"><ResearchQuestionPanel /><ResearchEvaluationResults /></div>
    <div className="map-card-grid">{maps.map((map) => {
      const included = map.nodes.filter((node) => node.included !== false)
      const done = included.filter((node) => node.status === 'understood').length
      return <article className="map-card" key={map.id}>
        <div className="map-card__top"><span className={`source-pill source-${map.sourceType}`}>{map.sourceLabel}</span><span>{included.length}ノード</span></div>
        <h2>{map.name}</h2><p className="map-card__goal"><b>到達目標</b>{map.goal}</p>
        <dl><div><dt>使用PDF</dt><dd>{map.pdf?.fileName ?? 'なし（デモ）'}</dd></div><div><dt>進捗</dt><dd>{done} / {included.length}</dd></div><div><dt>作成</dt><dd>{formatDate(map.createdAt)}</dd></div><div><dt>更新</dt><dd>{formatDate(map.updatedAt)}</dd></div></dl>
        <div className="map-card__actions"><button className="btn btn--ghost map-card__open" onClick={() => onOpen(map.id)}>{map.candidateStatus === 'review' ? '候補確認を続ける' : '学習マップを開く'} →</button>{map.creationMethod === 'ai-concept-dependency' && <button className="btn btn--ghost" onClick={() => onEvaluate(map.id)}>基準マップと評価</button>}</div>
      </article>
    })}</div>
  </section>
}
import ResearchEvaluationResults from './ResearchEvaluationResults.jsx'
import ResearchQuestionPanel from './ResearchQuestionPanel.jsx'
