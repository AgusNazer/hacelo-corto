from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.user import User
from app.models.video import Video
from app.schemas.video import VideoUploadResponse

router = APIRouter(prefix="/videos", tags=["Videos"])


def _get_s3_client():
    scheme = "https" if settings.MINIO_SECURE else "http"
    endpoint_url = f"{scheme}://{settings.MINIO_ENDPOINT}"
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        region_name="us-east-1",
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"})
    )


def _ensure_bucket_exists(s3_client, bucket: str) -> None:
    try:
        s3_client.head_bucket(Bucket=bucket)
    except ClientError:
        s3_client.create_bucket(Bucket=bucket)


def _create_video_record(
    db: Session,
    original_filename: str,
    user_id: UUID | None
) -> Video:
    # guardar metadatos mínimos del video en la base de datos.
    # por ahora en la tabla video, pero luego se podría migrar 
    # a la tabla metadata 
    video = Video(
        user_id=user_id,
        original_filename=original_filename,
        storage_path=None,
        status="uploaded"
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


@router.post(
    "/upload",
    response_model=VideoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir video",
    description="Sube un video a MinIO y guarda la metadata",
    responses={
        201: {"description": "Video subido"},
        400: {"description": "Archivo inválido"},
        401: {"description": "No autenticado"}
    }
)
async def upload_video(
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)]
) -> VideoUploadResponse:
    # Public upload: valida el archivo, guarda la metadata ( ver luego la tabla metadata, ahora se guarda en la misma tabla),
    # falta definir si vamos a permitir subir el mismo video varias veces (mismo filename) o no.
    # Por ahora lo deje permitido
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo sin nombre")

    if file.content_type and not file.content_type.startswith("video/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de archivo inválido")

    try:
        file.file.seek(0, 2)
        size_bytes = file.file.tell()
        file.file.seek(0)
    except Exception:
        size_bytes = 0

    if size_bytes == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo vacío")

    bucket = settings.MINIO_BUCKET_VIDEOS
    object_key = f"public/{uuid4()}_{file.filename}"
    
    s3_client = _get_s3_client()
    try:
        _ensure_bucket_exists(s3_client, bucket)
        # Asegurar que el cursor del archivo esté al inicio antes de subir
        file.file.seek(0)
        extra_args = {"ContentType": file.content_type} if file.content_type else None
        if extra_args:
            s3_client.upload_fileobj(file.file, bucket, object_key, ExtraArgs=extra_args)
        else:
            s3_client.upload_fileobj(file.file, bucket, object_key)
    except ClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error subiendo a MinIO: {exc}"
        )

    video = _create_video_record(db, file.filename, None)
    # Actualizar storage_path despues de subir exitosamente
    video.storage_path = f"s3://{bucket}/{object_key}"
    db.commit()

    return VideoUploadResponse(
        video_id=video.id,
        bucket=bucket,
        object_key=object_key,
        filename=file.filename,
        content_type=file.content_type,
        size_bytes=size_bytes,
        user_id=None,
        storage_path=video.storage_path,
        uploaded_at=datetime.utcnow()
    )


@router.post(
    "/upload/auth",
    response_model=VideoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir video (autenticado)",
    description="Sube un video (requiere token) y guarda la metadata",
    responses={
        201: {"description": "Video subido y job encolado"},
        400: {"description": "Archivo inválido"},
        401: {"description": "No autenticado"}
    }
)
async def upload_video_authenticated(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)]
) -> VideoUploadResponse:
    # Authenticated upload: misma funcionalidad pero asociada a un usuario. Validar token y extraer user_id.
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo sin nombre")

    if file.content_type and not file.content_type.startswith("video/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de archivo inválido")

    try:
        file.file.seek(0, 2)
        size_bytes = file.file.tell()
        file.file.seek(0)
    except Exception:
        size_bytes = 0

    if size_bytes == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo vacío")

    bucket = settings.MINIO_BUCKET_VIDEOS
    object_key = f"{current_user.id}/{uuid4()}_{file.filename}"

    s3_client = _get_s3_client()
    try:
        _ensure_bucket_exists(s3_client, bucket)
        # Asegurar que el cursor del archivo esté al inicio antes de subir
        file.file.seek(0)
        extra_args = {"ContentType": file.content_type} if file.content_type else None
        if extra_args:
            s3_client.upload_fileobj(file.file, bucket, object_key, ExtraArgs=extra_args)
        else:
            s3_client.upload_fileobj(file.file, bucket, object_key)
    except ClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error subiendo a MinIO: {exc}"
        )

    video = _create_video_record(db, file.filename, current_user.id)
    # actualizar storage_path despues de subir exitosamente
    video.storage_path = f"s3://{bucket}/{object_key}"
    db.commit()

    return VideoUploadResponse(
        video_id=video.id,
        bucket=bucket,
        object_key=object_key,
        filename=file.filename,
        content_type=file.content_type,
        size_bytes=size_bytes,
        user_id=current_user.id,
        storage_path=video.storage_path,
        uploaded_at=datetime.utcnow()
    )