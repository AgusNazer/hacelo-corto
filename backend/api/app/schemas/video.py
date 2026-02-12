from datetime import datetime
from uuid import UUID
from app.schemas.base import BaseSchema


class VideoUploadResponse(BaseSchema):
    video_id: UUID
    bucket: str
    object_key: str
    filename: str
    content_type: str | None
    size_bytes: int
    user_id: UUID | None
    storage_path: str
    uploaded_at: datetime