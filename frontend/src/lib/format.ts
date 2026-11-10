/** Compact large counts for card displays: 1250 → 1.3K, 2_500_000 → 2.5M */
export function formatCompactCount(value: string | number | null | undefined): string {
  if (value == null || value === '') return '—'
  if (typeof value === 'string' && Number.isNaN(Number(value))) return value
  const n = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(n)) return String(value)
  const abs = Math.abs(n)
  const sign = n < 0 ? '-' : ''
  if (abs >= 1_000_000) {
    const v = abs / 1_000_000
    return `${sign}${trimDecimals(v)}M`
  }
  if (abs >= 1_000) {
    const v = abs / 1_000
    return `${sign}${trimDecimals(v)}K`
  }
  if (Number.isInteger(n)) return String(n)
  return n.toFixed(2)
}

function trimDecimals(v: number): string {
  if (v >= 100) return String(Math.round(v))
  if (v >= 10) return v.toFixed(1).replace(/\.0$/, '')
  return v.toFixed(1).replace(/\.0$/, '')
}

/** Metric scores / seconds with stable short precision */
export function formatMetric(value: string | number | null | undefined, digits = 3): string {
  if (value == null || value === '') return '—'
  const n = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(n)) return String(value)
  return n.toFixed(digits)
}
