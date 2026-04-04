from pydantic import BaseModel


class SurferGenerateResponse(BaseModel):
    code: int
    imageUrl: str
    msg: str
