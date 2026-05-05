import threading
import uuid
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.services.microseismic_service import microseismic_service
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
        if extension != ".xls":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Feature A calculates W before plotting and currently supports .xls only",
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

        surfer_data_path = upload_path.with_name(upload_path.stem + "_computed_w.dat")
        image_name = upload_path.stem + ".png"
        output_path = settings.output_folder / image_name
        grid_path = surfer_data_path.with_suffix(".grd")

        with self._lock:
            try:
                self._write_computed_w_dat(upload_path, surfer_data_path)
                run_surfer_complete(
                    data_file=str(surfer_data_path),
                    output_folder=str(settings.output_folder),
                    output_name=image_name,
                    x_col=1,
                    y_col=2,
                    z_col=3,
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
                if surfer_data_path.exists():
                    surfer_data_path.unlink()
                if grid_path.exists():
                    grid_path.unlink()

        if not output_path.exists():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Output image was not generated",
            )

        return SurferResult(image_name=image_name)

    def _write_computed_w_dat(self, source_path: Path, target_path: Path) -> None:
        rows = microseismic_service.build_surfer_rows(source_path.read_bytes())
        if not rows:
            raise ValueError("No valid rows after W calculation")

        with target_path.open("w", encoding="ascii", newline="\n") as fp:
            for row in rows:
                fp.write(
                    "{map_x:.10f} {map_y:.10f} {w:.12g} {r:.10f} "
                    "{energy_j:.12g} {z:.10f} {event_id}\n".format(
                        map_x=row["map_x"],
                        map_y=row["map_y"],
                        w=row["w"],
                        r=row["r"],
                        energy_j=row["energy_j"],
                        z=row["z"] if row["z"] is not None else 0.0,
                        event_id=row["event_id"],
                    )
                )


surfer_service = SurferService()
