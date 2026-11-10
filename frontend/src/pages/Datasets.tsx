import { useEffect, useState } from 'react'
import { api } from '../api'
import { RippleButton, RippleLabel } from '../components/RippleButton'
import { DatasetsShimmer } from '../components/Shimmer'
import StatCard from '../components/StatCard'
import UploadProgressModal from '../components/UploadProgressModal'

export default function Datasets() {
  const [datasets, setDatasets] = useState<any[]>([])
  const [selected, setSelected] = useState<number | null>(null)
  const [stats, setStats] = useState<any>(null)
  const [validation, setValidation] = useState<any>(null)
  const [name, setName] = useState('')
  const [message, setMessage] = useState('')
  const [uploadResult, setUploadResult] = useState<any>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadDone, setUploadDone] = useState(false)
  const [uploadFileName, setUploadFileName] = useState('')
  const [uploadProgress, setUploadProgress] = useState<number | null>(null)
  const [uploadStage, setUploadStage] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function refresh(preferId?: number) {
    const data = await api.datasets()
    const list = data.datasets || []
    setDatasets(list)
    setSelected((current) => {
      if (preferId && list.some((d: any) => d.id === preferId)) return preferId
      if (current && list.some((d: any) => d.id === current)) return current
      return list[0]?.id ?? null
    })
  }

  useEffect(() => {
    setLoading(true)
    refresh()
      .catch((e) => setMessage(e.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    const ds = datasets.find((d) => d.id === selected)
    setStats(ds?.latest_version?.stats || null)
  }, [selected, datasets])

  const hasSelection = selected != null

  if (loading) return <DatasetsShimmer />

  return (
    <div className="space-y-6">
      <UploadProgressModal
        open={uploading || uploadDone}
        fileName={uploadFileName}
        done={uploadDone}
        progressPct={uploadProgress}
        stage={uploadStage}
      />
      <header>
        <h2 className="brand-serif text-3xl">Dataset Management</h2>
        <p className="text-[var(--muted)] mt-1">Import, validate, clean, and split annotated corpora locally.</p>
      </header>

      <div className="card p-5 space-y-3">
        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="text-xs text-[var(--muted)]">New dataset name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="block mt-1 rounded-xl border border-[var(--line)] px-3 py-2"
              placeholder="e.g. my_reviews"
            />
          </div>
          <RippleButton
            variant="primary"
            disabled={!name.trim()}
            onClick={async () => {
              try {
                const created = await api.createDataset({
                  name: name.trim(),
                  description: 'User dataset',
                  license_note: 'user-provided',
                })
                setName('')
                await refresh(created.id)
                setMessage(`Dataset "${created.name}" created. Upload is enabled now.`)
              } catch (err: any) {
                setMessage(err.message || 'Create failed. Is the backend running on port 8000?')
              }
            }}
          >
            Create
          </RippleButton>
          <RippleLabel
            className={!hasSelection || uploading ? 'opacity-60 pointer-events-none' : ''}
            title={!hasSelection ? 'Create or select a dataset first' : 'Upload a file into the selected dataset'}
          >
            {uploading ? 'Analyzing upload…' : 'Upload CSV/JSON/Excel'}
            <input
              type="file"
              accept=".csv,.json,.jsonl,.xlsx,.xls"
              className="hidden"
              disabled={!hasSelection || uploading}
              onChange={async (e) => {
                const file = e.target.files?.[0]
                if (!file || !selected) return
                setUploadFileName(file.name)
                setUploadDone(false)
                setUploading(true)
                setUploadProgress(2)
                setUploadStage('Uploading file…')
                setMessage('')
                try {
                  const res = await api.uploadDataset(selected, file)

                  // Large files return an async job — poll live progress
                  if (res.async && res.job_id) {
                    setUploadStage(res.message || 'Background import started…')
                    let finalResult: any = null
                    for (;;) {
                      const job = await api.importJob(res.job_id)
                      setUploadProgress(Math.round((job.progress || 0) * 100))
                      setUploadStage(job.stage || 'Processing…')
                      if (job.status === 'COMPLETED') {
                        finalResult = job.result
                        break
                      }
                      if (job.status === 'FAILED') {
                        throw new Error(job.error || 'Import job failed')
                      }
                      await new Promise((r) => setTimeout(r, 800))
                    }
                    setUploadDone(true)
                    setUploadProgress(100)
                    setUploadResult(finalResult)
                    setMessage(
                      `Imported ${finalResult?.added ?? 0} rows from ${file.name} (fast bulk mode).`
                    )
                  } else {
                    setUploadProgress(100)
                    setUploadDone(true)
                    setUploadResult(res)
                    setMessage(
                      `Imported ${res.added} rows from ${res.source_file || file.name}. ` +
                        `Auto-labeled ${res.auto_labeled_sentences ?? 0}; kept gold labels on ${res.preserved_gold_sentences ?? 0}.`
                    )
                  }
                  await refresh(selected)
                  window.setTimeout(() => {
                    setUploading(false)
                    setUploadDone(false)
                    setUploadFileName('')
                    setUploadProgress(null)
                    setUploadStage(null)
                  }, 800)
                } catch (err: any) {
                  setMessage(err.message || 'Upload failed')
                  setUploadResult(null)
                  setUploading(false)
                  setUploadDone(false)
                  setUploadProgress(null)
                  setUploadStage(null)
                } finally {
                  e.target.value = ''
                }
              }}
            />
          </RippleLabel>
          <RippleButton
            variant="ghost"
            disabled={!hasSelection}
            onClick={async () => setValidation(await api.validateDataset(selected!))}
          >
            Validate
          </RippleButton>
          <RippleButton
            variant="ghost"
            disabled={!hasSelection}
            onClick={async () => {
              const res = await api.splitDataset(selected!, {
                train_ratio: 0.7,
                val_ratio: 0.15,
                test_ratio: 0.15,
                seed: 42,
              })
              setMessage(`Split groups train/val/test: ${res.train_groups}/${res.val_groups}/${res.test_groups}`)
              await refresh(selected!)
            }}
          >
            Split 70/15/15
          </RippleButton>
          <RippleButton
            variant="ghost"
            disabled={!hasSelection}
            onClick={async () => {
              const res = await api.cleanDataset(selected!, { remove_empty: true, remove_duplicates: false })
              setMessage(`Cleaning actions: ${res.actions.length}`)
              await refresh(selected!)
            }}
          >
            Clean empties
          </RippleButton>
        </div>
        {!hasSelection && (
          <p className="text-sm text-[var(--muted)]">
            Upload is available after you <strong className="text-[var(--ink)]">Create</strong> a dataset
            or click one in the list below.
          </p>
        )}
        {hasSelection && (
          <p className="text-sm text-[var(--muted)]">
            Selected dataset id: <strong className="text-[var(--ink)]">{selected}</strong>
            {' · '}
            {datasets.find((d) => d.id === selected)?.name}
          </p>
        )}
      </div>

      {message && <p className="text-sm text-[var(--royal)] break-words">{message}</p>}

      {uploadResult?.analysis && (
        <div className="card p-5 space-y-3">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <h3 className="font-semibold">Upload analysis results</h3>
              <p className="text-xs text-[var(--muted)] mt-1">
                Generated for this file: {uploadResult.source_file || 'upload'} · model{' '}
                {uploadResult.analysis.model?.name} ({uploadResult.analysis.model?.source})
              </p>
            </div>
            <p className="text-xs text-[var(--muted)] max-w-md">{uploadResult.analysis.note}</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Sentences analyzed" value={uploadResult.analysis.sentences_analyzed} />
            <StatCard label="Code-switching YES" value={uploadResult.analysis.code_switching_yes} accent="var(--royal)" />
            <StatCard label="Code-switching NO" value={uploadResult.analysis.code_switching_no} />
            <StatCard label="Insufficient evidence" value={uploadResult.analysis.code_switching_insufficient} />
            <StatCard label="Roman Urdu tokens" value={uploadResult.analysis.roman_urdu_tokens} accent="var(--urdu)" />
            <StatCard label="English tokens" value={uploadResult.analysis.english_tokens} accent="var(--english)" />
            <StatCard label="Ambiguous tokens" value={uploadResult.analysis.ambiguous_tokens} accent="var(--ambiguous)" />
            <StatCard label="Unknown tokens" value={uploadResult.analysis.unknown_tokens} />
          </div>
          <p className="text-sm text-[var(--muted)]">
            Open <strong className="text-[var(--ink)]">Annotation</strong> to review every sentence from this upload,
            or check the dataset stats cards below.
          </p>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        <div className="card min-w-0 overflow-hidden p-4 space-y-2">
          <div className="text-xs uppercase tracking-wide text-[var(--muted)] mb-1">Datasets</div>
          {datasets.length === 0 && (
            <p className="text-sm text-[var(--muted)]">
              No datasets loaded. Click Create, or check that the API is running.
            </p>
          )}
          {datasets.map((d) => (
            <RippleButton
              key={d.id}
              variant="ghost"
              title={d.name}
              onClick={() => setSelected(d.id)}
              className={`!block w-full min-w-0 !justify-start !items-start text-left h-auto py-2 ${
                selected === d.id ? '!bg-[var(--royal-soft)] !border-[var(--royal)]' : ''
              }`}
            >
              <span className="block min-w-0">
                <span className="block font-medium break-words [overflow-wrap:anywhere]">{d.name}</span>
                <span className="block text-xs text-[var(--muted)] break-words [overflow-wrap:anywhere]">
                  {d.license_note || d.source || 'local'}
                </span>
              </span>
            </RippleButton>
          ))}
        </div>
        <div className="space-y-4">
          {stats ? (
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <StatCard label="Sentences" value={stats.total_sentences} />
              <StatCard label="Tokens" value={stats.total_tokens} />
              <StatCard label="Roman Urdu" value={stats.roman_urdu_tokens} accent="var(--urdu)" />
              <StatCard label="English" value={stats.english_tokens} accent="var(--english)" />
              <StatCard label="Ambiguous" value={stats.ambiguous_tokens} accent="var(--ambiguous)" />
              <StatCard label="Mixed sentences" value={stats.mixed_language_sentences} />
              <StatCard label="Duplicates" value={stats.duplicate_records} />
              <StatCard label="Unlabeled" value={stats.unlabeled_sentences} />
            </div>
          ) : (
            <p className="text-[var(--muted)]">Select a dataset</p>
          )}
          {validation && (
            <div className="card p-5">
              <h3 className="font-semibold mb-2">Validation report</h3>
              <p className="text-sm">Issues: {validation.issue_count}</p>
              <p className="text-sm">Duplicates: {validation.duplicates?.length || 0}</p>
              <pre className="mt-3 max-h-64 overflow-auto text-xs bg-[var(--card)] p-3 rounded-xl">
                {JSON.stringify(validation.issues?.slice(0, 20), null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
