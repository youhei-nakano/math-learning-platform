import { useEffect, useState } from 'react'

export default function ResearchEvaluationResults() {
  const [report, setReport] = useState(null)
  const [liveReport, setLiveReport] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    const controller = new AbortController()
    fetch('/evaluation-results.json', { signal: controller.signal }).then((response) => {
      if (!response.ok) throw new Error('結果ファイルがありません。')
      return response.json()
    }).then(setReport).catch((caught) => { if (caught.name !== 'AbortError') setError(caught.message) })
    fetch('/live-evaluation-status.json', { signal: controller.signal }).then((response) => {
      if (!response.ok) throw new Error('実LLM評価の状態ファイルがありません。')
      return response.json()
    }).then(setLiveReport).catch((caught) => {
      if (caught.name !== 'AbortError') setLiveReport({ status: 'not_run', reason: caught.message })
    })
    return () => controller.abort()
  }, [])
  return <section className="research-panel evaluation-summary" aria-labelledby="evaluation-summary-title">
    <div className="research-heading"><div><span className="eyebrow">MEASURED EVALUATION</span><h2 id="evaluation-summary-title">品質・時間・費用</h2></div>{report && <time dateTime={report.generatedAt}>更新 {new Date(report.generatedAt).toLocaleString('ja-JP')}</time>}</div>
    {!report && <p className="empty-evaluation">{error ? '評価はまだ実行されていません。' : '評価結果を読み込んでいます…'}</p>}
    {report && <><p className="research-description">評価セット {report.datasetVersion}。4問の小規模なオフライン抽出実験であり、一般的な数学性能やLLM性能を示すものではありません。</p><div className="evaluation-table-scroll"><table><thead><tr><th>方式</th><th>品質</th><th>引用精度</th><th>完了率</th><th>中央値</th><th>API費用/問</th><th>成功/実行</th></tr></thead><tbody>{report.rows.map((row) => <tr key={row.experimentId}><th>{row.label}</th><td>{(row.qualityScore * 100).toFixed(0)}%</td><td>{(row.citationPrecision * 100).toFixed(0)}%</td><td>{(row.completionRate * 100).toFixed(0)}%</td><td>{(row.medianSeconds * 1000).toFixed(3)}ms</td><td>${row.averageCostUsd.toFixed(4)}</td><td>{row.successes}/{row.runs}</td></tr>)}</tbody></table></div><div className="evaluation-meta"><span>実験ID: {report.rows.map((row) => row.experimentId).join(' / ')}</span><span>モデル: {report.model}</span><span>検索: {report.retrieval}</span></div><p className="research-notice">費用は外部モデルAPIのみ。今回のモデル呼び出しは0回のため$0で、端末の電力・計算費用は含みません。</p></>}
    {liveReport && <p className="research-notice" role="status"><strong>実LLM評価: {liveReport.status === 'measured' ? '実測済み' : 'Not run'}</strong> — {liveReport.status === 'measured' ? `${liveReport.experiments.length}件の実験結果があります。` : liveReport.reason}</p>}
  </section>
}
