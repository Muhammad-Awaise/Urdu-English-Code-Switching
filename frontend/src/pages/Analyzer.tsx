import { useMemo, useState } from 'react'
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { api } from '../api'
import { AnalyzerResultShimmer } from '../components/Shimmer'
import StatCard from '../components/StatCard'
import { labelClass } from '../lib/labelStyles'

const EXAMPLES = [
  'Main university mein admission apply kar raha hoon.',
  'Yeh project deadline kal hai.',
  'Please send me the report.',
  'Aaj mausam bohot acha hai.',
]

const COLORS: Record<string, string> = {
  'Roman Urdu': '#1f9d55',
  English: '#2563eb',
  Ambiguous: '#d97706',
  Unknown: '#6b7280',
}

export default function Analyzer() {
  const [text, setText] = useState(EXAMPLES[0])
  const [result, setResult] = useState<any>(null)
  const [selected, setSelected] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [usePrep, setUsePrep] = useState(true)

  const words = useMemo(() => text.trim().split(/\s+/).filter(Boolean).length, [text])

  async function analyze() {
    setLoading(true)
    setError('')
    try {
      const data = await api.analyze(text, usePrep)
      setResult(data)
      setSelected(null)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const pie = result
    ? [
        { name: 'Roman Urdu', value: result.summary.roman_urdu },
        { name: 'English', value: result.summary.english },
        { name: 'Ambiguous', value: result.summary.ambiguous },
        { name: 'Unknown', value: result.summary.unknown },
      ].filter((d) => d.value > 0)
    : []

  return (
    <div className="space-y-6">
      <header className="card overflow-hidden">
        <div
          className="px-6 py-8 text-white"
          style={{
            background:
              'linear-gradient(135deg, #071526 0%, #0b1f3a 45%, #1e4fd6 140%)',
          }}
        >
          <div className="text-xs uppercase tracking-[0.2em] text-blue-200">Urdu-English</div>
          <h2 className="brand-serif text-4xl mt-2">Code-Switching Analyzer</h2>
          <p className="mt-3 max-w-2xl text-blue-100/90">
            Identify Roman Urdu and English words in mixed-language sentences with local inference.
          </p>
        </div>
        <div className="p-6 space-y-4">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={5}
            className="w-full rounded-2xl border border-[var(--line)] bg-[var(--card)] p-4 outline-none focus:border-[var(--royal)]"
            placeholder="Enter mixed Roman Urdu / English text…"
          />
          <div className="flex flex-wrap items-center gap-3 justify-between">
            <div className="text-sm text-[var(--muted)]">
              {text.length} chars · {words} words
            </div>
            <div className="flex flex-wrap gap-2">
              <label className="text-sm flex items-center gap-2 mr-2">
                <input type="checkbox" checked={usePrep} onChange={(e) => setUsePrep(e.target.checked)} />
                Preprocessing
              </label>
              <button
                onClick={() => {
                  setText('')
                  setResult(null)
                  setSelected(null)
                }}
                className="rounded-xl border border-[var(--line)] px-4 py-2"
              >
                Clear
              </button>
              <button
                onClick={analyze}
                disabled={loading || !text.trim()}
                className="rounded-xl bg-[var(--royal)] px-5 py-2 text-white disabled:opacity-60"
              >
                {loading ? 'Analyzing…' : 'Analyze Text'}
              </button>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                onClick={() => setText(ex)}
                className="rounded-full bg-[var(--royal-soft)] px-3 py-1 text-xs text-[var(--royal)]"
              >
                {ex.slice(0, 42)}…
              </button>
            ))}
          </div>
          {error && <p className="text-red-600 text-sm">{error}</p>}
        </div>
      </header>

      {loading && <AnalyzerResultShimmer />}

      {result && !loading && (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Total Words" value={result.summary.total_words} />
            <StatCard label="Roman Urdu" value={result.summary.roman_urdu} accent="var(--urdu)" />
            <StatCard label="English" value={result.summary.english} accent="var(--english)" />
            <StatCard
              label="Code-Switching"
              value={result.code_switching.status}
              accent={result.code_switching.status === 'YES' ? 'var(--royal)' : 'var(--muted)'}
            />
          </section>

          <section className="grid gap-4 lg:grid-cols-[1.4fr_0.8fr]">
            <div className="card p-5">
              <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                <h3 className="font-semibold">Highlighted Tokens</h3>
                <div className="text-xs text-[var(--muted)]">
                  Model: {result.model?.name} ({result.model?.version})
                </div>
              </div>
              <div className="rounded-2xl bg-[var(--card)] p-4 leading-8">
                {result.tokens.map((t: any) => (
                  <span
                    key={`${t.position}-${t.token}`}
                    className={`token-chip ${labelClass(t.label)} ${selected?.position === t.position ? 'active' : ''}`}
                    onClick={() => setSelected(t)}
                  >
                    {t.token}
                  </span>
                ))}
              </div>
              <div className="mt-4 flex flex-wrap gap-3 text-xs">
                <span className={`token-chip ${labelClass('URDU_ROMAN')}`}>Roman Urdu</span>
                <span className={`token-chip ${labelClass('ENGLISH')}`}>English</span>
                <span className={`token-chip ${labelClass('AMBIGUOUS')}`}>Ambiguous</span>
                <span className={`token-chip ${labelClass('UNKNOWN')}`}>Unknown</span>
              </div>
              {selected && (
                <div className="mt-4 rounded-xl border border-[var(--line)] p-4 text-sm">
                  <div className="font-semibold">{selected.token}</div>
                  <div>Label: {selected.label}</div>
                  <div>Confidence: {selected.confidence ?? 'n/a'}</div>
                  <div>Position: {selected.position}</div>
                  <div>Model: {selected.model_version}</div>
                  {selected.alternative && <div>Alternative: {selected.alternative}</div>}
                </div>
              )}
            </div>

            <div className="card p-5 space-y-4">
              <h3 className="font-semibold">Analysis Results</h3>
              <ul className="text-sm space-y-1 text-[var(--muted)]">
                <li>Ambiguous: {result.summary.ambiguous}</li>
                <li>Unknown: {result.summary.unknown}</li>
                <li>Urdu %: {result.summary.urdu_percentage}</li>
                <li>English %: {result.summary.english_percentage}</li>
                <li>Detected: {(result.code_switching.detected_languages || []).join(', ') || '—'}</li>
                <li>
                  Transitions U→E / E→U:{' '}
                  {result.code_switching.transitions.urdu_to_english} /{' '}
                  {result.code_switching.transitions.english_to_urdu}
                </li>
              </ul>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={pie} dataKey="value" nameKey="name" innerRadius={45} outerRadius={70}>
                      {pie.map((entry) => (
                        <Cell key={entry.name} fill={COLORS[entry.name]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <div className="card p-5">
              <h3 className="font-semibold mb-3">Frequent English</h3>
              <div className="flex flex-wrap gap-2">
                {(result.summary.most_frequent_english || []).map(([w, c]: [string, number]) => (
                  <span key={w} className="rounded-full bg-[var(--royal-soft)] px-3 py-1 text-sm">
                    {w} ({c})
                  </span>
                ))}
              </div>
            </div>
            <div className="card p-5">
              <h3 className="font-semibold mb-3">Frequent Roman Urdu</h3>
              <div className="flex flex-wrap gap-2">
                {(result.summary.most_frequent_urdu || []).map(([w, c]: [string, number]) => (
                  <span key={w} className="rounded-full bg-green-50 px-3 py-1 text-sm text-green-700">
                    {w} ({c})
                  </span>
                ))}
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  )
}
