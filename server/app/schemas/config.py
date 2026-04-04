from pydantic import BaseModel, Field


class SurferConfigPayload(BaseModel):
    prog_id: str = Field(default="Surfer.Application")
    install_dir: str = Field(default="")
    exe_path: str = Field(default="")
    clr_path: str = Field(default="")
    default_colormap: str = Field(default="Terrain.clr")
    visible: bool = Field(default=False)
    screen_updating: bool = Field(default=False)


class GlobalConfigPayload(BaseModel):
    output_folder: str | None = None
    upload_folder: str | None = None
    max_upload_mb: int | None = Field(default=None, ge=1, le=1024)
    surfer: SurferConfigPayload | None = None


class PickDirectoryPayload(BaseModel):
    title: str = Field(default="选择目录")
    initial_path: str = Field(default="")


class PickFilePayload(BaseModel):
    title: str = Field(default="选择文件")
    initial_path: str = Field(default="")
    file_types: list[list[str]] | None = None
