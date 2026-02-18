from uuid import UUID
from datetime import datetime
from app.schemas.base import BaseSchema
from app.models.job import JobStatus, JobType

class JobReframeResponse(BaseSchema):
    job_id: UUID
    job_type: JobType
    status: JobStatus
    filename: str
    created_at: datetime

class JobStatusResponse(BaseSchema):
    job_id: UUID
    status: JobStatus
    output_path: str | None = None
    