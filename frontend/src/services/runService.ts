import { http } from './http'
import type { Run, RunSummary, RunMetrics } from '@/types/run'
import type { FireEvent } from '@/types/event'
import type { Tweet, StepExecution } from '@/types/tweet'

interface RunsResponse {
  runs: Run[]
}

interface EventsResponse {
  events: FireEvent[]
}

interface TweetsResponse {
  tweets: Tweet[]
}

interface TraceResponse {
  trace: StepExecution[]
}

export const runService = {
  list: (params?: { status?: string; mode?: string }) => {
    const q = new URLSearchParams()
    if (params?.status) q.set('status', params.status)
    if (params?.mode)   q.set('mode', params.mode)
    const qs = q.toString()
    return http.get<RunsResponse>(`/runs${qs ? `?${qs}` : ''}`).then((r) => r.runs)
  },

  summary: (runId: string) =>
    http.get<RunSummary>(`/runs/${runId}/summary`),

  // Metrics live under the simulation namespace, not /runs.
  metrics: (runId: string) =>
    http.get<RunMetrics>(`/simulation/${runId}/metrics`),

  events: (runId: string) =>
    http.get<EventsResponse>(`/runs/${runId}/events`).then((r) => r.events),

  tweets: (runId: string, limit = 200, offset = 0) =>
    http
      .get<TweetsResponse>(`/runs/${runId}/tweets?limit=${limit}&offset=${offset}`)
      .then((r) => r.tweets),

  trace: (runId: string) =>
    http.get<TraceResponse>(`/runs/${runId}/trace`).then((r) => r.trace),
}
