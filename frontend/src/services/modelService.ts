import { http } from './http'
import type { Model } from '@/types/model'
import type { HfSearchResponse } from '@/types/huggingface'

const BASE_URL = (import.meta.env.VITE_API_URL as string) ?? 'http://localhost:8000'

interface ModelsResponse {
  models: Model[]
}

export interface HfImportBody {
  repo_id:               string
  model_key:             string
  model_type:            string
  loader:                string
  compatible_components: string[]
  version?:              string
  hf_token?:             string | null
}

interface HfImportResponse {
  status:     string
  model_key:  string
  local_path: string
  repo_id:    string
}

export const modelService = {
  list: (params?: { model_type?: string; available?: boolean }) => {
    const q = new URLSearchParams()
    if (params?.model_type !== undefined) q.set('model_type', params.model_type)
    if (params?.available  !== undefined) q.set('available',  String(params.available))
    const qs = q.toString()
    return http.get<ModelsResponse>(`/models${qs ? `?${qs}` : ''}`).then((r) => r.models)
  },

  discover: () =>
    http.post<{ valid_models: Model[] }>('/models/discover').then((r) => r.valid_models),

  searchHuggingface: (q: string, limit = 20) => {
    const params = new URLSearchParams({ q, limit: String(limit) })
    return http.get<HfSearchResponse>(`/models/search/huggingface?${params.toString()}`)
  },

  importHuggingface: (body: HfImportBody) =>
    http.post<HfImportResponse>('/models/import/huggingface', body),

  importUpload: async (file: File): Promise<{ model_key: string; local_path: string }> => {
    const form = new FormData()
    form.append('file', file, file.name)

    const res = await fetch(`${BASE_URL}/models/import/upload`, { method: 'POST', body: form })

    if (!res.ok) {
      const body = await res.json().catch(() => null)
      throw new Error(body?.detail ?? `HTTP ${res.status}`)
    }

    return res.json()
  },
}
