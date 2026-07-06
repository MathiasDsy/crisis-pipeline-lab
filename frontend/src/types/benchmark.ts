export type BenchmarkStatus = 'running' | 'completed' | 'cancelled' | 'error'

export interface Benchmark {
  id:                    string
  name:                  string
  dataset_id:            string
  classifier_model_keys: string[]
  location_model_keys:   string[]
  total_runs:            number
  completed_runs:        number
  status:                BenchmarkStatus
  created_at:            string
  finished_at:           string | null
}

export interface BenchmarkStartResponse {
  status:       'started'
  benchmark_id: string
  total_runs:   number
  benchmark:    Benchmark
}

export interface LeaderboardEntry {
  run_id:  string
  status:  string
  model_snapshot_json: {
    classifier_model_key: string
    location_model_key:   string
  }
  tp: number
  fp: number
  fn: number
  tn: number
  precision:      number
  recall:         number
  f1:             number
  accuracy:       number
  total_tweets:   number
  labeled_tweets: number
}

export interface LeaderboardResponse {
  benchmark_id:   string
  status:         BenchmarkStatus
  total_runs:     number
  completed_runs: number
  leaderboard:    LeaderboardEntry[]
}
