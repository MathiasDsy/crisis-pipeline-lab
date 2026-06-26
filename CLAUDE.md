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

## Coding Rules

- Composition API uniquement.
- TypeScript strict.
- Fonctions courtes (<50 lignes quand possible).
- Pas de duplication.
- Les appels SQL passent par les repositories.
- Les routes FastAPI restent fines.
- La logique métier appartient aux services.

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
