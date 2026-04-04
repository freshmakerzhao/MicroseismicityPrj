from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

from app.schemas.surfer import SurferGenerateResponse
from app.services.surfer_service import surfer_service

router = APIRouter()


@router.post("/generate-surfer", response_model=SurferGenerateResponse)
def generate_surfer_map(request: Request, file: UploadFile = File(...)) -> SurferGenerateResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename")

    result = surfer_service.generate(file)
    image_url = str(request.base_url).rstrip("/") + f"/output/{result.image_name}"

    return SurferGenerateResponse(code=200, imageUrl=image_url, msg="success")
