import threading
import uuid
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from surfer_worker import run_surfer_complete


@dataclass
class SurferResult:
    image_name: str


class SurferService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._chunk_size = 1024 * 1024

    @property
    def max_upload_bytes(self) -> int:
        return settings.max_upload_mb * 1024 * 1024

    def generate(self, file: UploadFile) -> SurferResult:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing filename",
            )

        extension = Path(file.filename).suffix.lower()
        if extension not in settings.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type",
            )

        unique_prefix = uuid.uuid4().hex[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = f"{timestamp}_{unique_prefix}_{Path(file.filename).name.replace(' ', '_')}"
        upload_path = settings.upload_folder / safe_name

        total_size = 0
        try:
            with upload_path.open("wb") as target:
                while True:
                    chunk = file.file.read(self._chunk_size)
                    if not chunk:
                        break

                    total_size += len(chunk)
                    if total_size > self.max_upload_bytes:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File too large, max {settings.max_upload_mb}MB",
                        )

                    target.write(chunk)
        finally:
            file.file.close()

        image_name = upload_path.stem + ".png"
        output_path = settings.output_folder / image_name
        grid_path = upload_path.with_suffix(".grd")

        with self._lock:
            try:
                run_surfer_complete(
                    data_file=str(upload_path),
                    output_folder=str(settings.output_folder),
                    surfer_prog_id=settings.surfer_prog_id,
                    surfer_exe_path=settings.surfer_exe_path,
                    clr_path=settings.surfer_clr_path,
                    visible=settings.surfer_visible,
                    screen_updating=settings.surfer_screen_updating,
                )
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Surfer worker failed: {exc}",
                ) from exc
            finally:
                if upload_path.exists():
                    upload_path.unlink()
                if grid_path.exists():
                    grid_path.unlink()

        if not output_path.exists():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Output image was not generated",
            )

        return SurferResult(image_name=image_name)


surfer_service = SurferService()
