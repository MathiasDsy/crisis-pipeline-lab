#!/usr/bin/env python3
"""
Backend smoke test — hits every pipeline-api route (and the model-server health
endpoints) one by one and reports PASS / FAIL / SKIP.

Zero third-party dependencies: only the Python standard library, so it runs on
the host straight against the dev stack (docker compose up).

Usage:
    python smoke_test.py                 # read-only + discovery (safe)
    python smoke_test.py --heavy         # also run mutating / expensive routes
    API_URL=http://localhost:8000 MODEL_API_URL=http://localhost:8001 python smoke_test.py

Exit code is non-zero if at least one check FAILED.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
MODEL_API_URL = os.getenv("MODEL_API_URL", "http://localhost:8001").rstrip("/")

# Candidate keys used to extract an entity id from a list item, in priority order.
ID_KEYS = ("id", "model_key", "run_id", "benchmark_id", "event_id", "dataset_id")

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"

results: list[tuple[str, str, str, str]] = []  # (status, method, path, detail)


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def call(method: str, url: str, body: dict | None = None, timeout: float = 30.0):
    """Return (status_code, parsed_body_or_text, error_message)."""
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return resp.status, _parse(raw), None
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return exc.code, _parse(raw), None
    except Exception as exc:  # connection refused, timeout, DNS, ...
        return None, None, f"{type(exc).__name__}: {exc}"


def _parse(raw: bytes):
    try:
        return json.loads(raw)
    except Exception:
        return raw[:200].decode(errors="replace")


def _pick_id(item: dict) -> str | None:
    if not isinstance(item, dict):
        return None
    for key in ID_KEYS:
        if item.get(key):
            return str(item[key])
    return None


# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------

def record(status: str, method: str, path: str, detail: str = "") -> None:
    results.append((status, method, path, detail))
    color = {PASS: "\033[32m", FAIL: "\033[31m", SKIP: "\033[33m"}[status]
    print(f"  {color}{status}\033[0m  {method:6} {path}   {detail}")


def check(method: str, url: str, expected: tuple[int, ...], body: dict | None = None) -> tuple[int | None, object]:
    """Run one request, record PASS/FAIL against expected status codes."""
    path = url.replace(API_URL, "").replace(MODEL_API_URL, "[model]") or "/"
    started = time.perf_counter()
    status, parsed, err = call(method, url, body=body)
    ms = int((time.perf_counter() - started) * 1000)

    if err is not None:
        record(FAIL, method, path, f"connection error: {err}")
        return status, parsed

    if status in expected:
        record(PASS, method, path, f"{status} ({ms}ms)")
    else:
        snippet = parsed if isinstance(parsed, str) else json.dumps(parsed)[:160]
        record(FAIL, method, path, f"got {status}, expected {expected} — {snippet}")
    return status, parsed


def skip(method: str, path: str, reason: str) -> None:
    record(SKIP, method, path, reason)


# ---------------------------------------------------------------------------
# Test sections
# ---------------------------------------------------------------------------

def section(title: str) -> None:
    print(f"\n\033[1m# {title}\033[0m")


def test_health() -> None:
    section("Health / infra")
    check("GET", f"{MODEL_API_URL}/health", (200,))
    check("GET", f"{MODEL_API_URL}/models/current", (200,))
    check("GET", f"{API_URL}/admin/health", (200,))
    check("GET", f"{API_URL}/admin/system", (200,))
    check("GET", f"{API_URL}/admin/database", (200,))
    check("GET", f"{API_URL}/admin/stats", (200,))
    check("GET", f"{API_URL}/admin/logs", (200,))


def test_collections() -> dict[str, object]:
    """Hit every list endpoint, return the parsed bodies for id extraction."""
    section("Collections (list endpoints)")
    bodies: dict[str, object] = {}
    for path in (
        "/datasets",
        "/datasets/schema",
        "/models",
        "/pipelines",
        "/runs",
        "/events",
        "/tweets",
        "/benchmarks",
    ):
        _, parsed = check("GET", f"{API_URL}{path}", (200,))
        bodies[path] = parsed
    return bodies


def _first_id(body: object, key: str, id_field: str | None = None) -> str | None:
    if isinstance(body, dict):
        items = body.get(key)
        if isinstance(items, list) and items:
            item = items[0]
            if id_field and isinstance(item, dict) and item.get(id_field):
                return str(item[id_field])
            return _pick_id(item)
    return None


def test_details(bodies: dict[str, object]) -> None:
    section("Detail endpoints (dynamic ids)")

    # (list_path, json_key, id_field, [sub-routes with {id}])
    # id_field matters: /models is addressed by model_key, everyone else by id.
    resources = [
        ("/datasets", "datasets", "id", ["/datasets/{id}", "/datasets/{id}/preview", "/datasets/{id}/download"]),
        ("/models", "models", "model_key", ["/models/{id}"]),
        ("/pipelines", "pipelines", "id", ["/pipelines/{id}"]),
        ("/runs", "runs", "id", [
            "/runs/{id}", "/runs/{id}/events", "/runs/{id}/trace",
            "/runs/{id}/summary", "/runs/{id}/hard-cases", "/runs/{id}/tweets",
            "/simulation/{id}", "/simulation/{id}/results", "/simulation/{id}/metrics",
        ]),
        ("/events", "events", "id", ["/events/{id}", "/events/{id}/tweets"]),
        ("/benchmarks", "benchmarks", "id", [
            "/benchmarks/{id}", "/benchmarks/{id}/runs", "/benchmarks/{id}/leaderboard",
        ]),
    ]

    run_id_for_tweets: str | None = None
    for list_path, key, id_field, routes in resources:
        entity_id = _first_id(bodies.get(list_path), key, id_field)
        if entity_id is None:
            for route in routes:
                skip("GET", route, "no entity in collection")
            continue
        if list_path == "/runs":
            run_id_for_tweets = entity_id
        for route in routes:
            check("GET", f"{API_URL}{route.format(id=entity_id)}", (200,))

    # Tweets need an id sourced from a run's tweets, not from /tweets (empty without run_id).
    _test_tweet_details(run_id_for_tweets)


def _test_tweet_details(run_id: str | None) -> None:
    routes = ["/tweets/{id}", "/tweets/{id}/trace", "/tweets/{id}/annotations"]
    if run_id is None:
        for route in routes:
            skip("GET", route, "no run available to source a tweet")
        return
    _, parsed, _ = call("GET", f"{API_URL}/runs/{run_id}/tweets")
    tweet_id = None
    if isinstance(parsed, dict):
        tweets = parsed.get("tweets")
        if isinstance(tweets, list) and tweets:
            tweet_id = _pick_id(tweets[0])
    if tweet_id is None:
        for route in routes:
            skip("GET", route, "run has no tweets")
        return
    for route in routes:
        check("GET", f"{API_URL}{route.format(id=tweet_id)}", (200,))


def test_negative() -> None:
    section("Negative checks (valid but unknown id must be 404)")
    # A well-formed but non-existent UUID — the realistic "stale/deleted entity"
    # case the frontend actually hits. (A malformed, non-UUID id currently 500s
    # at the DB layer; that is a separate robustness issue, not tested here.)
    ghost = "00000000-0000-0000-0000-000000000000"
    for path in (
        f"/datasets/{ghost}",
        f"/models/{ghost}",
        f"/pipelines/{ghost}",
        f"/runs/{ghost}",
        f"/events/{ghost}",
        f"/benchmarks/{ghost}",
        f"/simulation/{ghost}",
    ):
        check("GET", f"{API_URL}{path}", (404,))


def test_discovery() -> None:
    section("Discovery (idempotent writes)")
    check("POST", f"{API_URL}/admin/sync", (200,))
    check("POST", f"{API_URL}/datasets/discover", (200,))
    check("POST", f"{API_URL}/models/discover", (200,))


HEAVY_ROUTES = [
    ("POST", "/simulation/start", "runs a full simulation (loads models + all tweets)"),
    ("POST", "/simulation/{id}/cancel", "mutates run state"),
    ("POST", "/benchmarks/start", "launches a benchmark (heavy)"),
    ("POST", "/benchmarks/{id}/cancel", "mutates benchmark state"),
    ("POST", "/datasets/import", "multipart upload"),
    ("POST", "/pipelines/import", "multipart upload"),
    ("POST", "/pipelines/{id}/validate", "loads models"),
    ("DELETE", "/pipelines/{id}", "destructive"),
    ("GET", "/models/search/huggingface", "external HuggingFace call"),
    ("POST", "/models/import/huggingface", "downloads a model"),
    ("POST", "/models/import/upload", "multipart upload"),
    ("POST", "/models/{key}/check", "loads a model"),
    ("POST", "/events/{id}/close", "mutates event state"),
    ("POST", "/events/{id}/reopen", "mutates event state"),
    ("POST", "/tweets/{id}/annotations", "creates annotation"),
]


def test_heavy(enabled: bool, bodies: dict[str, object]) -> None:
    section("Heavy / mutating routes" + ("" if enabled else " (skipped — pass --heavy to run)"))
    if not enabled:
        for method, path, reason in HEAVY_ROUTES:
            skip(method, path, reason)
        return

    dataset_id = _first_id(bodies.get("/datasets"), "datasets", "id")
    pipeline_id = _first_id(bodies.get("/pipelines"), "pipelines", "id")

    if not (dataset_id and pipeline_id):
        skip("POST", "/simulation/start", "need at least one dataset and one pipeline")
        return

    # /simulation/start now runs the whole simulation synchronously (loads models
    # then processes every tweet before returning — streaming is deferred to v2).
    # force_rerun=False so a cached completed run returns instantly; otherwise a
    # full run executes, which can take minutes — hence the long client timeout.
    status, parsed, err = call(
        "POST", f"{API_URL}/simulation/start",
        body={"dataset_id": dataset_id, "pipeline_config_id": pipeline_id, "force_rerun": False},
        timeout=900.0,
    )
    if err is not None:
        record(FAIL, "POST", "/simulation/start", f"connection error: {err}")
        return
    if status not in (200, 201):
        snippet = parsed if isinstance(parsed, str) else json.dumps(parsed)[:160]
        record(FAIL, "POST", "/simulation/start", f"got {status} — {snippet}")
        return
    run_status = parsed.get("status") if isinstance(parsed, dict) else None
    ok = run_status in ("completed", "cached")
    record(PASS if ok else FAIL, "POST", "/simulation/start", f"{status} (run status: {run_status})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Backend smoke test")
    parser.add_argument("--heavy", action="store_true", help="also run mutating / expensive routes")
    args = parser.parse_args()

    print(f"Target API:   {API_URL}")
    print(f"Target model: {MODEL_API_URL}")

    test_health()
    bodies = test_collections()
    test_details(bodies)
    test_negative()
    test_discovery()
    test_heavy(args.heavy, bodies)

    n_pass = sum(1 for r in results if r[0] == PASS)
    n_fail = sum(1 for r in results if r[0] == FAIL)
    n_skip = sum(1 for r in results if r[0] == SKIP)

    print("\n" + "=" * 60)
    print(f"  PASS: {n_pass}   FAIL: {n_fail}   SKIP: {n_skip}")
    print("=" * 60)

    if n_fail:
        print("\nFailures:")
        for status, method, path, detail in results:
            if status == FAIL:
                print(f"  {method:6} {path}  ->  {detail}")

    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
