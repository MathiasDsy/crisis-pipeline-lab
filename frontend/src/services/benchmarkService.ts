import { http } from './http'
import type {
  Benchmark,
  BenchmarkStartResponse,
  LeaderboardResponse,
} from '@/types/benchmark'

interface BenchmarksListResponse {
  benchmarks: Benchmark[]
  count: number
}

export interface StartBenchmarkBody {
  dataset_id:            string
  classifier_model_keys: string[]
  location_model_keys:   string[]
  name:                  string
}

export const benchmarkService = {
  start: (body: StartBenchmarkBody) =>
    http.post<BenchmarkStartResponse>('/benchmarks/start', body),

  list: () =>
    http.get<BenchmarksListResponse>('/benchmarks').then((r) => r.benchmarks),

  get: (id: string) =>
    http.get<Benchmark>(`/benchmarks/${id}`),

  leaderboard: (id: string) =>
    http.get<LeaderboardResponse>(`/benchmarks/${id}/leaderboard`),

  cancel: (id: string) =>
    http.post<{ status: string }>(`/benchmarks/${id}/cancel`),
}
