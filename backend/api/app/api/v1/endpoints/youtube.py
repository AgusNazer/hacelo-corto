"""Endpoints para publicación de videos en YouTube"""

import logging
import os
import tempfile
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel

from app.core.dependencies import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.models.video import Video
from app.models.enums import VideoStatus
from app.services.youtube_upload_service import YouTubeUploadService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/youtube", tags=["YouTube"])


class YouTubePublishRequest(BaseModel):
    """Request body para publicar video en YouTube"""
    title: str | None = None
    description: str | None = None
    privacy: str = "private"  # "public", "private", "unlisted"


@router.post("/publish/{video_id}", response_model=Dict[str, Any])
async def publish_video_to_youtube(
    video_id: str,
    request: YouTubePublishRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Publica un video procesado en YouTube.
    
    El usuario debe haber conectado su cuenta de YouTube previamente
    mediante Google OAuth (GET /api/v1/auth/google/authorize).
    
    Args:
        video_id: UUID del video en nuestra base de datos
        request: Configuración de publicación (título, descripción, privacidad)
        current_user: Usuario autenticado (inyectado automáticamente)
        db: Sesión de base de datos (inyectada automáticamente)
    
    Returns:
        Información del video publicado en YouTube (ID, URL, etc.)
    
    Raises:
        400: Usuario no tiene cuenta de YouTube conectada
        403: Video no pertenece al usuario
        404: Video no encontrado
        500: Error al subir a YouTube
    """
    logger.info(f"📤 Solicitud de publicación en YouTube - video_id={video_id}, user_id={current_user.id}")
    
    # 1. Buscar el video en la base de datos
    try:
        video_uuid = UUID(video_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="video_id debe ser un UUID válido"
        )
    
    video = db.query(Video).filter(Video.id == video_uuid).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video {video_id} no encontrado"
        )
    
    # 2. Verificar que el video pertenece al usuario actual
    if video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para publicar este video"
        )
    
    # 3. Verificar que el video está listo para publicar
    if video.status not in [VideoStatus.COMPLETED, VideoStatus.READY]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Video aún no está listo. Estado actual: {video.status}"
        )
    
    if not video.storage_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video no tiene ruta de almacenamiento"
        )
    
    # 4. Descargar video de MinIO a archivo temporal
    temp_file = None
    try:
        storage_service = StorageService()
        
        logger.info(f"📥 Descargando video de MinIO: {video.storage_path}")
        
        # Crear archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        temp_file_path = temp_file.name
        temp_file.close()
        
        # Descargar desde MinIO usando el método correcto del StorageService
        # El storage_path ya contiene el bucket y object name en formato: bucket/path/file.mp4
        bucket_name = settings.MINIO_BUCKET_VIDEOS
        object_name = video.storage_path
        
        # Usar boto3 client para descargar
        storage_service.s3_client.download_file(
            Bucket=bucket_name,
            Key=object_name,
            Filename=temp_file_path
        )
        
        logger.info(f"✅ Video descargado a: {temp_file_path}")
        
        # 5. Preparar metadata del video
        title = request.title or video.original_filename or f"Video {video_id[:8]}"
        description = request.description or "Video generado con NoCountry Video Processor"
        privacy = request.privacy
        
        # Tags basados en las dimensiones del video
        tags = ["nocountry", "ai"]
        if video.width and video.height and video.height > video.width:
            tags.append("shorts")
        
        # 6. Subir a YouTube
        youtube_service = YouTubeUploadService(db)
        
        result = await youtube_service.upload_video(
            user_id=str(current_user.id),
            video_file_path=temp_file_path,
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy,
        )
        
        logger.info(f"✅ Video publicado en YouTube: {result['video_url']}")
        
        # 7. (Opcional) Actualizar estado del video en BD
        # video.status = VideoStatus.PUBLISHED
        # db.commit()
        
        return {
            "success": True,
            "message": "Video publicado en YouTube exitosamente",
            "video_id": str(video.id),
            "youtube_video_id": result["video_id"],
            "youtube_url": result["video_url"],
            "title": result["title"],
            "privacy": result["privacy_status"],
            "thumbnail_url": result.get("thumbnail_url"),
        }
    
    except HTTPException:
        raise  # Re-lanzar HTTPExceptions
    except Exception as e:
        logger.error(f"❌ Error inesperado publicando video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )
    finally:
        # 8. Limpiar archivo temporal
        if temp_file and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info(f"🗑️ Archivo temporal eliminado: {temp_file_path}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo eliminar archivo temporal: {e}")


@router.get("/status")
async def check_youtube_connection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Verifica si el usuario tiene una cuenta de YouTube conectada.
    
    Útil para que el frontend sepa si debe mostrar el botón de
    "Conectar YouTube" o "Publicar en YouTube".
    
    Returns:
        Estado de la conexión de YouTube del usuario
    """
    from app.models.oauth_token import OAuthToken
    
    oauth_token = (
        db.query(OAuthToken)
        .filter(
            OAuthToken.user_id == current_user.id,
            OAuthToken.provider == "youtube"
        )
        .first()
    )
    
    if not oauth_token:
        return {
            "connected": False,
            "message": "Usuario no tiene cuenta de YouTube conectada"
        }
    
    return {
        "connected": True,
        "provider_username": oauth_token.provider_username,
        "provider_user_id": oauth_token.provider_user_id,
        "token_expires_at": oauth_token.expires_at.isoformat() if oauth_token.expires_at else None,
        "is_expired": oauth_token.is_expired(),
    }
