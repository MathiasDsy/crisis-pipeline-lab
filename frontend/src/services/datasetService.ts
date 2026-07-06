import { http } from './http'
import type { Dataset, DatasetPreview } from '@/types/dataset'

const BASE_URL = (import.meta.env.VITE_API_URL as string) ?? 'http://localhost:8000'

interface DatasetsResponse {
  datasets: Dataset[]
  count: number
}

interface ImportResponse {
  status: string
  dataset: Dataset
}

export const datasetService = {
  list: (valid?: boolean) => {
    const q = valid !== undefined ? `?valid=${valid}` : ''
    return http.get<DatasetsResponse>(`/datasets${q}`).then((r) => r.datasets)
  },

  discover: () =>
    http.post<DatasetsResponse>('/datasets/discover').then((r) => r.datasets),

  import: async (file: File): Promise<Dataset> => {
    const form = new FormData()
    form.append('file', file, file.name)

    const res = await fetch(`${BASE_URL}/datasets/import`, { method: 'POST', body: form })

    if (!res.ok) {
      // FastAPI returns { detail: "..." } on error
      const body = await res.json().catch(() => null)
      throw new Error(body?.detail ?? `HTTP ${res.status}`)
    }

    const data = (await res.json()) as ImportResponse
    return data.dataset
  },

  get: (id: string) =>
    http.get<Dataset>(`/datasets/${id}`),

  preview: (id: string, rows = 10) =>
    http.get<DatasetPreview>(`/datasets/${id}/preview?rows=${rows}`),
}
