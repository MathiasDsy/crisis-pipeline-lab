type CrisisEvent = Record<string, unknown>

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function getEvents(): Promise<CrisisEvent[]> {
  const res = await fetch(`${API_BASE}/events`)

  if (!res.ok) {
    throw new Error(`Failed to fetch events: ${res.status}`)
  }

  return res.json()
}