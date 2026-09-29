from fastapi import APIRouter

from backend.schemas.response_models import BenchmarkReportResponse, EDAResponse, ModelInfoResponse
from backend.services.model_info_service import (
    get_benchmark_payload,
    get_eda_payload,
    get_model_info_payload,
)


router = APIRouter(tags=["model"])


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    return ModelInfoResponse(**get_model_info_payload())


@router.get("/eda", response_model=EDAResponse)
def eda() -> EDAResponse:
    return EDAResponse(**get_eda_payload())


@router.get("/benchmark-report", response_model=BenchmarkReportResponse)
def benchmark_report() -> BenchmarkReportResponse:
    return BenchmarkReportResponse(**get_benchmark_payload())
