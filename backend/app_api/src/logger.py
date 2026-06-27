import traceback
from datetime import datetime, timezone


def _print(level: str, context: str, message: str, details: dict | None) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    prefix = f"[{ts}] [{level.upper()}] [{context}]"
    print(f"{prefix} {message}")
    if details:
        for k, v in details.items():
            print(f"  {k}: {v}")


def _insert(
    level: str,
    context: str,
    message: str,
    run_id: str | None,
    details: dict | None,
) -> None:
    try:
        from src.repositories.log_repository import insert_log
        insert_log(message=message, level=level, context=context, run_id=run_id, details=details)
    except Exception as e:
        print(f"[LOGGER] Failed to write log to DB: {e}")


def info(message: str, context: str = "", run_id: str | None = None, details: dict | None = None) -> None:
    _print("info", context, message, details)
    _insert("info", context, message, run_id, details)


def warning(message: str, context: str = "", run_id: str | None = None, details: dict | None = None) -> None:
    _print("warning", context, message, details)
    _insert("warning", context, message, run_id, details)


def error(message: str, context: str = "", run_id: str | None = None, details: dict | None = None, exc: Exception | None = None) -> None:
    if exc is not None:
        details = {**(details or {}), "traceback": traceback.format_exc()}
    _print("error", context, message, details)
    _insert("error", context, message, run_id, details)
