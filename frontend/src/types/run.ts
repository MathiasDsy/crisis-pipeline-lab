export type RunStatus = 'running' | 'completed' | 'cancelled' | 'error'

export interface Run {
  id: string
  pipeline_config_id: string | null
  dataset_id: string | null
  mode: string
  status: RunStatus
  name?: string
  started_at: string
  finished_at: string | null
  model_snapshot_json: Record<string, unknown>
}

export interface RunSummary {
  run_id: string
  mode: string
  status: RunStatus
  tweets_processed: number
  events_created: number
  steps_executed: number
  errors: number
  started_at: string
  finished_at: string | null
}

export interface RunMetrics {
  run_id: string
  total_tweets: number
  labeled_tweets: number
  unlabeled_tweets: number
  tp: number
  fp: number
  fn: number
  tn: number
  precision: number
  recall: number
  f1: number
  accuracy: number
  per_tweet: Array<{
    tweet_id: string
    label: boolean
    predicted: boolean
  }>
}
