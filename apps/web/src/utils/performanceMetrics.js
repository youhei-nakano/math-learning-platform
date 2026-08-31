export function observeWebPerformance() {
  if (typeof window === 'undefined' || !('performance' in window)) return
  const metrics = { startedAt: new Date().toISOString() }
  window.__MATH_NOTES_PERFORMANCE__ = metrics

  const record = (name, value) => {
    metrics[name] = Math.round(value)
    window.dispatchEvent(new CustomEvent('math-notes:performance', { detail: { ...metrics } }))
  }

  try {
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === 'first-contentful-paint') record('fcpMs', entry.startTime)
      }
    }).observe({ type: 'paint', buffered: true })
    new PerformanceObserver((list) => {
      const last = list.getEntries().at(-1)
      if (last) record('lcpMs', last.startTime)
    }).observe({ type: 'largest-contentful-paint', buffered: true })
  } catch { /* Older browsers still receive navigation metrics below. */ }

  window.addEventListener('load', () => {
    const navigation = performance.getEntriesByType('navigation')[0]
    if (!navigation) return
    const resources = performance.getEntriesByType('resource')
    record('transferredBytes', navigation.transferSize + resources.reduce((sum, entry) => sum + (entry.transferSize || 0), 0))
    record('decodedBytes', navigation.decodedBodySize + resources.reduce((sum, entry) => sum + (entry.decodedBodySize || 0), 0))
    record('domInteractiveMs', navigation.domInteractive)
    record('loadMs', navigation.loadEventEnd || performance.now())
  }, { once: true })
}
