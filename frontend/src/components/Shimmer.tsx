export function ShimmerBlock({ className = '' }: { className?: string }) {
  return <div className={`shimmer-block ${className}`} aria-hidden />
}

function PageHeaderShimmer() {
  return (
    <header className="space-y-3">
      <ShimmerBlock className="h-9 w-72 max-w-full" />
      <ShimmerBlock className="h-4 w-full max-w-2xl" />
    </header>
  )
}

export function DashboardShimmer() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading dashboard">
      <header className="space-y-3">
        <ShimmerBlock className="h-3 w-36" />
        <ShimmerBlock className="h-9 w-full max-w-xl" />
        <ShimmerBlock className="h-4 w-full max-w-2xl" />
      </header>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="card min-w-0 overflow-hidden p-4 space-y-3">
            <ShimmerBlock className="h-3 w-28" />
            <ShimmerBlock className="h-8 w-20" />
          </div>
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="card p-5 space-y-4">
          <ShimmerBlock className="h-5 w-56" />
          <ShimmerBlock className="h-64 w-full rounded-2xl" />
        </div>
        <div className="card p-5 space-y-4">
          <ShimmerBlock className="h-5 w-40" />
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="rounded-xl bg-[var(--card)] px-3 py-3 space-y-2">
              <ShimmerBlock className="h-4 w-48" />
              <ShimmerBlock className="h-3 w-32" />
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

export function DatasetsShimmer() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading datasets">
      <PageHeaderShimmer />
      <div className="card p-5 space-y-3">
        <div className="flex flex-wrap gap-3">
          <ShimmerBlock className="h-10 w-48" />
          <ShimmerBlock className="h-10 w-24" />
          <ShimmerBlock className="h-10 w-44" />
          <ShimmerBlock className="h-10 w-28" />
        </div>
        <ShimmerBlock className="h-4 w-80 max-w-full" />
      </div>
      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        <div className="card p-4 space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="rounded-xl bg-[var(--card)] p-3 space-y-2">
              <ShimmerBlock className="h-4 w-40" />
              <ShimmerBlock className="h-3 w-28" />
            </div>
          ))}
        </div>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="card p-4 space-y-3">
              <ShimmerBlock className="h-3 w-24" />
              <ShimmerBlock className="h-8 w-16" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export function AnnotationShimmer() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading annotation">
      <PageHeaderShimmer />
      <div className="card p-4 flex flex-wrap gap-3">
        <ShimmerBlock className="h-10 w-56" />
        <ShimmerBlock className="h-6 w-48" />
        <ShimmerBlock className="h-6 w-24" />
      </div>
      <div className="card p-6 space-y-4">
        <ShimmerBlock className="h-3 w-40" />
        <ShimmerBlock className="h-7 w-full" />
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="flex gap-3 rounded-xl bg-[var(--card)] px-3 py-2">
            <ShimmerBlock className="h-8 w-24 rounded-full" />
            <ShimmerBlock className="h-8 w-40" />
            <ShimmerBlock className="h-8 w-24" />
          </div>
        ))}
      </div>
    </div>
  )
}

export function ListCardsShimmer({
  titleWidth = 'w-56',
  rows = 4,
  label = 'Loading',
}: {
  titleWidth?: string
  rows?: number
  label?: string
}) {
  return (
    <div className="space-y-6" aria-busy="true" aria-label={label}>
      <PageHeaderShimmer />
      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="card p-4 space-y-3">
            <ShimmerBlock className={`h-5 ${titleWidth}`} />
            <ShimmerBlock className="h-3 w-48" />
            <ShimmerBlock className="h-20 w-full rounded-xl" />
          </div>
        ))}
      </div>
    </div>
  )
}

export function EvaluationShimmer() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading evaluation">
      <PageHeaderShimmer />
      <div className="card p-5 space-y-4">
        <ShimmerBlock className="h-5 w-40" />
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="grid grid-cols-6 gap-3">
            {Array.from({ length: 6 }).map((__, j) => (
              <ShimmerBlock key={j} className="h-4 w-full" />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

export function ResearchShimmer() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading research">
      <PageHeaderShimmer />
      <div className="card p-5 space-y-3">
        <ShimmerBlock className="h-5 w-72 max-w-full" />
        <ShimmerBlock className="h-4 w-56" />
        <ShimmerBlock className="h-4 w-full max-w-xl" />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        {Array.from({ length: 2 }).map((_, i) => (
          <div key={i} className="card p-5 space-y-3">
            <ShimmerBlock className="h-5 w-40" />
            <ShimmerBlock className="h-10 w-full" />
            <ShimmerBlock className="h-10 w-full" />
            <ShimmerBlock className="h-28 w-full" />
            <ShimmerBlock className="h-10 w-32" />
          </div>
        ))}
      </div>
    </div>
  )
}

export function SettingsShimmer() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading settings">
      <PageHeaderShimmer />
      <div className="card p-5 space-y-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <ShimmerBlock key={i} className="h-4 w-full max-w-lg" />
        ))}
      </div>
    </div>
  )
}

export function TrainingShimmer() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading training">
      <PageHeaderShimmer />
      <div className="card p-5 grid gap-4 md:grid-cols-2">
        <ShimmerBlock className="h-10 w-full" />
        <ShimmerBlock className="h-10 w-full" />
        <ShimmerBlock className="h-6 w-64" />
        <ShimmerBlock className="h-10 w-48 md:col-span-2" />
      </div>
      <div className="card p-5 space-y-3">
        <ShimmerBlock className="h-5 w-40" />
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="rounded-xl bg-[var(--card)] p-3 space-y-2">
            <ShimmerBlock className="h-4 w-56" />
            <ShimmerBlock className="h-3 w-40" />
          </div>
        ))}
      </div>
    </div>
  )
}

export function AnalyzerResultShimmer() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Analyzing text">
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="card p-4 space-y-3">
            <ShimmerBlock className="h-3 w-24" />
            <ShimmerBlock className="h-8 w-16" />
          </div>
        ))}
      </section>
      <section className="grid gap-4 lg:grid-cols-[1.4fr_0.8fr]">
        <div className="card p-5 space-y-4">
          <ShimmerBlock className="h-5 w-40" />
          <ShimmerBlock className="h-40 w-full rounded-2xl" />
        </div>
        <div className="card p-5 space-y-3">
          <ShimmerBlock className="h-5 w-36" />
          <ShimmerBlock className="h-4 w-full" />
          <ShimmerBlock className="h-4 w-5/6" />
          <ShimmerBlock className="h-48 w-full rounded-2xl" />
        </div>
      </section>
    </div>
  )
}
