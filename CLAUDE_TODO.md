# V1 TODO

## Priorité 1 — Bugs à corriger

- [ ] `datasets.py /import` : ajouter le check colonne `label` (copie de la logique de `discover_datasets`)
- [ ] `datasets.py /schema` : ajouter `label` dans `required_columns`
- [ ] `tweets.py GET /{tweet_id}` : guard sur `None` avant `.get("content")`
- [ ] `model_api/main.py` : renommer la deuxième `def load_model` (double définition silencieuse)

## Priorité 2 — Features benchmark core

- [ ] `GET /runs/compare?run_ids=a,b,c` : retourner precision/recall/F1 de chaque run côte à côte
- [ ] `GET /runs/{run_id}/hard-cases` : tweets avec `label=True` ratés par le pipeline (faux négatifs)

## Priorité 3 — Confort & robustesse

- [ ] `GET /datasets/{id}/preview` : retourner les 10 premières lignes du CSV pour vérification avant simulation
- [ ] `GET /runs` : ajouter pagination (`limit` / `offset`)
- [ ] `GET /admin/stats` : brancher les vrais counts depuis la BDD
- [ ] `GET /tweets` : brancher `list_tweets_by_run_id` au lieu de retourner `[]`
- [ ] Stocker les métriques en BDD après chaque run (éviter le recalcul à chaque appel de `/metrics`)

## Priorité 4 — Chantier (post-V1)

- [ ] `POST /simulation/start` asynchrone : job en background + polling de statut pour les gros datasets
