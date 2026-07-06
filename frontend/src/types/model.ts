export interface Model {
  id: string
  model_key: string
  name: string
  version: string
  model_type: string
  compatible_components_key: string[]
  local_path: string
  is_available: boolean
  metadata_json: Record<string, unknown>
  created_at: string
  updated_at: string
}
