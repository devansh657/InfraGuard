from fastapi import APIRouter, Depends, HTTPException, status

from backend.schemas.request_models import MetricsRequest
from backend.schemas.response_models import FailurePredictionResponse
from backend.services.data_service import record_prediction
from backend.services.ml_service import MLService, get_ml_service
from backend.utils.logger import get_logger


router = APIRouter(prefix="/predict", tags=["prediction"])
logger = get_logger(__name__)


@router.post("", response_model=FailurePredictionResponse)
def predict_failure(
    payload: MetricsRequest,
    ml_service: MLService = Depends(get_ml_service),
) -> FailurePredictionResponse:
    try:
        logger.info("prediction request received")
        analysis = ml_service.analyze_metrics(payload)
        record_prediction(payload, analysis.failure, analysis.anomaly)
        logger.info(
            "failure prediction completed",
            extra={
                "failure_probability": analysis.failure.failure_probability,
                "prediction": analysis.failure.prediction,
            },
        )
        return analysis.failure
    except FileNotFoundError as exc:
        logger.exception("model file missing during prediction")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        logger.exception("prediction request failed")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
