from fastapi import APIRouter, HTTPException, status

from backend.schemas.response_models import LiveStatusResponse, LiveTickResponse
from backend.services.live_replay_service import get_live_replay_service


router = APIRouter(prefix="/live", tags=["live-monitoring"])


@router.get("/status", response_model=LiveStatusResponse)
def live_status() -> LiveStatusResponse:
    try:
        return LiveStatusResponse(**get_live_replay_service().status())
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Live telemetry stream is unavailable.",
        ) from exc


@router.post("/tick", response_model=LiveTickResponse)
def live_tick() -> LiveTickResponse:
    try:
        return LiveTickResponse(**get_live_replay_service().tick())
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Live telemetry stream is unavailable.",
        ) from exc
