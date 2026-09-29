from fastapi import APIRouter, Query

from backend.schemas.response_models import HistoryResponse
from backend.services.data_service import get_prediction_history


router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=HistoryResponse)
def history(limit: int = Query(default=100, ge=1, le=500)) -> HistoryResponse:
    return HistoryResponse(records=get_prediction_history(limit=limit))
