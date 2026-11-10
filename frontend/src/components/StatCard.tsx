import { formatCompactCount } from '../lib/format'

export default function StatCard({
  label,
  value,
  accent,
  compact = true,
}: {
  label: string
  value: string | number | null | undefined
  accent?: string
  /** When true (default), large numbers show as 1.2K / 3.4M */
  compact?: boolean
}) {
  const raw = value ?? '—'
  const isNumeric =
    typeof value === 'number' ||
    (typeof value === 'string' && value.trim() !== '' && Number.isFinite(Number(value)))

  const display =
    compact && isNumeric ? formatCompactCount(value) : raw == null ? '—' : String(raw)
  const title = isNumeric ? String(value) : display
  const isLongText = typeof value === 'string' && !isNumeric && value.length > 12

  return (
    <div className="card min-w-0 overflow-hidden p-4">
      <div className="text-xs uppercase tracking-wide text-[var(--muted)]">{label}</div>
      <div
        className={`mt-2 font-semibold tabular-nums break-words [overflow-wrap:anywhere] ${
          isLongText ? 'text-lg leading-snug' : 'text-2xl'
        }`}
        style={{ color: accent || 'var(--ink)' }}
        title={title}
      >
        {display}
      </div>
    </div>
  )
}
