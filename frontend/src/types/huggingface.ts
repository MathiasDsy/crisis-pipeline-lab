export interface HfModel {
  repo_id:         string
  author:          string | null
  model_name:      string
  downloads:       number | null
  likes:           number | null
  tags:            string[]
  pipeline_tag:    string | null
  last_modified:   string | null
  url:             string
  num_parameters:  number | null
  size_label:      string | null
  size_on_disk_mb: number | null
}

export interface HfSearchResponse {
  query:  string
  count:  number
  models: HfModel[]
}
