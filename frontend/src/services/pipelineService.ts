import { http } from './http'
import type { PipelineConfig } from '@/types/pipeline'

const BASE_URL = (import.meta.env.VITE_API_URL as string) ?? 'http://localhost:8000'

interface PipelinesResponse {
  pipelines: PipelineConfig[]
}

interface ImportResponse {
  status: string
  filename: string
  pipeline_config: PipelineConfig
}

export interface ValidateResponse {
  pipeline_config_id: string
  is_valid: boolean
  errors: string[]
}

export const pipelineService = {
  list: (valid?: boolean) => {
    const q = valid !== undefined ? `?valid=${valid}` : ''
    return http.get<PipelinesResponse>(`/pipelines${q}`).then((r) => r.pipelines)
  },

  get: (id: string) =>
    http.get<PipelineConfig>(`/pipelines/${id}`),

  import: async (file: File): Promise<PipelineConfig> => {
    const form = new FormData()
    form.append('file', file, file.name)

    const res = await fetch(`${BASE_URL}/pipelines/import`, { method: 'POST', body: form })

    if (!res.ok) {
      const body = await res.json().catch(() => null)
      throw new Error(body?.detail ?? `HTTP ${res.status}`)
    }

    const data = (await res.json()) as ImportResponse
    return data.pipeline_config
  },

  validate: (id: string) =>
    http.post<ValidateResponse>(`/pipelines/${id}/validate`),

  delete: (id: string) =>
    http.delete<{ pipeline_config_id: string; status: string }>(`/pipelines/${id}`),
}
