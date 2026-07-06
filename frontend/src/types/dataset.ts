export interface Dataset {
  id: string
  name: string
  path: string
  hash: string
  is_valid: boolean
  validation_errors: string[]
  metadata_json: {
    filename: string
    columns: string[]
    row_count?: number
  }
  created_at: string
  updated_at: string
}

export interface DatasetPreview {
  dataset_id: string
  columns: string[]
  rows: Record<string, unknown>[]
  count: number
}
