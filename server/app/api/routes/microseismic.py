from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.services.centerline_service import centerline_service
from app.services.microseismic_service import microseismic_service

router = APIRouter()


@router.get("/microseismic-centerline")
def get_microseismic_centerline():
    try:
        return centerline_service.payload()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load centerline database: {exc}",
        ) from exc


@router.post("/microseismic-warning")
def calculate_microseismic_warning(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename")
    if not file.filename.lower().endswith(".xls"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .xls files are supported")

    contents = file.file.read()
    if not contents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    try:
        return microseismic_service.build_warning_data(contents, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate microseismic warning: {exc}",
        ) from exc
    finally:
        file.file.close()
