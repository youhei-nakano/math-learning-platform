import { LEARNING_STATUSES, NODE_TYPES } from '../learningMap/constants'
import { layoutNodes } from '../learningMap/graphLayout'

export default function LearningGraph({ goal, nodes, edges, selectedId, mode, onSelect }) {
  const eligible = nodes.filter((node) => node.included !== false)
  const visibleNodes = mode === 'minimal' ? eligible.filter((node) => node.importance === 'required' || node.type === 'goal') : eligible
  const visibleIds = new Set(visibleNodes.map((node) => node.id))
  const visibleEdges = edges.filter((edge) => visibleIds.has(edge.sourceId) && visibleIds.has(edge.targetId))
  const positionedNodes = layoutNodes(visibleNodes, visibleEdges)
  const byId = Object.fromEntries(positionedNodes.map((node) => [node.id, node]))
  const maxX = Math.max(...positionedNodes.map((node) => node.x), 800)
  const maxY = Math.max(...positionedNodes.map((node) => node.y), 300)
  const width = maxX + 240
  const height = maxY + 125

  function hasUnfinishedPrerequisite(node) {
    return edges.filter((edge) => edge.targetId === node.id).some((edge) => nodes.find((item) => item.id === edge.sourceId)?.status !== 'understood')
  }

  return (
    <div className="learning-graph-scroll" aria-label="学習依存グラフ">
      <svg className="learning-graph" style={{ width, height }} viewBox={`0 0 ${width} ${height}`} role="img" aria-labelledby="graph-title graph-desc">
        <title id="graph-title">{goal}の学習依存グラフ</title>
        <desc id="graph-desc">左側の前提から右側の目標へ進みます。ノードを選ぶと詳細と専用メモを編集できます。</desc>
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" /></marker>
        </defs>
        <g className="graph-edges">
          {visibleEdges.map((edge) => {
            const start = byId[edge.sourceId]
            const end = byId[edge.targetId]
            const highlighted = start.importance === 'required' && end.importance === 'required'
            return <path key={edge.id} className={`graph-edge${highlighted ? ' recommended' : ''}${edge.confirmationStatus === 'unconfirmed' ? ' unconfirmed' : ''}`} d={`M ${start.x + 190} ${start.y + 44} C ${start.x + 220} ${start.y + 44}, ${end.x - 30} ${end.y + 44}, ${end.x} ${end.y + 44}`} markerEnd="url(#arrow)" />
          })}
        </g>
        {positionedNodes.map((node) => {
          const type = NODE_TYPES[node.type]
          const status = LEARNING_STATUSES[node.status]
          const blocked = hasUnfinishedPrerequisite(node)
          return (
            <g key={node.id} className={`graph-node importance-${node.importance ?? 'required'} status-${node.status} type-${node.type}${blocked ? ' blocked' : ''}${selectedId === node.id ? ' selected' : ''}${node.notes?.trim() ? ' has-notes' : ''}`} transform={`translate(${node.x} ${node.y})`} role="button" tabIndex="0" aria-label={`${node.title}、${type.label}、${status.label}${blocked ? '、未完了の前提あり' : ''}${node.notes?.trim() ? '、メモあり' : ''}`} onClick={() => onSelect(node.id)} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelect(node.id) } }}>
              <rect width="190" height="88" rx="13" />
              <text className="node-type" x="14" y="22">{type.icon} {type.label}</text>
              <text className="node-title" x="14" y="48">{node.title.length > 16 ? `${node.title.slice(0, 16)}…` : node.title}</text>
              <text className="node-status" x="14" y="72">{status.symbol} {status.label}</text>
              {blocked && <text className="node-blocked" x="176" y="22" textAnchor="end">⚠ 前提</text>}
              {node.notes?.trim() && <text className="node-memo-indicator" x="176" y="72" textAnchor="end">● メモ</text>}
            </g>
          )
        })}
      </svg>
    </div>
  )
}
