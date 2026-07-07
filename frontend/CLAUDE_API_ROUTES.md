# API Routes — Early Fire Detection

## Stack

- **pipeline-api** : `http://localhost:8000` — FastAPI, logique métier, BDD PostgreSQL
- **model-server** : `http://localhost:8001` — FastAPI, inférence ML (classifier + GLiNER)

Swagger UI disponible sur `/docs` pour chaque service.

---

## pipeline-api (port 8000)

### ADMIN

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/admin/health` | Health check global |
| GET | `/admin/stats` | Counts globaux (datasets, pipelines, runs, tweets, events, models) — stub à brancher |
| GET | `/admin/database` | Vérifie la connexion PostgreSQL |
| GET | `/admin/system` | Infos runtime (env, version) |
| POST | `/admin/sync` | Relance tous les scanners — stub |
| GET | `/admin/logs` | Liste les logs applicatifs |

**Query params `/admin/logs` :**
- `run_id` (UUID, optionnel) — filtrer par run
- `level` (string, optionnel) — `info` / `warning` / `error`
- `limit` (int, défaut 200)
- `offset` (int, défaut 0)

**Réponse `/admin/logs` :**
```json
{
  "logs": [
    {
      "id": "uuid",
      "run_id": "uuid | null",
      "level": "info",
      "context": "simulation",
      "message": "Simulation started — 50 rows to process",
      "details": {},
      "created_at": "2026-06-27T09:00:00"
    }
  ],
  "count": 1,
  "filters": { "run_id": null, "level": null }
}
```

---

### DATASETS

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/datasets` | Liste tous les datasets |
| POST | `/datasets/discover` | Scanne `/app/storage/datasets/` et upsert en BDD |
| POST | `/datasets/import` | Upload d'un fichier CSV |
| GET | `/datasets/schema` | Colonnes requises et optionnelles |
| GET | `/datasets/{id}` | Détail d'un dataset |
| GET | `/datasets/{id}/preview` | 10 premières lignes du CSV |

**Query params `/datasets` :**
- `valid` (bool, optionnel) — filtrer par validité

**Query params `/datasets/{id}/preview` :**
- `rows` (int, défaut 10)

**Schéma CSV attendu :**
- `content` (requis) — texte du tweet
- `label` (requis) — `True` / `False` / `1` / `0` / `yes` / `on-topic`
- `id`, `created_at`, `source` (optionnels)

**Réponse `/datasets` :**
```json
{
  "datasets": [
    {
      "id": "uuid",
      "name": "croatia_wildfire_test",
      "path": "/app/storage/datasets/croatia_wildfire_test.csv",
      "hash": "sha256",
      "is_valid": true,
      "validation_errors": [],
      "metadata_json": { "filename": "...", "columns": ["content", "label"] },
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "count": 1,
  "filters": { "valid": null }
}
```

**Réponse `/datasets/{id}/preview` :**
```json
{
  "dataset_id": "uuid",
  "columns": ["content", "label"],
  "rows": [{ "content": "...", "label": true }],
  "count": 10
}
```

---

### MODELS

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/models` | Liste les modèles enregistrés |
| POST | `/models/discover` | Scanne `/app/storage/models/` et upsert en BDD |
| GET | `/models/search/huggingface` | Recherche des modèles sur HuggingFace Hub |
| POST | `/models/import/huggingface` | Télécharge et importe un modèle depuis HuggingFace |
| POST | `/models/import/upload` | Importe un modèle par upload d'un .zip |
| GET | `/models/{model_key}` | Détail d'un modèle par model_key |
| POST | `/models/{model_key}/check` | Vérifie la présence du modèle sur disque + maj disponibilité |

**Query params `/models` :**
- `model_type` (string, optionnel)
- `available` (bool, optionnel)

**Query params `/models/search/huggingface` :**
- `q` (string, requis) — terme de recherche ex: `wildfire classifier`
- `limit` (int, défaut 20)
- `hf_token` (string, optionnel) — pour les modèles privés

**Réponse `/models/search/huggingface` :**
```json
{
  "query": "wildfire classifier",
  "count": 1,
  "models": [
    {
      "repo_id": "username/xlm-roberta-wildfire",
      "author": "username",
      "model_name": "xlm-roberta-wildfire",
      "downloads": 1240,
      "likes": 8,
      "tags": ["pytorch", "text-classification"],
      "pipeline_tag": "text-classification",
      "last_modified": "2025-03-12",
      "url": "https://huggingface.co/username/xlm-roberta-wildfire",
      "num_parameters": 278000000,
      "size_label": "278M",
      "size_on_disk_mb": 556.0
    }
  ]
}
```
> `num_parameters`, `size_label`, `size_on_disk_mb` peuvent être `null` si HuggingFace ne fournit pas les infos safetensors.

**Body `/models/import/huggingface` :**
```json
{
  "repo_id": "username/my-model",
  "model_key": "my_model_v1",
  "model_type": "classifier",
  "loader": "transformers",
  "compatible_components": ["relevance_classifier"],
  "version": "1.0.0",
  "hf_token": null
}
```
> Génère automatiquement le `metadata.json`. Retourne `409` si le `model_key` existe déjà.

**`/models/import/upload` :** multipart `file` (.zip). Le zip doit contenir un `metadata.json` valide avec au moins `model_key`. L'extraction détecte la racine du modèle automatiquement. Retourne `409` si le `model_key` existe déjà.

**Structure `metadata.json` d'un modèle :**
```json
{
  "model_key": "relevance_xlmroberta_finetuned_v1",
  "name": "XLM-RoBERTa Relevance Classifier",
  "model_type": "classifier",
  "version": "1.0.0",
  "entrypoint": "model/",
  "loader": "transformers",
  "compatible_components": ["relevance_classifier"]
}
```

**Réponse `/models` :**
```json
{
  "models": [
    {
      "id": "uuid",
      "model_key": "relevance_xlmroberta_finetuned_v1",
      "name": "...",
      "version": "1.0.0",
      "model_type": "classifier",
      "compatible_components_key": ["relevance_classifier"],
      "local_path": "/app/storage/models/relevance_model/model/",
      "is_available": true,
      "metadata_json": {},
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "filters": { "model_type": null, "available": null }
}
```

---

### PIPELINES

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/pipelines` | Liste les pipeline configs |
| POST | `/pipelines/import` | Upload d'un fichier YAML |
| GET | `/pipelines/{id}` | Détail d'une pipeline config |
| POST | `/pipelines/{id}/validate` | Valide la config (composants + modèles disponibles) |
| DELETE | `/pipelines/{id}` | Supprime une pipeline config |

**Query params `/pipelines` :**
- `valid` (bool, optionnel)

**Structure YAML pipeline :**
```yaml
name: Fire Detection V1
version: "1.0.0"
description: Early wildfire detection pipeline

runtime:
  stop_on_error: true

steps:
  - id: relevance
    component_key: relevance_classifier
    model_key: relevance_xlmroberta_finetuned_v1
    input:
      text: tweet.content
    output: outputs.relevance
    params:
      threshold: 0.7

  - id: location
    component_key: location_extractor
    model_key: gliner_multi_v2_1
    input:
      text: tweet.content
    output: outputs.locations
    params:
      threshold: 0.5

  - id: geocoding
    component_key: geocoder
    input:
      locations: outputs.locations
    output: outputs.geocoding

  - id: event_matching
    component_key: event_matcher
    input:
      geocoding: outputs.geocoding
    output: outputs.event
    params:
      radius_km: 5.0
```

**Composants disponibles :**
- `relevance_classifier` — classifie si le tweet est un signal de crise
- `location_extractor` — extrait les entités géographiques (GLiNER)
- `geocoder` — géocode via Photon local
- `event_matcher` — matche ou crée un event via Haversine (défaut 5km)

**Réponse `/pipelines` :**
```json
{
  "pipelines": [
    {
      "id": "uuid",
      "name": "Fire Detection V1",
      "version": "1.0.0",
      "description": "...",
      "config_json": {},
      "required_models_json": ["relevance_xlmroberta_finetuned_v1"],
      "required_components_json": ["relevance_classifier", "location_extractor"],
      "original_filename": "fire_pipeline_v1.yaml",
      "is_valid": true,
      "validation_errors": [],
      "created_at": "..."
    }
  ],
  "filters": { "valid": null }
}
```

---

### SIMULATION

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/simulation/start` | Lance une simulation (asynchrone, retourne immédiatement) |
| GET | `/simulation/{run_id}` | État d'une simulation |
| GET | `/simulation/{run_id}/results` | Tweets + events + trace du run |
| GET | `/simulation/{run_id}/metrics` | Precision / Recall / F1 / Accuracy |
| POST | `/simulation/{run_id}/cancel` | Annule une simulation en cours |

**Body `/simulation/start` :**
```json
{
  "dataset_id": "uuid",
  "pipeline_config_id": "uuid",
  "force_rerun": false
}
```

**Réponse `/simulation/start` (démarrage) :**
```json
{
  "status": "started",
  "cached": false,
  "run_id": "uuid",
  "run": { ... }
}
```

**Réponse `/simulation/start` (cache hit) :**
```json
{
  "status": "cached",
  "cached": true,
  "run_id": "uuid",
  "run": { ... }
}
```

**Réponse `/simulation/{run_id}/metrics` :**
```json
{
  "run_id": "uuid",
  "total_tweets": 50,
  "labeled_tweets": 50,
  "unlabeled_tweets": 0,
  "tp": 18,
  "fp": 5,
  "fn": 2,
  "tn": 25,
  "precision": 0.7826,
  "recall": 0.9000,
  "f1": 0.8372,
  "accuracy": 0.8600,
  "per_tweet": [
    { "tweet_id": "uuid", "label": true, "predicted": true }
  ]
}
```

**Polling recommandé :** `GET /simulation/{run_id}` toutes les 2-3 secondes jusqu'à `status != "running"`.

**Statuts possibles d'un run :** `running` / `completed` / `cancelled` / `error`

---

### RUNS

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/runs` | Liste tous les runs |
| GET | `/runs/compare` | Compare precision/recall/F1 de plusieurs runs |
| GET | `/runs/{run_id}` | Détail d'un run |
| GET | `/runs/{run_id}/summary` | Résumé (counts tweets/events/steps/errors) |
| GET | `/runs/{run_id}/events` | Events du run (paginé) |
| GET | `/runs/{run_id}/tweets` | Tweets du run (paginé) |
| GET | `/runs/{run_id}/trace` | Step executions du run (paginé) |
| GET | `/runs/{run_id}/hard-cases` | Tweets label=True ratés par le pipeline (faux négatifs) |

**Query params `/runs` :**
- `mode` (string, optionnel) — ex: `simulation`
- `status` (string, optionnel) — `running` / `completed` / `cancelled` / `error`

**Query params `/runs/compare` :**
- `run_ids` (string, requis) — UUIDs séparés par virgule ex: `a,b,c`

**Réponse `/runs/compare` :**
```json
{
  "run_ids": ["uuid-a", "uuid-b"],
  "comparison": [
    { "run_id": "uuid-a", "precision": 0.87, "recall": 0.91, "f1": 0.89, "accuracy": 0.88, "tp": 18, "fp": 2, "fn": 2, "tn": 28 },
    { "run_id": "uuid-b", "precision": 0.75, "recall": 0.80, "f1": 0.77, "accuracy": 0.79, "tp": 15, "fp": 5, "fn": 4, "tn": 26 }
  ]
}
```

**Réponse `/runs/{run_id}/summary` :**
```json
{
  "run_id": "uuid",
  "mode": "simulation",
  "status": "completed",
  "tweets_processed": 50,
  "events_created": 12,
  "steps_executed": 148,
  "errors": 0,
  "started_at": "...",
  "finished_at": "..."
}
```

**Réponse `/runs/{run_id}` (run object) :**
```json
{
  "id": "uuid",
  "pipeline_config_id": "uuid",
  "dataset_id": "uuid",
  "mode": "simulation",
  "status": "completed",
  "started_at": "...",
  "finished_at": "...",
  "model_snapshot_json": {}
}
```

---

### TWEETS

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/tweets` | Liste les tweets (requiert run_id) |
| GET | `/tweets/{tweet_id}` | Détail d'un tweet |
| GET | `/tweets/{tweet_id}/trace` | Steps d'exécution pour ce tweet |
| GET | `/tweets/{tweet_id}/annotations` | Annotations du tweet |
| POST | `/tweets/{tweet_id}/annotations` | Crée une annotation |

**Query params `/tweets` :**
- `run_id` (UUID, recommandé) — sans run_id retourne `[]`
- `event_id` (UUID, optionnel) — non branché en V1
- `source` (string, optionnel) — non branché en V1
- `limit` (int, défaut 100)
- `offset` (int, défaut 0)

**Body `/tweets/{tweet_id}/annotations` :**
```json
{
  "expected_is_signal": true,
  "expected_lat": 43.508,
  "expected_lon": 16.44,
  "expected_location": "Split",
  "comment": "Correct classification"
}
```

**Réponse `/tweets/{tweet_id}` :**
```json
{
  "tweet_id": "uuid",
  "tweet": "Smoke visible near Split",
  "event_id": "uuid | null",
  "run_id": "uuid",
  "source": "dataset",
  "created_at": "..."
}
```

**Réponse `/tweets/{tweet_id}/trace` :**
```json
[
  {
    "id": "uuid",
    "run_id": "uuid",
    "tweet_id": "uuid",
    "step_name": "relevance",
    "status": "success",
    "duration_ms": 142.5,
    "input_json": { "text": "..." },
    "output_json": { "is_relevant": true, "confidence": 0.995 },
    "step_index": 0,
    "created_at": "..."
  }
]
```

---

### BENCHMARKS

Benchmark matriciel : lance le produit cartésien `classifiers × location_models` sur un dataset,
avec la structure de pipeline V1 fixe (classifier → location → geocoding → event_matching).
Chaque combinaison = un run lié au benchmark. Les modèles geocoder/event_matcher sont fixes.

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/benchmarks/start` | Lance une matrice de runs (asynchrone) |
| GET | `/benchmarks` | Liste tous les benchmarks |
| GET | `/benchmarks/{id}` | Statut + progression d'un benchmark |
| GET | `/benchmarks/{id}/runs` | Runs bruts + métriques (ordre chronologique) |
| GET | `/benchmarks/{id}/leaderboard` | Runs du benchmark triés par F1 décroissant |
| POST | `/benchmarks/{id}/cancel` | Annule un benchmark en cours |

**Body `/benchmarks/start` :**
```json
{
  "dataset_id": "uuid",
  "classifier_model_keys": ["relevance_v1", "relevance_v2"],
  "location_model_keys": ["gliner_multi", "gliner_small"],
  "name": "Benchmark wildfire V1"
}
```
→ génère `2 × 2 = 4` runs.

**Réponse `/benchmarks/start` :**
```json
{
  "status": "started",
  "benchmark_id": "uuid",
  "total_runs": 4,
  "benchmark": { ... }
}
```

**Réponse `/benchmarks/{id}` (objet benchmark, pollable pour la progression) :**
```json
{
  "id": "uuid",
  "name": "Benchmark wildfire V1",
  "dataset_id": "uuid",
  "classifier_model_keys": ["relevance_v1", "relevance_v2"],
  "location_model_keys": ["gliner_multi", "gliner_small"],
  "total_runs": 4,
  "completed_runs": 2,
  "status": "running",
  "created_at": "...",
  "finished_at": null
}
```

**Statuts benchmark :** `running` / `completed` / `cancelled` / `error`

**Polling recommandé :** `GET /benchmarks/{id}` jusqu'à `status !== "running"`, en affichant `completed_runs / total_runs` comme barre de progression.

**Réponse `/benchmarks/{id}/runs` (données brutes, ordre chronologique) :**
```json
{
  "benchmark_id": "uuid",
  "status": "completed",
  "total_runs": 4,
  "completed_runs": 4,
  "count": 4,
  "runs": [
    {
      "run_id": "uuid",
      "status": "completed",
      "started_at": "...",
      "finished_at": "...",
      "model_snapshot_json": {
        "classifier_model_key": "relevance_v2",
        "location_model_key": "gliner_multi"
      },
      "tp": 18, "fp": 3, "fn": 2, "tn": 27,
      "precision": 0.8571, "recall": 0.9000, "f1": 0.8780, "accuracy": 0.9000,
      "total_tweets": 50, "labeled_tweets": 50,
      "computed_at": "..."
    }
  ]
}
```
> Endpoint recommandé pour construire le leaderboard côté front (tri/filtres/colonnes libres). Les champs métriques sont `null` tant que le run n'est pas terminé. Chaque `run_id` permet le drill-down via `/runs/{run_id}/trace`.

**Réponse `/benchmarks/{id}/leaderboard` (trié par F1 desc, NULLS last) :**
```json
{
  "benchmark_id": "uuid",
  "status": "completed",
  "total_runs": 4,
  "completed_runs": 4,
  "leaderboard": [
    {
      "run_id": "uuid",
      "status": "completed",
      "model_snapshot_json": {
        "classifier_model_key": "relevance_v2",
        "location_model_key": "gliner_multi"
      },
      "tp": 18, "fp": 3, "fn": 2, "tn": 27,
      "precision": 0.8571, "recall": 0.9000, "f1": 0.8780, "accuracy": 0.9000,
      "total_tweets": 50, "labeled_tweets": 50
    }
  ]
}
```

**Notes :**
- Exécution **séquentielle** (le model-server ne garde qu'un classifier + un gliner en mémoire). Un benchmark de N combos prend ~N × durée d'un run.
- Chaque combinaison est un `pipeline_run` avec `mode: "benchmark"`, `benchmark_id` renseigné, et `pipeline_config_id: null` (structure fixe injectée en mémoire).
- La combinaison de modèles est dans `model_snapshot_json` du run.
- Les métriques sont **persistées en BDD** (table `run_metrics`) à la fin de chaque run — utilisable aussi via `GET /simulation/{run_id}/metrics`.

---

### EVENTS

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/events` | Liste les events |
| GET | `/events/{event_id}` | Détail d'un event |
| GET | `/events/{event_id}/tweets` | Tweets liés à cet event |
| POST | `/events/{event_id}/close` | Ferme un event |
| POST | `/events/{event_id}/reopen` | Réouvre un event |

**Query params `/events` :**
- `run_id` (UUID, optionnel)
- `active` (bool, optionnel)
- `limit` (int, défaut 100)
- `offset` (int, défaut 0)

**Réponse `/events/{event_id}` :**
```json
{
  "id": "uuid",
  "run_id": "uuid",
  "center_lat": 43.508,
  "center_lon": 16.44,
  "radius_km": 20.0,
  "is_active": true,
  "finished_at": null,
  "tweet_count": 3,
  "latest_tweet_text": "Smoke visible near Split",
  "created_at": "...",
  "updated_at": "..."
}
```

---

## model-server (port 8001)

### HEALTH

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/health` | Statut + modèles chargés |

**Réponse `/health` :**
```json
{
  "status": "ok",
  "classifier_loaded": true,
  "gliner_loaded": true
}
```

---

### MODELS

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/models/current` | model_key des modèles actuellement chargés |
| POST | `/models/load/classifier` | Charge un classifier à chaud |
| POST | `/models/load/location_extractor` | Charge un modèle GLiNER à chaud |
| POST | `/models/unload/classifier` | Décharge le classifier |
| POST | `/models/unload/location_extractor` | Décharge le modèle de localisation |

**Body `/models/load/classifier` et `/models/load/location_extractor` :**
```json
{
  "model_key": "relevance_xlmroberta_finetuned_v1",
  "local_path": "/app/storage/models/relevance_model/model/",
  "loader": "transformers"
}
```

**Réponse `/models/current` :**
```json
{
  "classifier": { "model_key": "relevance_xlmroberta_finetuned_v1" },
  "gliner": { "model_key": "gliner_multi_v2_1" }
}
```

---

### INFERENCE

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/predict` | Classifie un tweet (signal de crise ou non) |
| POST | `/extract-locations` | Extrait les entités géographiques |

**Body `/predict` :**
```json
{ "text": "Smoke visible near Split" }
```

**Réponse `/predict` :**
```json
{
  "label": "Low Signal",
  "is_relevant": true,
  "confidence": 0.995,
  "model_key": "relevance_xlmroberta_finetuned_v1"
}
```

**Body `/extract-locations` :**
```json
{
  "text": "Smoke visible near Split",
  "labels": ["location", "city", "region", "country"],
  "threshold": 0.5
}
```

**Réponse `/extract-locations` :**
```json
{
  "entities": [
    { "text": "Split", "label": "city", "score": 0.91 }
  ],
  "model_key": "gliner_multi_v2_1"
}
```

---

## Base URL frontend

```
VITE_API_URL=http://localhost:8000
VITE_MODEL_API_URL=http://localhost:8001
```

## Notes importantes pour le frontend

- **Simulation asynchrone** : `POST /simulation/start` retourne immédiatement. Poller `GET /simulation/{run_id}` toutes les 2-3s jusqu'à `status !== "running"`.
- **IDs** : tous les IDs sont des UUIDs (string). Pas de lookup par nom en V1.
- **Pagination** : `limit` + `offset` sur tweets, events, trace, logs. Pas de curseur.
- **Labels tweets** : `label: true` = signal réel, `label: false` = bruit. `label: null` = non annoté.
- **Step status** : `success` = passé, `blocked` = filtré (tweet rejeté à ce step), `error` = exception.
- **Geocoder** : instance Photon locale Croatia-only en V1. Les lieux non-croates seront mal géocodés.
- **CORS** autorisé sur `http://localhost:5173` (Vite dev server).
