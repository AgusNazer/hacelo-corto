from uuid import UUID, uuid4
from datetime import datetime
from app.core.config import settings
from sqlalchemy.orm import Session
from app.models.job import Job, JobStatus, JobType
from app.models.video import Video
from app.schemas.job import JobReframeResponse, JobStatusResponse
from app.utils.exceptions import (
    NotFoundException,
)


class JobService:
    """Servicio de Jobs - Persiste un Job, luego envia mensaje a Redis"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def mock_reframe_video(self, video_id: UUID, user_id: UUID) -> JobReframeResponse:
        # MOCK temporal
        return JobReframeResponse(
            job_id=UUID("00000000-0000-0000-0000-000000000001"),
            job_type=JobType.REFRAME,
            status=JobStatus.PENDING,
            filename="mock_video.mp4",
            created_at=datetime(2024, 1, 1)
        )

    def mock_get_job_status(self, job_id: UUID, user_id: UUID) -> JobStatusResponse:
        # MOCK temporal
        return JobStatusResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            output_path=None
        )
    
    def reframe_video(self, video_id: UUID, user_id: UUID) -> Job:
        video = self.db.query(Video).filter(
            Video.id == video_id,
            Video.user_id == user_id
        ).first()

        if not video:
            raise NotFoundException(status_code=404, detail="Video no encontrado")

        job = Job(
            user_id=user_id,
            video_id=video_id,
            job_type=JobType.REFRAME,
            status=JobStatus.PENDING
        )

        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        # TODO: confirmar commit en db y luego enviar a Redis

        return job