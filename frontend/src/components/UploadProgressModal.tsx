import { useEffect, useState } from 'react'
import { ShimmerBlock } from './Shimmer'

function formatElapsed(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return m > 0 ? `${m}m ${s.toString().padStart(2, '0')}s` : `${s}s`
}

export default function UploadProgressModal({
  open,
  fileName,
  done,
  progressPct,
  stage,
}: {
  open: boolean
  fileName?: string
  done?: boolean
  /** Real server progress 0–100 when available */
  progressPct?: number | null
  stage?: string | null
}) {
  const [elapsed, setElapsed] = useState(0)
  const hasServerProgress = typeof progressPct === 'number'

  useEffect(() => {
    if (!open) {
      setElapsed(0)
      return
    }
    const id = window.setInterval(() => setElapsed((e) => e + 1), 1000)
    return () => window.clearInterval(id)
  }, [open])

  if (!open) return null

  const pct = done ? 100 : hasServerProgress ? Math.max(1, Math.min(99, progressPct)) : null
  const label = done ? 'Complete' : stage || 'Processing upload…'

  return (
    <div
      className="fixed inset-0 z-[80] flex items-center justify-center p-4"
      style={{ background: 'rgba(7, 21, 38, 0.55)', backdropFilter: 'blur(4px)' }}
      role="dialog"
      aria-modal="true"
      aria-label="Upload progress"
    >
      <div className="card w-full max-w-lg overflow-hidden shadow-2xl">
        <div
          className="px-5 py-4 text-white"
          style={{ background: 'linear-gradient(135deg, #071526 0%, #0b1f3a 55%, #1e4fd6 140%)' }}
        >
          <div className="text-xs uppercase tracking-[0.18em] text-blue-200">Dataset upload</div>
          <h3 className="brand-serif text-2xl mt-1">Analyzing your file</h3>
          <p className="text-sm text-blue-100/85 mt-1 break-all">{fileName || 'Selected file'}</p>
        </div>

        <div className="p-5 space-y-4">
          <div className="flex items-center justify-between gap-3 text-sm">
            <span className="text-[var(--muted)]">{label}</span>
            <span className="font-semibold text-[var(--royal)] whitespace-nowrap">
              {done ? '100%' : pct != null ? `${Math.round(pct)}%` : 'Working…'}
            </span>
          </div>

          <div className="h-3 w-full overflow-hidden rounded-full bg-[var(--royal-soft)]">
            {pct == null && !done ? (
              <div className="upload-indeterminate h-full w-1/3 rounded-full bg-[var(--royal)]" />
            ) : (
              <div
                className="h-full rounded-full transition-[width] duration-300 ease-out"
                style={{
                  width: `${done ? 100 : pct}%`,
                  background: 'linear-gradient(90deg, #1e4fd6, #4f7df3)',
                }}
              />
            )}
          </div>

          <div className="flex items-center justify-between text-xs text-[var(--muted)]">
            <span>Elapsed: {formatElapsed(elapsed)}</span>
            <span>{hasServerProgress ? 'Live import progress' : 'Preparing…'}</span>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-[var(--card)] p-3 space-y-2">
              <ShimmerBlock className="h-3 w-16" />
              <ShimmerBlock className="h-6 w-10" />
            </div>
            <div className="rounded-xl bg-[var(--card)] p-3 space-y-2">
              <ShimmerBlock className="h-3 w-20" />
              <ShimmerBlock className="h-6 w-12" />
            </div>
            <div className="rounded-xl bg-[var(--card)] p-3 space-y-2">
              <ShimmerBlock className="h-3 w-14" />
              <ShimmerBlock className="h-6 w-10" />
            </div>
          </div>

          <p className="text-xs text-[var(--muted)] leading-relaxed">
            Large files (thousands to 100k+ rows) import in the background with chunked fast labeling
            so the app stays responsive.
          </p>
        </div>
      </div>
    </div>
  )
}
