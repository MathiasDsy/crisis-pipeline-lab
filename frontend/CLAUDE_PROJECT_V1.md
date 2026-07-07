# Crisis Detection Simulator — Project V1

## Concept

Early Fire Detection est un simulateur de pipeline de détection de crises (incendies, catastrophes naturelles) basé sur des tweets. Il permet de tester et benchmarker des pipelines de traitement NLP sur des datasets annotés, sans dépendance à une API Twitter réelle.

L'objectif est de répondre à la question : **"Quel pipeline détecte le mieux les signaux de crise dans un flux de tweets, avec quelle précision, et où géographiquement ?"**

---

## Ce que fait le projet

### 1. Gestion de datasets
L'utilisateur importe des fichiers CSV contenant des tweets annotés (`content` + `label`). Le système valide le format, calcule un hash pour éviter les doublons, et stocke les métadonnées en BDD. Les datasets sont scannés automatiquement au démarrage depuis `/storage/datasets/`.

### 2. Gestion de pipelines
Un pipeline est défini en YAML. Il décrit une séquence de steps (composants) avec leurs paramètres et leurs modèles associés. Les pipelines sont importés via upload ou scannés depuis `/storage/pipelines/` au démarrage. Chaque pipeline est validé (composants connus, modèles disponibles).

### 3. Gestion de modèles
Les modèles ML sont stockés localement dans `/storage/models/`. Chaque modèle contient un `metadata.json` qui décrit comment le charger (`loader`, `model_key`, `entrypoint`, `compatible_components`). Le model-server (service séparé) charge les modèles à chaud et expose des endpoints d'inférence.

### 4. Simulation
L'utilisateur choisit un dataset et un pipeline, puis lance une simulation. Chaque tweet du dataset passe dans le pipeline step by step :
- **Relevance classifier** — filtre les tweets non pertinents (bruit)
- **Location extractor** — extrait les entités géographiques (GLiNER)
- **Geocoder** — résout les lieux en coordonnées GPS (Photon local)
- **Event matcher** — regroupe les tweets géographiquement proches en events (Haversine, rayon 5km)

La simulation est **asynchrone** : elle démarre en background et peut être annulée. L'état est pollable via `GET /simulation/{run_id}`.

### 5. Métriques et benchmark
Une fois la simulation terminée, le système calcule automatiquement precision / recall / F1 / accuracy en comparant les labels du dataset aux prédictions du pipeline. L'utilisateur peut comparer plusieurs runs côte à côte (`/runs/compare`) et identifier les faux négatifs (`/runs/{run_id}/hard-cases`).

### 6. Events géospatiaux
Les tweets qui passent tout le pipeline (pertinents + géocodés) sont regroupés en events géographiques. Un event représente un foyer d'incendie potentiel avec ses coordonnées, son rayon, et les tweets associés. Les events peuvent être fermés ou rouverts manuellement.

---

## Architecture technique

```
frontend (Vue 3 + Leaflet)
    ↓ HTTP
pipeline-api (FastAPI, port 8000)
    ↓ SQL          ↓ HTTP
PostgreSQL     model-server (FastAPI, port 8001)
                   ↓ local files
               /storage/models/
               
photon (geocoder OSM local, port 2322)
```

### Services Docker
| Service | Port | Rôle |
|---------|------|------|
| `pipeline-api` | 8000 | API principale, logique métier |
| `model-server` | 8001 | Inférence ML (classifier + GLiNER) |
| `postgres` | 5432 | Base de données |
| `photon` | 2322 | Géocodeur OSM local (Croatie en V1) |
| `frontend` | 5173 | Interface Vue 3 |

---

## Ce que fait le frontend (V1)

Le frontend est une interface sobre inspirée de GitHub / Linear. Il permet de :

### Vue principale — Dashboard
- Résumé global : nombre de datasets, pipelines, runs, events
- Accès rapide aux derniers runs et leur statut

### Page Datasets
- Liste des datasets avec statut de validité
- Upload d'un nouveau CSV
- Preview des 10 premières lignes avant simulation
- Indicateur colonnes manquantes

### Page Pipelines
- Liste des pipeline configs avec statut de validité
- Upload d'un YAML de pipeline
- Détail d'une config (steps, modèles requis, composants)
- Bouton de validation manuelle

### Page Simulation (écran principal)
- Sélecteur dataset + sélecteur pipeline
- Bouton "Lancer la simulation"
- Statut en temps réel (polling) : `running` → progress, `completed` → résultats
- Bouton annulation pendant l'exécution
- Affichage post-run :
  - Métriques : precision / recall / F1 / accuracy
  - Carte Leaflet avec les events géolocalisés
  - Liste des tweets traités avec leur statut (passed / blocked / error)
  - Faux négatifs (hard cases)

### Page Runs
- Historique de tous les runs
- Filtres par statut, mode
- Comparaison de runs (precision/recall/F1 côte à côte)
- Détail d'un run : summary, trace step-by-step

### Page Events
- Liste des events détectés avec coordonnées et tweet_count
- Carte Leaflet interactive (marqueurs par event)
- Clic sur un event → tweets associés
- Fermer / rouvrir un event

### Page Models
- Liste des modèles disponibles avec disponibilité
- Bouton "Discover" pour rescanner le storage
- Statut du model-server (modèles chargés)

### Page Logs
- Logs applicatifs filtrables par run_id et level
- Utile pour debugger une simulation qui a planté

---

## Schéma BDD (résumé)

| Table | Rôle |
|-------|------|
| `datasets` | Datasets CSV importés |
| `model_registry` | Modèles ML découverts |
| `pipeline_configs` | Configs YAML importées |
| `pipeline_runs` | Runs de simulation |
| `tweets` | Tweets traités par run |
| `pipeline_step_executions` | Trace détaillée step par step |
| `events` | Events géospatiaux détectés |
| `benchmarks` | Matrices de runs (classifiers × location models) |
| `run_metrics` | Métriques persistées par run (precision/recall/F1/accuracy) |
| `run_logs` | Logs applicatifs (info/warning/error) |

---

## Import de modèles (V1)

Deux voies pour amener un classifier ou un extracteur de localisation dans le système :

- **HuggingFace** — recherche filtrée par composant (`GET /models/search/huggingface?component=...`) puis import. Le type est imposé par le contrat du composant :
  - `relevance_classifier` → `text-classification` + `zero-shot-classification`, loader `transformers`
  - `location_extractor` → modèles `gliner`, loader `gliner`
- **Upload zip** — pour un modèle déjà fine-tuné hors-ligne (le zip contient son `metadata.json`).

> Important : un modèle base HF n'est pas entraîné pour la tâche de pertinence crise. Pour un vrai classifier sur cette tâche en V1, on fine-tune **hors-ligne** (notebook/Colab) puis on importe via zip. L'entraînement intégré est repoussé en V2 (voir Roadmap).

---

## Limites V1

- **Geocoder Croatia-only** : Photon est chargé avec un dump OSM Croatie. Les lieux hors Croatie seront mal géocodés. V2 : swap de dump par pays.
- **IDs opaques** : la simulation prend des UUIDs. V2 : lookup par nom de dataset / pipeline.
- **Simulation mono-run** : pas de parallélisation. Le model-server ne garde qu'un classifier + un gliner en mémoire → lancer deux runs concurrents corrompt les résultats. V2 : verrou / queue.
- **Event matcher statique** : rayon fixé dans la config pipeline. V2 : rayon dynamique par type de crise.
- **Pas d'auth** : API ouverte. Conçu pour usage local / dev.

---

## Roadmap V2

### Entraînement de modèles (epic)

Permettre de fine-tuner un classifier depuis l'app, pour l'adapter à la tâche de pertinence crise sur un dataset annoté.

- **Recette de training fixe** — une seule config (epochs, learning rate, split train/val figés), pas de tuning exposé. C'est ce qui rend la feature tenable.
- **Job asynchrone long** — progress, checkpoints, cancel. Bien plus lourd qu'une simulation (minutes → heures).
- **Emplacement** — dans `model_api` (qui a déjà torch/transformers/accès GPU), **pas** dans `pipeline-api`.
- **Compute** — fine-tuning sur CPU faisable seulement pour petits modèles/petits datasets ; GPU recommandé.
- **Lineage** — base model → variante fine-tunée, versioning, nouveau `model_key` + `metadata.json` régénérée, sauvegarde dans `/storage/models/`.
- **Flow cible** — chercher un base/finetuned sur HF → télécharger → entraîner sur un dataset annoté → la variante devient disponible pour les pipelines et benchmarks.

### Contrats de composants & modèles configurables (epic)

Généraliser le système de contrats pour supporter des modèles **zero-shot configurables** aux côtés des modèles fine-tunés, sans tomber dans la config générique free-form.

**Deux axes orthogonaux** (à ne pas confondre) :

1. **Type de modèle** → détermine le composant et son schéma de params.
2. **Origine du modèle** → soit `[base zero-shot, configuré par labels au runtime]`, soit `[fine-tuné, tête entraînée]`. Un même composant peut accepter les deux.

**Principe directeur : contraindre par composant, jamais l'universel.** Chaque composant déclare un schéma de params **typé**. On n'expose pas un "ajoute n'importe quel champ" — on expose les champs que ce composant précis comprend. C'est ce contrat qui fait qu'un modèle incompatible (ex: un **sentence-transformer**, qui produit des embeddings et non des logits/entités) n'entre dans aucun composant et n'est donc **jamais proposé**.

**Schémas de params par composant (cible) :**

| Composant | Origine | Params configurables |
|-----------|---------|----------------------|
| `relevance_classifier` | fine-tuné | `threshold` |
| `zero_shot_classifier` (nouveau) | base zero-shot (NLI) | `candidate_labels: []`, `threshold` |
| `location_extractor` | GLiNER (zero-shot NER, déjà en place) | `labels: []`, `threshold` |
| `zero_shot_ner` (généralisation) | base zero-shot NER | `labels: []`, `threshold` |

**Travaux :**
- Nouveau composant `zero_shot_classifier` + inférence NLI par labels candidats (différente du `/predict` seq-classification actuel).
- Schéma de params validé par composant (rejet des params inconnus), en s'appuyant sur le mécanisme de contrat déjà en place pour l'import.
- Exposer les `params` de chaque step dans l'UI (labels, threshold, candidate_labels) — le YAML de pipeline les supporte déjà.
- Le modèle `origine` détermine si le bouton "Entraîner" (epic Entraînement) est proposé ou non.

> Le pattern est déjà validé : `location_extractor` (GLiNER) fonctionne aujourd'hui en zero-shot NER via `params.labels`. La V2 ne fait que généraliser ce qui marche.

### Benchmark utile : scoring par étape & inspection qualitative (epic)

Objectif : comparer les pipelines à travers les 26 crises de **CrisisLexT26**, empiriquement là où on a de la vérité terrain, qualitativement ailleurs.

**Les deux niveaux de comparaison :**
1. **Leaderboard empirique** — scorer l'**étape classifier directement** contre le label (pas le pass/block end-to-end). C'est la métrique fiable.
2. **Inspection qualitative** — regarder à l'œil si l'event est bien reconstruit (géocoding + event matching), via la vue de comparaison.

**Point clé — le leaderboard empirique ne dépend PAS de Photon.** Le classifier ne géocode rien : on peut classer les modèles sur les 26 crises sans monter aucune instance Photon. Photon régional n'est nécessaire que pour *inspecter* la reconstruction d'events d'un dataset donné.

**Le plafond est l'annotation, pas le code.** La difficulté escalade en descendant le pipeline :

| Étape | Ground truth | Effort | Statut cible |
|-------|-------------|--------|--------------|
| Classifier | label pertinent/non | déjà là | ✅ empirique |
| Location extraction | lieux attendus (texte) | modéré | 🟢 **palier V2 à viser** (2/4 empiriques) |
| Geocoding | lat/lon gold + tolérance km | cher, confondu par couverture Photon | 🟡 qualitatif |
| Event matching | clusters gold | très cher, subjectif | 🔴 qualitatif |

> Le schéma d'annotation existe déjà : `create_tweet_annotation` prend `expected_is_signal`, `expected_location`, `expected_lat`, `expected_lon`. Ce qui manque = le flow pour *remplir* ces annotations + le scoring qui les lit. Le palier haut-ROI est d'annoter l'**étape location** (match de chaîne) pour passer à 2/4 étapes empiriques.

**Comparaison de résultats (pas que métriques) — nécessite un `sample_id` stable :**
- Aujourd'hui chaque combo recrée ses `tweets` (UUID différents) → impossible d'aligner "le même tweet" entre modèles.
- Proposition : chaque ligne de dataset a un `sample_id` stable, porté par le tweet de chaque run (`source_sample_id`).
- Débloque : vue **pivot** (lignes = samples, colonnes = modèles, cellules = prédiction + confiance + où le tweet s'est arrêté), **hard-cases agrégés** ("dur pour tous" vs "dur pour un seul"), **easy cases**, et le breakdown "**mort où ?**" (relevance / pas de location / pas de geocode).

**Multi-Photon régional (confort d'inspection, pas prérequis) :**
- Plusieurs conteneurs Photon, un par région, chacun avec son extrait OSM (New York State, pas les US entiers, pour tenir en RAM/disque).
- **Contrainte 12 Go : un seul (ou peu) Photon up à la fois** — impossible de charger les 26 régions simultanément.
- Le dataset porte sa région → route vers le bon endpoint via un param (`geocoder_region` / `photon_url`).

**Volume BDD (le vrai risque du benchmark) :**
- `N combos × M tweets × ~4 steps` explose sur gros dataset × grosse matrice.
- Mitigations : échantillonnage du dataset avec `random_state` (reproductible), trace `step_executions` complète **optionnelle/élaguée**, rétention/cleanup des vieux runs.
- Toujours garder l'**outcome par sample** (léger, alimente pivot + hard-cases) ; la trace intégrale devient optionnelle.

**Pièges à retenir :**
- Le pass/block end-to-end **confond** erreur classifier / pas de location / échec geocoder → ne pas l'utiliser comme métrique de classifier.
- **Fuite train/test** : entraîner un sklearn sur le dataset X puis benchmarker sur X = score gonflé. Split strict obligatoire.
- Petits datasets (14-50 lignes) → leaderboard bruité, classements peu significatifs.
- Threshold figé biaise la comparaison de modèles → viser PR-AUC / threshold par modèle.

### Sandbox classifiers scikit-learn self-contained (epic)

Rester dans l'app pour tester une **famille curée** de classifiers scikit — pas un AutoML universel.

- **Pourquoi scikit** : entraînement en **secondes sur CPU** (tient dans 12 Go), 100% self-contained, s'entraîne sur *tes* labels (label space propre), famille d'algos (LogReg, LinearSVC, MultinomialNB, RandomForest, kNN).
- **Le training in-app trivial** : contrairement aux transformers (epic lourd, GPU, jobs longs), sklearn est assez léger pour un training quasi-synchrone → c'est le **seul candidat training réaliste tôt**.
- **Se branche sur le benchmark existant** : un sklearn entraîné = un `model_key` de plus (`loader=sklearn`). Le benchmark peut alors **mélanger les paradigmes** (transformer vs SVM vs zero-shot), comparés pomme-à-pomme.
- **Vectorizer par défaut** : TF-IDF **char n-grams (3-5)** — robuste au multilingue des tweets (fautes, hashtags).
- **Hyperparams** : presets figés par algo pour commencer, exposables ensuite (éviter le sandbox infini).

**Décisions actées du brainstorm :**
- **Inférence** dans le model-server (loader `sklearn`/joblib), pour garder un seul chemin d'inférence uniforme.
- **UX "un clic"** : sélection modèles + dataset + params (`random_state`, taille d'échantillon) → train sweep (N artefacts) → benchmark auto → leaderboard.
- **Métriques** : le training rapporte un F1 de val (indicatif) ; la comparaison officielle reste le benchmark.

### Autres pistes V2

- Swap du dump Photon par pays (mono-pays chargé à la fois vu la contrainte RAM).
- Lookup par nom (dataset/pipeline) au lieu des UUIDs.
- Verrou/queue de concurrence pour les runs (résout le point model-server mono-état).
- Parallélisation via Celery/worker dédié.
