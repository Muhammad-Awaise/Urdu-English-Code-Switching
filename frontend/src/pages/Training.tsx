import { useEffect, useState } from 'react'
import { api } from '../api'
import { TrainingShimmer } from '../components/Shimmer'

export default function Training() {
  const [datasets, setDatasets] = useState<any[]>([])
  const [versionId, setVersionId] = useState<number | null>(null)
  const [modelType, setModelType] = useState('logreg')
  const [jobs, setJobs] = useState<any[]>([])
  const [message, setMessage] = useState('')
  const [confirmLarge, setConfirmLarge] = useState(false)
  const [loading, setLoading] = useState(true)

  async function refreshJobs() {
    const data = await api.jobs()
    setJobs(data.jobs || [])
  }

  useEffect(() => {
    setLoading(true)
    Promise.all([
      api.datasets().then((d) => {
        setDatasets(d.datasets || [])
        const ver = d.datasets?.[0]?.latest_version?.id
        if (ver) setVersionId(ver)
      }),
      refreshJobs(),
    ])
      .catch(() => undefined)
      .finally(() => setLoading(false))
    const t = setInterval(() => refreshJobs().catch(() => undefined), 2500)
    return () => clearInterval(t)
  }, [])

  if (loading) return <TrainingShimmer />

  return (
    <div className="space-y-6">
      <header>
        <h2 className="brand-serif text-3xl">Model Training Laboratory</h2>
        <p className="text-[var(--muted)] mt-1">
          Local CPU training only. Analyzer stays available while jobs run in a background thread.
        </p>
      </header>

      <div className="card p-5 grid gap-4 md:grid-cols-2">
        <div>
          <label className="text-xs text-[var(--muted)]">Dataset version</label>
          <select
            className="mt-1 w-full rounded-xl border border-[var(--line)] px-3 py-2"
            value={versionId ?? ''}
            onChange={(e) => setVersionId(Number(e.target.value))}
          >
            {datasets.map((d) => (
              <option key={d.id} value={d.latest_version?.id}>
                {d.name} ({d.latest_version?.version})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-[var(--muted)]">Model type</label>
          <select
            className="mt-1 w-full rounded-xl border border-[var(--line)] px-3 py-2"
            value={modelType}
            onChange={(e) => setModelType(e.target.value)}
          >
            <option value="logreg">TF-IDF + Logistic Regression</option>
            <option value="linearsvm">TF-IDF + Linear SVM</option>
            <option value="naive_bayes">Naive Bayes</option>
          </select>
        </div>
        <label className="text-sm flex items-center gap-2 md:col-span-2">
          <input type="checkbox" checked={confirmLarge} onChange={(e) => setConfirmLarge(e.target.checked)} />
          Confirm large run if dataset is big (&gt;5000 tokens)
        </label>
        <button
          className="rounded-xl bg-[var(--royal)] text-white px-4 py-2 md:col-span-2"
          onClick={async () => {
            if (!versionId) return
            try {
              const res = await api.startTraining({
                dataset_version_id: versionId,
                model_type: modelType,
                confirm_large_run: confirmLarge,
                word_ngram_range: [1, 1],
                char_ngram_range: [2, 5],
                use_char: true,
                use_word: true,
                random_seed: 42,
              })
              setMessage(`Started job ${res.job_id}`)
              await refreshJobs()
            } catch (e: any) {
              setMessage(e.message)
            }
          }}
        >
          Start local training
        </button>
        {message && <p className="text-sm text-[var(--royal)] md:col-span-2">{message}</p>}
      </div>

      <div className="card p-5">
        <h3 className="font-semibold mb-3">Training jobs</h3>
        <div className="space-y-3">
          {jobs.map((j) => (
            <div key={j.job_id} className="rounded-xl bg-[var(--card)] p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <div className="font-medium">{j.job_id} · {j.model_type}</div>
                  <div className="text-xs text-[var(--muted)]">
                    {j.status} / {j.stage} · progress {(j.progress * 100).toFixed(0)}%
                  </div>
                </div>
                {['QUEUED', 'PREPARING', 'TRAINING', 'VALIDATING', 'EVALUATING'].includes(j.status) && (
                  <button
                    className="rounded-lg border border-[var(--line)] px-3 py-1 text-sm"
                    onClick={() => api.cancelJob(j.job_id).then(refreshJobs)}
                  >
                    Cancel
                  </button>
                )}
              </div>
              {j.error_log && (
                <pre className="mt-2 max-h-40 overflow-auto text-xs text-red-700">{j.error_log}</pre>
              )}
              {j.metrics?.test && (
                <div className="mt-2 text-sm">
                  Test macro F1: {j.metrics.test.macro_f1?.toFixed?.(4) ?? j.metrics.test.macro_f1}
                </div>
              )}
            </div>
          ))}
          {!jobs.length && <p className="text-sm text-[var(--muted)]">No jobs yet.</p>}
        </div>
      </div>
    </div>
  )
}
