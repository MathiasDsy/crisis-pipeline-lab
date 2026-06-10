export interface CrisisEvent {
  id: string
  center_lat: number
  center_lon: number
  radius_km: number
  status: string
  is_finished: boolean
  tweet_count: number
  latest_tweet_text: string | null
  created_at: string
  updated_at: string
  finished_at?: string | null
}

export type EventTabKey = "all" | "active" | "resolved" | "watching"

export type FireEventStatus = "active" | "resolved" | "watching"

export interface FireEvent {
  id: string
  center_lat: number
  center_lon: number
  radius_km: number
  status: FireEventStatus
  confidence: number
  tweet_count: number
  first_seen: string
  last_seen: string
  created_at: string
  updated_at: string
  latest_tweet_text: string | null
  // tweet_ids: string[]
}