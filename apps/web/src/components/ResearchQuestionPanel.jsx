import { useEffect, useRef, useState } from 'react'
import { queryResearch } from '../research/researchApi.js'

export default function ResearchQuestionPanel() {
  const [question, setQuestion] = useState('What properties define a basis?')
  const [mode, setMode] = useState('single')
  const [result, setResult] = useState(null)
  const [state, setState] = useState('idle')
  const [error, setError] = useState('')
  const requestRef = useRef(null)

  useEffect(() => () => requestRef.current?.abort(), [])

  async function submit(event) {
    event?.preventDefault()
    requestRef.current?.abort()
    const controller = new AbortController()
    requestRef.current = controller
    const timer = setTimeout(() => controller.abort('timeout'), 20_000)
    setState('loading'); setError(''); setResult(null)
    try {
      const response = await queryResearch({ question: question.trim(), mode, signal: controller.signal })
      setResult(response); setState('success')
    } catch (caught) {
      if (controller.signal.aborted && controller.signal.reason !== 'timeout') { setState('idle'); return }
      setError(controller.signal.reason === 'timeout' ? '20秒以内に完了しませんでした。再試行してください。' : caught.message)
      setState('error')
    } finally {
      clearTimeout(timer)
      if (requestRef.current === controller) requestRef.current = null
    }
  }

  function cancel() { requestRef.current?.abort('user') }

  return <section className="research-panel" aria-labelledby="research-question-title">
    <div className="research-heading"><div><span className="eyebrow">GROUNDED QUESTION</span><h2 id="research-question-title">資料を根拠に質問する</h2></div><span className="offline-pill">CC0デモ資料・外部AIなし</span></div>
    <p className="research-description">openai-sandboxの固定済みPDFを検索し、取得済みチャンクだけを引用します。回答は抽出的なデモで、数学的な正しさを保証しません。</p>
    <form onSubmit={submit} className="research-form">
      <label>質問または数学問題<textarea value={question} maxLength={2000} required onChange={(event) => setQuestion(event.target.value)} /></label>
      <div className="research-controls"><fieldset><legend>処理方式</legend><label><input type="radio" name="mode" value="single" checked={mode === 'single'} onChange={() => setMode('single')} /> 単一エージェント</label><label><input type="radio" name="mode" value="multi" checked={mode === 'multi'} onChange={() => setMode('multi')} /> 複数役割</label></fieldset><div className="research-actions"><button className="btn btn--primary" disabled={state === 'loading' || !question.trim()}>{state === 'loading' ? '検索・回答生成中…' : '根拠付きで回答'}</button>{state === 'loading' && <button type="button" className="btn btn--ghost" onClick={cancel}>キャンセル</button>}</div></div>
    </form>
    {error && <div className="research-error" role="alert"><p>{error}</p><button className="btn btn--ghost btn--compact" onClick={submit}>再試行</button></div>}
    {result && <div className="research-answer" aria-live="polite"><div className="research-answer__meta"><b>{result.mode === 'multi' ? '複数役割' : '単一'}・{result.retrieval}</b><span>検索 {Math.round((result.timings?.searchSeconds ?? 0) * 1000)}ms / 全体 {Math.round((result.timings?.totalSeconds ?? 0) * 1000)}ms</span></div><h3>回答</h3><p className="answer-text">{result.answer}</p>{result.citations.length === 0 ? <p className="no-evidence">引用可能な根拠は見つかりませんでした。</p> : <ol className="citation-list">{result.citations.map((citation) => <li key={citation.chunkId}><details><summary><b>[{citation.number}] {citation.documentTitle}</b> p.{citation.pageNumber} <span>スコア {citation.score.toFixed(3)}</span></summary><dl><div><dt>文書ID</dt><dd>{citation.documentId}</dd></div><div><dt>版</dt><dd><code>{citation.documentVersion.slice(0, 12)}…</code></dd></div><div><dt>チャンク</dt><dd><code>{citation.chunkId}</code></dd></div><div><dt>方式</dt><dd>{citation.retrievalMethod}{citation.ocrDerived ? '・OCR' : ''}</dd></div></dl><blockquote>{citation.text}</blockquote></details></li>)}</ol>}<p className="research-notice">{result.notice ?? '根拠がない場合は「資料内では確認できません」と表示します。'}</p></div>}
  </section>
}
