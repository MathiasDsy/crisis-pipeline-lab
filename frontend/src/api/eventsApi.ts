const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function fetchAllEvents() {
  const response = await fetch(`${API_BASE}/events`)
  return response.json()
}
