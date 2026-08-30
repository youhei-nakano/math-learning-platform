import { useMemo } from 'react'
import { renderLatexToHtml } from '../utils/latexRenderer'

export default function LatexPreview({ content }) {
  const html = useMemo(() => renderLatexToHtml(content), [content])

  if (!content.trim()) {
    return (
      <div className="latex-preview latex-preview--empty">
        <span className="latex-preview-placeholder">LaTeXプレビュー</span>
      </div>
    )
  }

  return (
    <div
      className="latex-preview"
      aria-label="LaTeXプレビュー"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
