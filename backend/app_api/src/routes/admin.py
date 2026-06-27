from fastapi import APIRouter
from src.database.db import check_database_connection
from src.repositories.log_repository import list_logs

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.get("/health")
def health():
    """
    Health check global de l'API.
    """
    return {
        "status": "ok",
    }


@router.get("/stats")
def get_stats():
    """
    Dashboard général.
    """
    return {
        "datasets": 0,
        "pipeline_configs": 0,
        "pipeline_runs": 0,
        "tweets": 0,
        "events": 0,
        "models": 0,
    }



@router.post("/sync")
def sync_all():
    """
    Relance tous les scanners.
    """
    return {
        "status": "success",
    }


@router.get("/system")
def system_info():
    """
    Informations runtime.
    """
    return {
        "environment": "development",
        "api_version": "1.0.0",
    }

@router.get("/database")
def database_health():
    """
    Vérifie la connexion PostgreSQL.
    """
    return check_database_connection()


@router.get("/logs")
def get_logs(
    run_id: str | None = None,
    level: str | None = None,
    limit: int = 200,
    offset: int = 0,
):
    logs = list_logs(run_id=run_id, level=level, limit=limit, offset=offset)
    return {
        "logs": logs,
        "count": len(logs),
        "filters": {"run_id": run_id, "level": level},
    }