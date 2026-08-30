import { useState } from 'react'
import { reviewProofSteps } from '../learningMap/mockLearningServices'

export default function ProofReviewPanel({ node, onUpdate }) {
  const [reviews, setReviews] = useState([])
  const [reviewed, setReviewed] = useState(false)

  function updateStep(stepId, field, value) {
    onUpdate({ proofSteps: node.proofSteps.map((step) => step.id === stepId ? { ...step, [field]: value } : step) })
  }

  function addStep() {
    onUpdate({ proofSteps: [...node.proofSteps, { id: crypto.randomUUID(), claim: '', grounds: '', explanation: '' }] })
  }

  async function runDemoReview() {
    setReviews(await reviewProofSteps(node.id, node.proofSteps))
    setReviewed(true)
  }

  function toggleResolved(reviewId) {
    const exists = node.resolvedReviewIds.includes(reviewId)
    onUpdate({ resolvedReviewIds: exists ? node.resolvedReviewIds.filter((id) => id !== reviewId) : [...node.resolvedReviewIds, reviewId] })
  }

  return (
    <section className="proof-panel">
      <div className="detail-section-heading"><div><span className="detail-kicker">Proof workspace</span><h3>証明ステップ</h3></div><button className="btn btn--ghost btn--compact" onClick={addStep}>＋ ステップ</button></div>
      <p className="review-disclaimer">このレビューは、論理の飛躍や根拠不足の可能性を指摘するものです。指摘がないことは、証明の完全な正しさを保証しません。</p>
      <div className="proof-steps">
        {node.proofSteps.map((step, index) => (
          <div className="proof-step" key={step.id}>
            <span className="proof-step__number">{index + 1}</span>
            <label>ステップの主張<textarea value={step.claim} onChange={(e) => updateStep(step.id, 'claim', e.target.value)} /></label>
            <label>根拠として使用した定義・定理<input value={step.grounds} onChange={(e) => updateStep(step.id, 'grounds', e.target.value)} /></label>
            <label>補足説明<textarea value={step.explanation} onChange={(e) => updateStep(step.id, 'explanation', e.target.value)} /></label>
          </div>
        ))}
      </div>
      <button className="btn btn--primary demo-review-button" onClick={runDemoReview}>デモレビューを表示</button>
      {reviewed && <div className="review-results">
        <div className="review-results__title"><h4>デモ指摘</h4><span>{reviews.length}件</span></div>
        {reviews.length === 0 ? <p className="empty-review">このノード用のデモ指摘はありません（正しさを保証するものではありません）。</p> : reviews.map((review) => {
          const stepIndex = node.proofSteps.findIndex((step) => step.id === review.stepId)
          const resolved = node.resolvedReviewIds.includes(review.id)
          return <article className={`review-card${resolved ? ' resolved' : ''}`} key={review.id}>
            <div className="review-card__top"><span className="review-severity">{review.severity}</span><strong>ステップ {stepIndex + 1} · {review.type}</strong></div>
            <p>{review.description}</p><p className="review-check"><b>確認:</b> {review.check}</p>
            <label className="review-resolved"><input type="checkbox" checked={resolved} onChange={() => toggleResolved(review.id)} /> 解決済みにする</label>
          </article>
        })}
      </div>}
    </section>
  )
}
