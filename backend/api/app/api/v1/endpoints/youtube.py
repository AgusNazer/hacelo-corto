"""Endpoints para publicación de videos en YouTube"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.youtube_upload_service import YouTubeUploadService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/youtube", tags=["YouTube"])


@router.post("/publish/{video_id}", response_model=Dict[str, Any])
async def publish_video_to_youtube(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Publica un video procesado en YouTube.
    
    El usuario debe haber conectado su cuenta de YouTube previamente
    mediante Google OAuth (GET /api/v1/auth/google/login).
    
    Args:
        video_id: UUID del video en nuestra base de datos
        current_user: Usuario autenticado (inyectado automáticamente)
        db: Sesión de base de datos (inyectada automáticamente)
    
    Returns:
        Información del video publicado en YouTube (ID, URL, etc.)
    
    Raises:
        400: Usuario no tiene cuenta de YouTube conectada
        404: Video no encontrado
        500: Error al subir a YouTube
    """
    logger.info(f"📤 Solicitud de publicación en YouTube - video_id={video_id}, user_id={current_user.id}")
    
    # TODO: Aquí deberías:
    # 1. Buscar el video en la DB por video_id
    # 2. Verificar que pertenece al current_user
    # 3. Verificar que el video está procesado y listo
    # 4. Obtener la ruta del video en MinIO
    # 5. Descargar el video de MinIO a un archivo temporal
    
    # Por ahora, simulamos que el video existe
    # En producción, esto debe integrarse con tu modelo Video
    
    try:
        youtube_service = YouTubeUploadService(db)
        
        # Metadata del video (deberías obtenerla de tu modelo Video)
        title = f"Video {video_id}"  # Placeholder
        description = "Video generado con NoCountry Video Processor"
        tags = ["shorts", "youtube", "ai-generated"]
        
        # Ruta temporal (en producción esto viene de MinIO)
        video_file_path = f"/tmp/videos/{video_id}.mp4"  # Placeholder
        
        result = await youtube_service.upload_video(
            user_id=str(current_user.id),
            video_file_path=video_file_path,
            title=title,
            description=description,
            tags=tags,
            privacy_status="private",  # Recomendado: empezar privado
        )
        
        logger.info(f"✅ Video publicado en YouTube: {result['video_url']}")
        
        return {
            "success": True,
            "message": "Video publicado en YouTube exitosamente",
            "youtube_video_id": result["video_id"],
            "youtube_url": result["video_url"],
            "published_at": result["uploaded_at"],
        }
        
    except HTTPException:
        raise  # Re-lanzar HTTPExceptions del service
    except Exception as e:
        logger.error(f"❌ Error inesperado publicando video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )


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
