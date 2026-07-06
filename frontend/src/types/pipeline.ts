export interface PipelineConfig {
  id: string
  name: string
  version: string
  description: string
  config_json: Record<string, unknown>
  required_models_json: string[]
  required_components_json: string[]
  original_filename: string
  is_valid: boolean
  validation_errors: string[]
  created_at: string
}
