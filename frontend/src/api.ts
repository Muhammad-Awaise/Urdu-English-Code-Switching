const API = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) },
    ...options,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || JSON.stringify(body)
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return res.json()
}

export const api = {
  dashboard: () => request<any>('/dashboard'),
  analyze: (text: string, use_preprocessing = true, model_override?: string) =>
    request<any>('/analyze', {
      method: 'POST',
      body: JSON.stringify({ text, use_preprocessing, model_override }),
    }),
  analyzeHistory: () => request<any>('/analyze/history'),
  preprocess: (payload: Record<string, unknown>) =>
    request<any>('/preprocess', { method: 'POST', body: JSON.stringify(payload) }),
  datasets: () => request<any>('/datasets'),
  createDataset: (payload: Record<string, unknown>) =>
    request<any>('/datasets', { method: 'POST', body: JSON.stringify(payload) }),
  datasetRecords: (id: number, unlabeled_only = false) =>
    request<any>(`/datasets/${id}/records?unlabeled_only=${unlabeled_only}`),
  validateDataset: (id: number) => request<any>(`/datasets/${id}/validate`, { method: 'POST' }),
  splitDataset: (id: number, payload: Record<string, unknown>) =>
    request<any>(`/datasets/${id}/split`, { method: 'POST', body: JSON.stringify(payload) }),
  cleanDataset: (id: number, payload: Record<string, unknown>) =>
    request<any>(`/datasets/${id}/clean`, { method: 'POST', body: JSON.stringify(payload) }),
  addSentence: (id: number, payload: Record<string, unknown>) =>
    request<any>(`/datasets/${id}/sentences`, { method: 'POST', body: JSON.stringify(payload) }),
  updateAnnotation: (id: number, payload: Record<string, unknown>) =>
    request<any>(`/annotations/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  uploadDataset: async (id: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${API}/datasets/${id}/upload`, { method: 'POST', body: form })
    if (!res.ok) {
      let detail = await res.text()
      try {
        detail = JSON.parse(detail).detail || detail
      } catch {
        /* ignore */
      }
      throw new Error(detail)
    }
    return res.json()
  },
  importJob: (jobId: string) => request<any>(`/datasets/import-jobs/${jobId}`),
  startTraining: (payload: Record<string, unknown>) =>
    request<any>('/training/start', { method: 'POST', body: JSON.stringify(payload) }),
  jobs: () => request<any>('/training/jobs'),
  job: (id: string) => request<any>(`/training/jobs/${id}`),
  cancelJob: (id: string) => request<any>(`/training/jobs/${id}/cancel`, { method: 'POST' }),
  models: () => request<any>('/models'),
  activateModel: (id: number) => request<any>(`/models/${id}/activate`, { method: 'POST' }),
  deactivateModel: (id: number) => request<any>(`/models/${id}/deactivate`, { method: 'POST' }),
  compare: () => request<any>('/experiments/compare'),
  modelEval: (id: number) => request<any>(`/models/${id}/evaluation`),
  researchDashboard: () => request<any>('/research/dashboard'),
  notes: () => request<any>('/research/notes'),
  createNote: (payload: Record<string, unknown>) =>
    request<any>('/research/notes', { method: 'POST', body: JSON.stringify(payload) }),
  deleteNote: (id: number) => request<any>(`/research/notes/${id}`, { method: 'DELETE' }),
  papers: () => request<any>('/research/papers'),
  createPaper: (payload: Record<string, unknown>) =>
    request<any>('/research/papers', { method: 'POST', body: JSON.stringify(payload) }),
  experiments: () => request<any>('/research/experiments'),
  methodology: () => request<any>('/research/methodology'),
  exportReport: (report_type: string, format = 'markdown') =>
    request<any>('/research/reports', {
      method: 'POST',
      body: JSON.stringify({ report_type, format }),
    }),
  settings: () => request<any>('/settings'),
}
