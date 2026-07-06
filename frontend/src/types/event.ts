export interface FireEvent {
  id: string
  run_id: string
  center_lat: number
  center_lon: number
  radius_km: number
  is_active: boolean
  finished_at: string | null
  tweet_count: number
  latest_tweet_text: string
  created_at: string
  updated_at: string
}
