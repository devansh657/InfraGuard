from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.schemas.response_models import UploadResponse
from backend.services.data_service import save_uploaded_dataset


router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=UploadResponse)
async def upload_dataset(file: UploadFile = File(...)) -> UploadResponse:
    try:
        return await save_uploaded_dataset(file)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
