import katex from 'katex'

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function renderMath(latex, displayMode) {
  try {
    return katex.renderToString(latex.trim(), {
      displayMode,
      throwOnError: false,
      strict: false,
      trust: false,
      output: 'html',
    })
  } catch {
    return `<span class="latex-error">${escapeHtml(latex)}</span>`
  }
}

const MATH_DELIMITER_PATTERN =
  /(\$\$[\s\S]+?\$\$|\\\[[\s\S]+?\\\]|\$[^$\n]+?\$|\\\([\s\S]+?\\\))/g

function parseMathToken(token) {
  if (token.startsWith('$$')) {
    return { type: 'display', value: token.slice(2, -2) }
  }
  if (token.startsWith('\\[')) {
    return { type: 'display', value: token.slice(2, -2) }
  }
  if (token.startsWith('\\(')) {
    return { type: 'inline', value: token.slice(2, -2) }
  }
  if (token.startsWith('$')) {
    return { type: 'inline', value: token.slice(1, -1) }
  }
  return { type: 'text', value: token }
}

function splitLatexSegments(text) {
  const segments = []
  let lastIndex = 0
  let match

  while ((match = MATH_DELIMITER_PATTERN.exec(text)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ type: 'text', value: text.slice(lastIndex, match.index) })
    }
    segments.push(parseMathToken(match[0]))
    lastIndex = MATH_DELIMITER_PATTERN.lastIndex
  }

  if (lastIndex < text.length) {
    segments.push({ type: 'text', value: text.slice(lastIndex) })
  }

  if (segments.length === 0) {
    segments.push({ type: 'display', value: text })
  }

  return segments
}

function hasMathDelimiters(text) {
  return /(\$\$|\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\))/.test(text)
}

function renderTextSegment(value) {
  const lines = value.split('\n')
  return lines
    .map((line, index) => {
      const content = line ? `<span class="latex-text">${escapeHtml(line)}</span>` : ''
      return index < lines.length - 1 ? `${content}<br />` : content
    })
    .join('')
}

export function renderLatexToHtml(content) {
  const trimmed = content.trim()
  if (!trimmed) return ''

  const segments = hasMathDelimiters(trimmed)
    ? splitLatexSegments(trimmed)
    : [{ type: 'display', value: trimmed }]

  return segments
    .map((segment) => {
      if (segment.type === 'text') {
        return renderTextSegment(segment.value)
      }
      if (segment.type === 'display') {
        return `<div class="latex-display">${renderMath(segment.value, true)}</div>`
      }
      return `<span class="latex-inline">${renderMath(segment.value, false)}</span>`
    })
    .join('')
}
