import { CONCEPT_CHECKS, LEARNING_STATUSES, NODE_TYPES, UNDERSTANDING_LEVELS } from '../learningMap/constants'
import ProofReviewPanel from './ProofReviewPanel'
import LatexPreview from './LatexPreview'
import 'katex/dist/katex.min.css'

const SAVE_LABELS = { saving: '保存中…', saved: '保存しました', error: '保存失敗' }

export default function LearningNodeDetail({ node, nodes, edges, isDemo, onClose, onUpdate, onDuplicate, onDelete, saveState, onRetrySave }) {
  const prerequisites = edges.filter((edge) => edge.targetId === node.id).map((edge) => nodes.find((item) => item.id === edge.sourceId)).filter(Boolean)
  const nextNodes = edges.filter((edge) => edge.sourceId === node.id).map((edge) => nodes.find((item) => item.id === edge.targetId)).filter(Boolean)
  const showChecklist = node.type === 'concept' || node.type === 'definition'
  const showProof = node.type === 'theorem' || node.type === 'lemma'
  const type = NODE_TYPES[node.type]
  function requestDelete() {
    if (window.confirm(`「${node.title}」を削除しますか？関連する依存関係とノードメモも削除されます。`)) onDelete()
  }

  return (
    <aside className="node-detail" aria-label={`${node.title}の詳細`}>
      <div className="node-detail__header">
        <div><span className="node-detail__type">{type.icon} {type.label}</span><h2>{node.title}</h2>{isDemo && <span className="demo-badge">デモ用の暫定構成</span>}</div>
        <button className="detail-close" onClick={onClose} aria-label="詳細を閉じる">×</button>
      </div>
      <div className="node-detail__body">
        <div className="detail-grid">
          <label>学習状態<select value={node.status} onChange={(e) => onUpdate({ status: e.target.value })}>{Object.entries(LEARNING_STATUSES).map(([value, item]) => <option value={value} key={value}>{item.label}</option>)}</select></label>
          <label>必要な理解レベル<select value={node.level} onChange={(e) => onUpdate({ level: e.target.value })}>{UNDERSTANDING_LEVELS.map((level) => <option key={level}>{level}</option>)}</select></label>
        </div>
        <label>この項目を学ぶ理由<textarea value={node.reason} onChange={(e) => onUpdate({ reason: e.target.value })} /></label>
        <label>目標概念との関係<textarea value={node.relation} onChange={(e) => onUpdate({ relation: e.target.value })} /></label>
        <label>到達条件<textarea value={node.completion} onChange={(e) => onUpdate({ completion: e.target.value })} /></label>
        <section className="node-notes" aria-labelledby={`node-notes-${node.id}`}><div className="node-notes__heading"><div><span className="detail-kicker">NODE MEMO</span><h3 id={`node-notes-${node.id}`}>このノード専用のメモ</h3></div><span className={`save-indicator save-${saveState.status}`} role="status" aria-live="polite">{SAVE_LABELS[saveState.status]}</span></div><label className="visually-hidden" htmlFor={`node-note-input-${node.id}`}>このノード専用のメモ</label><textarea id={`node-note-input-${node.id}`} className="detail-notes" value={node.notes ?? ''} placeholder={'理解したこと、疑問、次に確認すること…\n数式は $x^2$ または $$A^T=A$$ の形式で入力できます。'} onChange={(e) => onUpdate({ notes: e.target.value })} />{saveState.status === 'error' && <div className="save-error" role="alert"><span>{saveState.message}</span><button className="btn btn--ghost" onClick={onRetrySave}>再試行</button></div>}<LatexPreview content={node.notes ?? ''} /></section>
        <label>参照文献<textarea value={node.references} placeholder="書名・章・ページ・URLなど" onChange={(e) => onUpdate({ references: e.target.value })} /></label>
        {node.pdfTitle && <div className="pdf-reference"><span className="detail-kicker">PDF reference</span><strong>『{node.pdfTitle}』</strong><span>{node.section}</span><span>PDF p.{node.pdfPage}</span><small>抽出元: {node.extractionSource} · 信頼度: {node.confidence === 'high' ? '高' : node.confidence}</small></div>}
        <div className="relation-columns">
          <div><span className="detail-label">前提ノード</span>{prerequisites.length ? prerequisites.map((item) => <button key={item.id} className="relation-chip">← {item.title}</button>) : <span className="relation-empty">なし</span>}</div>
          <div><span className="detail-label">後続ノード</span>{nextNodes.length ? nextNodes.map((item) => <button key={item.id} className="relation-chip">→ {item.title}</button>) : <span className="relation-empty">なし</span>}</div>
        </div>
        {showChecklist && <section className="understanding-checks"><div className="detail-section-heading"><div><span className="detail-kicker">Math Notes</span><h3>理解確認</h3></div><span className="check-count">{Object.values(node.checklist).filter(Boolean).length} / {CONCEPT_CHECKS.length}</span></div>{CONCEPT_CHECKS.map((label, index) => <label className="understanding-check" key={label}><input type="checkbox" checked={Boolean(node.checklist[index])} onChange={(e) => onUpdate({ checklist: { ...node.checklist, [index]: e.target.checked } })} /><span>{label}</span></label>)}</section>}
        {showProof && <ProofReviewPanel node={node} onUpdate={onUpdate} />}
        <div className="node-detail__actions"><button className="btn btn--ghost" onClick={onDuplicate}>ノードを複製</button><button className="btn btn--danger" onClick={requestDelete} disabled={node.type === 'goal'} title={node.type === 'goal' ? '目標ノードは削除できません' : undefined}>ノードを削除</button></div>
      </div>
    </aside>
  )
}
