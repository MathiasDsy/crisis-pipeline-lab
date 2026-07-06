// Shape returned by GET /runs/{run_id}/tweets (raw `tweets` table rows).
export interface Tweet {
  id: string
  content: string
  label: boolean | null
  event_id: string | null
  run_id: string
  source: string
  created_at: string
}

export type ClassKind = 'TP' | 'FP' | 'FN' | 'TN'

export interface ClassifiedTweet {
  tweet_id:  string
  text:      string
  label:     boolean | null
  predicted: boolean | null
  kind:      ClassKind | null
}

export interface StepExecution {
  id: string
  run_id: string
  tweet_id: string
  step_name: string
  status: 'success' | 'blocked' | 'error'
  duration_ms: number
  input_json: Record<string, unknown>
  output_json: Record<string, unknown>
  step_index: number
  created_at: string
}
