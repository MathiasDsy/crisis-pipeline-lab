export type EventTabKey = "all" | "active" | "resolved" | "watching"

export type FireEventStatus = "active" | "resolved" | "watching"

export interface FireEvent {
  id: string
  name: string
  status: FireEventStatus
  location_name?: string
  centroid_lat: number
  centroid_lon: number
  confidence: number
  tweet_count: number
  first_seen: string
  last_seen: string
  tweet_ids: string[]
}