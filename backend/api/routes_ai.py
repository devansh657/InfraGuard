from fastapi import APIRouter, Depends, HTTPException, status

from backend.schemas.request_models import MetricsRequest, WhatIfRequest
from backend.schemas.response_models import AnalystResponse, NovaBriefingResponse, WhatIfResponse
from backend.services.ai_analyst_service import analyze_telemetry, compare_what_if
from backend.services.ml_service import MLService, get_ml_service
from backend.services.nova_service import build_nova_briefing
from backend.utils.logger import get_logger


router = APIRouter(prefix="/ai", tags=["ai-analyst"])
logger = get_logger(__name__)


@router.post("/analyze", response_model=AnalystResponse)
def analyze(
    payload: MetricsRequest,
    ml_service: MLService = Depends(get_ml_service),
) -> AnalystResponse:
    try:
        logger.info("ai analyst request received")
        return analyze_telemetry(payload, ml_service)
    except FileNotFoundError as exc:
        logger.exception("model file missing during ai analysis")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI analyst runtime is unavailable.",
        ) from exc
    except ValueError as exc:
        logger.exception("ai analysis request failed")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/what-if", response_model=WhatIfResponse)
def what_if(
    payload: WhatIfRequest,
    ml_service: MLService = Depends(get_ml_service),
) -> WhatIfResponse:
    try:
        logger.info("ai what-if request received")
        return compare_what_if(payload.baseline, payload.candidate, ml_service)
    except FileNotFoundError as exc:
        logger.exception("model file missing during what-if analysis")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI analyst runtime is unavailable.",
        ) from exc
    except ValueError as exc:
        logger.exception("what-if request failed")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/nova/briefing", response_model=NovaBriefingResponse)
def nova_briefing() -> NovaBriefingResponse:
    try:
        logger.info("nova briefing requested")
        return build_nova_briefing()
    except FileNotFoundError as exc:
        logger.exception("nova runtime unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="NOVA briefing runtime is unavailable.",
        ) from exc
