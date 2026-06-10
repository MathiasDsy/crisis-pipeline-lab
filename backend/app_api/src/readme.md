clients/    -> appels externes : Ollama, Photon, APIs
database/   -> DB, repositories
domain/     -> objets métier : Incident, Tweet, Location, PipelineRun
modules/    -> grosses features applicatives
pipeline/   -> moteur YAML + orchestration
storage/    -> fichiers, logs, datasets, CSV
utils/      -> helpers génériques
main.py     -> point d’entrée FastAPI