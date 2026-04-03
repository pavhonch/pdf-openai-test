from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    status: str
    page_count: int | None
    file_size: int
    summary: str | None
    error_message: str | None
    created_at: datetime
