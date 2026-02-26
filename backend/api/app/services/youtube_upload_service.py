"""Servicio para subir videos a YouTube usando YouTube Data API v3"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import httpx
from fastapi import HTTPException, status
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

from app.core.config import settings
from app.models.oauth_token import OAuthToken
from app.models.user import User

logger = logging.getLogger(__name__)


class YouTubeUploadService:
    """
    Servicio para manejar la subida de videos a YouTube.
    
    Implementa:
    - Renovación automática de tokens expirados
    - Upload en partes (resumable upload para videos grandes)
    - Manejo de cuotas y rate limits de YouTube
    """
    
    YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
    YOUTUBE_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    
    def __init__(self, db: Session):
        self.db = db
    
    async def upload_video(
        self,
        user_id: str,
        video_file_path: str,
        title: str,
        description: str = "",
        tags: list[str] = None,
        category_id: str = "22",  # 22 = People & Blogs
        privacy_status: str = "private",  # "public", "private", "unlisted"
    ) -> Dict[str, Any]:
        """
        Sube un video a YouTube usando la API oficial de Google.
        
        Args:
            user_id: ID del usuario que sube el video
            video_file_path: Ruta del archivo de video
            title: Título del video (máx 100 caracteres)
            description: Descripción del video (máx 5000 caracteres)
            tags: Lista de tags/palabras clave (máx 500 caracteres total)
            category_id: ID de categoría de YouTube
            privacy_status: "public", "private", o "unlisted"
            
        Returns:
            Dict con información del video subido (id, url, etc.)
            
        Raises:
            HTTPException: Si el usuario no tiene tokens o hay error en YouTube
        """
        # 1. Verificar que el archivo existe
        if not os.path.exists(video_file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Archivo de video no encontrado: {video_file_path}"
            )
        
        # 2. Obtener y verificar token de YouTube
        access_token = await self._get_valid_access_token(user_id)
        
        # 3. Crear credenciales de Google
        credentials = Credentials(
            token=access_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
        )
        
        # 4. Construir cliente de YouTube API
        youtube = build("youtube", "v3", credentials=credentials)
        
        # 5. Preparar metadata del video
        body = {
            "snippet": {
                "title": title[:100],  # YouTube limita a 100 caracteres
                "description": description[:5000],  # Límite 5000 caracteres
                "tags": tags or [],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            }
        }
        
        logger.info(f"📤 Subiendo video '{title}' a YouTube para user_id={user_id}")
        logger.info(f"📁 Archivo: {video_file_path} ({os.path.getsize(video_file_path)} bytes)")
        
        try:
            # 6. Preparar media upload (con resumable upload para videos grandes)
            media = MediaFileUpload(
                video_file_path,
                mimetype="video/*",
                resumable=True,
                chunksize=1024 * 1024  # 1MB chunks
            )
            
            # 7. Ejecutar upload
            insert_request = youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media
            )
            
            # Upload con progreso (para resumable uploads)
            response = None
            while response is None:
                status_obj, response = insert_request.next_chunk()
                if status_obj:
                    progress = int(status_obj.progress() * 100)
                    logger.info(f"📊 Upload progress: {progress}%")
            
            # 8. Extraer información del video subido
            video_id = response.get("id")
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            logger.info(f"✅ Video subido exitosamente a YouTube!")
            logger.info(f"🔗 URL: {video_url}")
            logger.info(f"🆔 Video ID: {video_id}")
            
            return {
                "video_id": video_id,
                "video_url": video_url,
                "title": response["snippet"]["title"],
                "description": response["snippet"]["description"],
                "privacy_status": response["status"]["privacyStatus"],
                "published_at": response.get("snippet", {}).get("publishedAt"),
                "thumbnail_url": response.get("snippet", {}).get("thumbnails", {}).get("default", {}).get("url"),
            }
            
        except Exception as e:
            logger.error(f"❌ Error al subir video a YouTube: {str(e)}")
            logger.error(f"📄 Error type: {type(e).__name__}")
            
            # Manejo específico de errores de YouTube
            error_message = str(e)
            if "quota" in error_message.lower():
                detail = "Cuota de YouTube API excedida. Intenta más tarde."
            elif "authentication" in error_message.lower():
                detail = "Error de autenticación con YouTube. Reconecta tu cuenta."
            elif "permission" in error_message.lower():
                detail = "Sin permisos suficientes. Verifica los scopes de YouTube."
            else:
                detail = f"Error al subir video: {error_message}"
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=detail
            )
    
    async def _get_valid_access_token(self, user_id: str) -> str:
        """
        Obtiene un access token válido para YouTube.
        Si está expirado, lo renueva automáticamente.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Access token válido
            
        Raises:
            HTTPException: Si el usuario no tiene tokens conectados
        """
        # Buscar token de YouTube del usuario
        oauth_token = (
            self.db.query(OAuthToken)
            .filter(
                OAuthToken.user_id == user_id,
                OAuthToken.provider == "youtube"
            )
            .first()
        )
        
        if not oauth_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario no tiene cuenta de YouTube conectada. Debe hacer login con Google primero."
            )
        
        # Si el token no está expirado, devolverlo
        if not oauth_token.is_expired():
            return oauth_token.access_token
        
        # Token expirado - renovar con refresh_token
        logger.info(f"🔄 Token expirado, renovando para user_id={user_id}")
        
        if not oauth_token.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay refresh token. Usuario debe reconectar su cuenta de YouTube."
            )
        
        # Renovar token
        new_access_token = await self._refresh_access_token(oauth_token)
        return new_access_token
    
    async def _refresh_access_token(self, oauth_token: OAuthToken) -> str:
        """
        Renueva el access token usando el refresh token.
        
        Args:
            oauth_token: Token OAuth a renovar
            
        Returns:
            Nuevo access token
            
        Raises:
            HTTPException: Si falla la renovación
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.GOOGLE_TOKEN_URL,
                    data={
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "refresh_token": oauth_token.refresh_token,
                        "grant_type": "refresh_token",
                    }
                )
                
                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"❌ Error renovando token: {error_detail}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error al renovar token de YouTube"
                    )
                
                token_data = response.json()
                new_access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                
                # Actualizar token en DB
                oauth_token.access_token = new_access_token
                oauth_token.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                oauth_token.last_refreshed_at = datetime.utcnow()
                self.db.commit()
                
                logger.info(f"✅ Token renovado exitosamente")
                return new_access_token
                
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error renovando token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error de conexión al renovar token"
            )
