from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.schemas.config import GlobalConfigPayload, PickDirectoryPayload, PickFilePayload

router = APIRouter()


@router.get("/config")
def get_runtime_config() -> dict:
    return {
        "raw": settings.raw_config,
        "upload_folder": str(settings.upload_folder),
        "output_folder": str(settings.output_folder),
        "max_upload_mb": settings.max_upload_mb,
        "allowed_extensions": sorted(settings.allowed_extensions),
        "surfer": {
            "prog_id": settings.surfer_prog_id,
            "install_dir": settings.surfer_install_dir,
            "exe_path": settings.surfer_exe_path,
            "clr_path": settings.surfer_clr_path,
            "default_colormap": settings.surfer_default_colormap,
            "visible": settings.surfer_visible,
            "screen_updating": settings.surfer_screen_updating,
        },
    }


@router.put("/config")
def update_runtime_config(payload: GlobalConfigPayload) -> dict:
    data = payload.dict(exclude_none=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No config updates provided",
        )

    updated = settings.update_and_persist(data)
    return {"code": 200, "msg": "config updated", "config": updated}


@router.post("/config/pick-directory")
def pick_directory(payload: PickDirectoryPayload) -> dict:
    try:
        from tkinter import Tk, filedialog

        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askdirectory(
            title=payload.title,
            initialdir=payload.initial_path or None,
            mustexist=True,
        )
        root.destroy()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Open directory dialog failed: {exc}",
        ) from exc

    return {"code": 200, "path": selected or ""}


@router.post("/config/pick-file")
def pick_file(payload: PickFilePayload) -> dict:
    try:
        from tkinter import Tk, filedialog

        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        file_types = payload.file_types or [["All Files", "*.*"]]
        selected = filedialog.askopenfilename(
            title=payload.title,
            initialdir=payload.initial_path or None,
            filetypes=[tuple(x) for x in file_types],
        )
        root.destroy()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Open file dialog failed: {exc}",
        ) from exc

    return {"code": 200, "path": selected or ""}
