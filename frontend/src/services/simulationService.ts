import { http } from './http'
import type { Run } from '@/types/run'

export interface StartSimulationBody {
  dataset_id: string
  pipeline_config_id: string
  force_rerun?: boolean
}

export interface StartSimulationResponse {
  status: 'started' | 'cached'
  cached: boolean
  run_id: string
  run: Run
}

export const simulationService = {
  start: (body: StartSimulationBody) =>
    http.post<StartSimulationResponse>('/simulation/start', body),

  getStatus: (runId: string) =>
    http.get<Run>(`/simulation/${runId}`),

  cancel: (runId: string) =>
    http.post<{ status: string }>(`/simulation/${runId}/cancel`),
}
