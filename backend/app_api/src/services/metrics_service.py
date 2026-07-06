from src.repositories.tweet_repository import list_tweets_by_run_id, count_tweets_by_run_id
from src.repositories.pipeline_step_repository import list_step_executions_by_run_id


def compute_run_metrics(run_id: str) -> dict:
    total = count_tweets_by_run_id(run_id)
    tweets = list_tweets_by_run_id(run_id, limit=total, offset=0)
    steps = list_step_executions_by_run_id(run_id, limit=total * 20, offset=0)

    # Index: tweet_id -> list of step executions (ordered by step_index)
    steps_by_tweet: dict[str, list] = {}
    for step in steps:
        tid = str(step["tweet_id"])
        steps_by_tweet.setdefault(tid, []).append(step)

    labeled = [t for t in tweets if t.get("label") is not None]

    if not labeled:
        return {
            "run_id": run_id,
            "total_tweets": total,
            "labeled_tweets": 0,
            "warning": "No labeled tweets found — add a 'label' column to your CSV.",
        }

    tp = fp = fn = tn = 0
    unlabeled = 0
    errored = 0
    results = []

    for tweet in tweets:
        label = tweet.get("label")
        if label is None:
            unlabeled += 1
            continue

        tweet_steps = steps_by_tweet.get(str(tweet["id"]), [])

        # Un tweet dont une étape a échoué techniquement (timeout, model-server down)
        # n'a pas de prédiction fiable → on l'exclut du scoring au lieu de le compter comme négatif.
        if any(step["status"] == "error" for step in tweet_steps):
            errored += 1
            continue

        predicted = _is_predicted_positive(tweet_steps)

        if label and predicted:
            tp += 1
        elif not label and predicted:
            fp += 1
        elif label and not predicted:
            fn += 1
        else:
            tn += 1

        results.append({
            "tweet_id": str(tweet["id"]),
            "label": label,
            "predicted": predicted,
        })

    scored = tp + fp + fn + tn
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / scored if scored else 0.0

    return {
        "run_id": run_id,
        "total_tweets": total,
        "labeled_tweets": len(labeled),
        "scored_tweets": scored,
        "errored_tweets": errored,
        "unlabeled_tweets": unlabeled,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "per_tweet": results,
    }


def _is_predicted_positive(tweet_steps: list) -> bool:
    """A tweet is positive if it was never blocked in the pipeline."""
    if not tweet_steps:
        return False
    for step in tweet_steps:
        if step["status"] == "blocked":
            return False
    return True
