from fastapi import APIRouter, Depends, HTTPException, status

from backend.schemas.request_models import MetricsRequest
from backend.schemas.response_models import AnalysisResponse
from backend.services.data_service import record_prediction
from backend.services.ml_service import MLService, get_ml_service
from backend.utils.logger import get_logger


router = APIRouter(prefix="/diagnose", tags=["diagnosis"])
logger = get_logger(__name__)


@router.post("", response_model=AnalysisResponse)
def diagnose(
    payload: MetricsRequest,
    ml_service: MLService = Depends(get_ml_service),
) -> AnalysisResponse:
    try:
        logger.info("diagnosis request received")
        analysis = ml_service.analyze_metrics(payload)
        record_prediction(payload, analysis.failure, analysis.anomaly)
        logger.info(
            "diagnosis completed",
            extra={
                "failure_probability": analysis.failure.failure_probability,
                "prediction": analysis.failure.prediction,
                "is_anomaly": analysis.anomaly.is_anomaly,
                "anomaly_score": analysis.anomaly.score,
            },
        )
        return analysis
    except FileNotFoundError as exc:
        logger.exception("model file missing during diagnosis")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        logger.exception("diagnosis request failed")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
