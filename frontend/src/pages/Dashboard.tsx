import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api'
import { DashboardShimmer } from '../components/Shimmer'
import StatCard from '../components/StatCard'
import { formatMetric } from '../lib/format'

export default function Dashboard() {
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.dashboard().then(setData).catch((e) => setError(e.message))
  }, [])

  if (error) return <p className="text-red-600">{error}</p>
  if (!data) return <DashboardShimmer />

  const cards = data.cards
  const langData = Object.entries(data.language_distribution || {}).map(([name, value]) => ({
    name,
    value,
  }))

  return (
    <div className="space-y-6">
      <header>
        <div className="text-sm text-[var(--muted)]">Research Dashboard</div>
        <h2 className="brand-serif text-3xl mt-1">Urdu-English Code-Switching Analyzer</h2>
        <p className="text-[var(--muted)] mt-2 max-w-3xl">
          Detecting Urdu and English in mixed-language text — local models only, no paid APIs.
        </p>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Dataset Sentences" value={cards.total_dataset_sentences} />
        <StatCard label="Annotated Tokens" value={cards.total_annotated_tokens} />
        <StatCard label="Roman Urdu Tokens" value={cards.roman_urdu_tokens} accent="var(--urdu)" />
        <StatCard label="English Tokens" value={cards.english_tokens} accent="var(--english)" />
        <StatCard label="Trained Models" value={cards.trained_models} />
        <StatCard label="Experiments" value={cards.completed_experiments} />
        <StatCard
          label="Best Macro F1"
          value={cards.best_macro_f1 == null ? 'n/a' : formatMetric(cards.best_macro_f1)}
          compact={false}
        />
        <StatCard
          label="Active Model"
          value={`${cards.active_model?.name || 'dictionary-baseline'}`}
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="card p-5">
          <h3 className="font-semibold mb-4">Language Distribution (annotated)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={langData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#d7e0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#1e4fd6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="card p-5">
          <h3 className="font-semibold mb-4">Model Comparison</h3>
          {(data.model_comparison || []).length === 0 ? (
            <p className="text-sm text-[var(--muted)]">
              No trained models yet. Dictionary baseline is active for inference.
            </p>
          ) : (
            <div className="space-y-3">
              {data.model_comparison.map((m: any) => (
                <div key={m.id} className="flex items-center justify-between rounded-xl bg-[var(--card)] px-3 py-2">
                  <div>
                    <div className="font-medium">{m.name}</div>
                    <div className="text-xs text-[var(--muted)]">{m.architecture} · {m.version}</div>
                  </div>
                  <div className="text-sm tabular-nums">Macro F1: {formatMetric(m.macro_f1)}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
