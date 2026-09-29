from fastapi import APIRouter, Depends, HTTPException, status

from backend.schemas.request_models import MetricsRequest
from backend.schemas.response_models import AnomalyResponse
from backend.services.data_service import record_prediction
from backend.services.ml_service import MLService, get_ml_service
from backend.utils.logger import get_logger


router = APIRouter(prefix="/anomaly", tags=["anomaly"])
logger = get_logger(__name__)


@router.post("", response_model=AnomalyResponse)
def detect_anomaly(
    payload: MetricsRequest,
    ml_service: MLService = Depends(get_ml_service),
) -> AnomalyResponse:
    try:
        logger.info("anomaly request received")
        analysis = ml_service.analyze_metrics(payload)
        record_prediction(payload, analysis.failure, analysis.anomaly)
        logger.info(
            "anomaly detection completed",
            extra={
                "is_anomaly": analysis.anomaly.is_anomaly,
                "score": analysis.anomaly.score,
            },
        )
        return analysis.anomaly
    except FileNotFoundError as exc:
        logger.exception("model file missing during anomaly detection")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        logger.exception("anomaly request failed")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
