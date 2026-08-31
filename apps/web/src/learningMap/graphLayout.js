export function layoutNodes(nodes, edges) {
  const included = nodes.filter((node) => node.included !== false)
  const ids = new Set(included.map((node) => node.id))
  const incoming = Object.fromEntries(included.map((node) => [node.id, []]))
  edges.filter((edge) => ids.has(edge.sourceId) && ids.has(edge.targetId)).forEach((edge) => incoming[edge.targetId].push(edge.sourceId))
  const memo = {}
  const visiting = new Set()
  function depth(id) {
    if (memo[id] !== undefined) return memo[id]
    if (visiting.has(id)) return 0
    visiting.add(id)
    memo[id] = incoming[id].length ? 1 + Math.max(...incoming[id].map(depth)) : 0
    visiting.delete(id)
    return memo[id]
  }
  const columns = {}
  included.forEach((node) => { const d = depth(node.id); (columns[d] ??= []).push(node) })
  return included.map((node) => {
    const d = depth(node.id); const index = columns[d].findIndex((item) => item.id === node.id)
    return { ...node, x: 45 + d * 245, y: 28 + index * 112 }
  })
}
