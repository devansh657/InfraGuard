from fastapi import APIRouter

from backend.schemas.response_models import ReportResponse
from backend.services.data_service import generate_incident_report


router = APIRouter(prefix="/report", tags=["report"])


@router.get("", response_model=ReportResponse)
def report() -> ReportResponse:
    return generate_incident_report()
