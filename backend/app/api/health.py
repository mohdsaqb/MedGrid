from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def get_health_status() -> dict[str, str]:
    """
    Confirms the API process is running and reachable.

    Used by: load balancers / uptime checks in production (Module 12),
    and by us right now to prove frontend <-> backend wiring works.
    """
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "environment": settings.environment,
    }
