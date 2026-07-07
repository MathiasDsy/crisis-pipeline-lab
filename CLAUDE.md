# Early Fire Detection

## Stack

- Vue 3
- TypeScript
- Pinia
- FastAPI
- PostgreSQL
- Docker
- Leaflet

## Architecture

backend/
api/
services/
repositories/
models/

frontend/
components/
views/
stores/

## Exécution locale (Docker)

- Stack de dev par défaut (`docker compose up`) : `postgres`, `model-server`, `pipeline-api` uniquement.
- Stack complète (`docker compose --profile full up`) : ajoute `frontend` et `photon`.
- Les services attendent que leurs dépendances soient `healthy` (healthchecks), pas seulement démarrées.
- Géocodage : `GEOCODING_ENABLED` (défaut `true` dans le code, `false` dans la stack dev car Photon en est absent). Le step `geocoder` est skippé proprement (`blocked`, pas `error`) quand il est désactivé. Pour l'activer : `GEOCODING_ENABLED=true docker compose --profile full up`.
- Simulation : `/simulation/start` est synchrone (charge les modèles puis exécute toute la run avant de répondre). Le streaming de progression live est reporté en v2.
- Les modèles ne vivent qu'en RAM du `model-server` : ils sont rechargés à chaque `/simulation/start`.

## Coding Rules

- Composition API uniquement.
- TypeScript strict.
- Fonctions courtes (<50 lignes quand possible).
- Pas de duplication.
- Les appels SQL passent par les repositories.
- Les routes FastAPI restent fines.
- La logique métier appartient aux services.
- Les commentaires (code et scripts) sont rédigés en anglais.

## UI

- Interface sobre.
- Inspirée de GitHub / Linear.
- Responsive.
- Peu de couleurs.
- Utiliser les composants existants avant d'en créer de nouveaux.

## Avant de coder

Toujours :

1. analyser le problème ;
2. proposer une solution ;
3. vérifier si des composants similaires existent ;
4. minimiser les modifications.

## Lorsqu'une fonctionnalité est terminée

- vérifier le typage TypeScript ;
- vérifier que le projet compile ;
- ne pas casser les fonctionnalités existantes.
