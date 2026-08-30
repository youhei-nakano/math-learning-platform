import { useCallback, useEffect, useMemo, useState } from 'react'
import { loadLearningMaps, saveLearningMaps } from '../learningMap/mapStore'

export function useLearningMaps() {
  const [data, setData] = useState(loadLearningMaps)
  const [saveState, setSaveState] = useState({ status: 'saved', message: '' })
  const [saveAttempt, setSaveAttempt] = useState(0)
  useEffect(() => {
    setSaveState({ status: 'saving', message: '' })
    try {
      saveLearningMaps(data)
      const timer = window.setTimeout(() => setSaveState({ status: 'saved', message: '' }), 250)
      return () => window.clearTimeout(timer)
    } catch {
      setSaveState({ status: 'error', message: 'このブラウザに保存できませんでした。空き容量またはプライベートブラウズ設定を確認してください。' })
    }
    return undefined
  }, [data, saveAttempt])
  const activeMap = useMemo(() => data.maps.find((map) => map.id === data.activeMapId) ?? null, [data])
  const selectMap = useCallback((id) => setData((current) => ({ ...current, activeMapId: id })), [])
  const upsertMap = useCallback((map) => setData((current) => {
    const exists = current.maps.some((item) => item.id === map.id)
    return { ...current, activeMapId: map.id, maps: exists ? current.maps.map((item) => item.id === map.id ? map : item) : [...current.maps, map] }
  }), [])
  const updateActiveMap = useCallback((updater) => setData((current) => ({ ...current, maps: current.maps.map((map) => map.id === current.activeMapId ? (typeof updater === 'function' ? updater(map) : { ...map, ...updater }) : map) })), [])
  const updateNode = useCallback((id, updates) => updateActiveMap((map) => ({ ...map, updatedAt: new Date().toISOString(), nodes: map.nodes.map((node) => node.id === id ? { ...node, ...updates } : node) })), [updateActiveMap])
  const retrySave = useCallback(() => setSaveAttempt((value) => value + 1), [])
  return { maps: data.maps, activeMap, selectMap, upsertMap, updateActiveMap, updateNode, saveState, retrySave }
}
