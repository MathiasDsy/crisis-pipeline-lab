import type { AnnotationLabel } from "@/types/pipeline"

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'


export async function fetchAllTweets() {
  
  
  const response = await fetch(`${API_BASE}/fetch_all_tweets`)

  if (!response.ok) {
    throw new Error(`Failed to fetch tweets: ${response.status}`)
  }
  let data = await response.json()
  console.log("Tweets fetched successfully", data)
  return data
}

export async function annotatePipelineStep(payload: {
  pipelineStepId: string
  label: AnnotationLabel
}) {
  const response = await fetch(`${API_BASE}/pipeline-steps/annotate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error("Failed to annotate pipeline step")
  }

  return await response.json()
}