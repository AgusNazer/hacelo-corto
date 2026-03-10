import boto3
import os

from uuid import uuid4
from urllib.parse import urlparse

from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.logging import setup_logging
from app.core.config import settings
from app.utils.exceptions import (
    BadRequestException,
    MinIOStorageException
)

# CRÍTICO: Deshabilitar redirects de región S3 para MinIO
os.environ['AWS_S3_US_EAST_1_REGIONAL_ENDPOINT'] = 'regional'

logger = setup_logging()


def _disable_s3_redirect():
    """Monkey-patch para desactivar S3RegionRedirector en boto3"""
    try:
        from botocore import utils
        original_redirector = utils.S3RegionRedirector
        
        class NoOpS3RegionRedirector:
            """Redirector nulo que no hace nada para evitar loops con MinIO"""
            def __init__(self, *args, **kwargs):
                pass
            
            def redirect_from_error(self, *args, **kwargs):
                # No hacer nada, no redirigir
                return None
            
            def get_bucket_region(self, *args, **kwargs):
                return 'us-east-1'
        
        utils.S3RegionRedirector = NoOpS3RegionRedirector
        logger.info("✅ S3RegionRedirector desactivado para MinIO")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo desactivar S3RegionRedirector: {e}")


# Aplicar monkey-patch al importar el módulo
_disable_s3_redirect()

class StorageService:

    def __init__(self):
        # Cliente por defecto
        self.client = self._create_s3_client(
            endpoint=settings.MINIO_ENDPOINT,
            secure=settings.MINIO_SECURE,
        )
        # Cache de clientes por endpoint+secure
        self._clients_cache: dict[tuple[str, bool], boto3.client] = {}


    def _create_s3_client(self, endpoint: str, secure: bool) -> boto3.client:
        raw_endpoint = endpoint.strip().rstrip("/")

        if raw_endpoint.startswith("http://") or raw_endpoint.startswith("https://"):
            parsed = urlparse(raw_endpoint)
            endpoint_url = f"{parsed.scheme}://{parsed.netloc}"
        else:
            clean_endpoint = raw_endpoint.split("/", 1)[0]
            scheme = "https" if secure else "http"
            endpoint_url = f"{scheme}://{clean_endpoint}"

        logger.info(f"🔧 Creando cliente S3 con endpoint: {endpoint_url}")

        # Configuración MinIO-friendly: sin redirects, path-style addressing
        return boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name="us-east-1",
            use_ssl=secure,
            config=Config(
                signature_version="s3v4",
                s3={
                    "addressing_style": "path",
                },
            ),
        )

    def _get_s3_client(self, endpoint: str | None = None, secure: bool | None = None):
        """
            Reutiliza clientes existentes: no creas uno nuevo cada vez.
            Soporta endpoints dinámicos: _get_s3_client sigue pudiendo cambiar endpoint o secure.
            self.client sigue existiendo como cliente “por defecto”, para casos comunes sin parámetros.
        """
        selected_endpoint = endpoint or settings.MINIO_ENDPOINT
        selected_secure = settings.MINIO_SECURE if secure is None else secure

        key = (selected_endpoint, selected_secure)
        if key not in self._clients_cache:
            self._clients_cache[key] = self._create_s3_client(selected_endpoint, selected_secure)

        return self._clients_cache[key]


    def _ensure_bucket_exists(self, s3_client, bucket: str) -> None:
        """
        Verifica que un bucket exista en MinIO y lo crea si no existe.

        Args:
            s3_client: Cliente S3 de boto3
            bucket: Nombre del bucket

        Raises:
            MinIOStorageException: Si falla la verificación o creación
        """
        try:
            # Solo verifica si el bucket existe
            s3_client.head_bucket(Bucket=bucket)
            return
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchBucket"):
            # El bucket no existe, intentar crear
                try:
                    s3_client.create_bucket(Bucket=bucket)
                except ClientError as create_exc:
                    raise MinIOStorageException(
                    f"Error creando bucket '{bucket}'", str(create_exc)
                )
            else:
                # Otro error (permisos, endpoint, etc.)
                raise MinIOStorageException(
                    f"No se pudo verificar el bucket '{bucket}'", str(exc)
                )


    def _extract_bucket_and_key(self, storage_path: str) -> tuple[str, str]:
        if not storage_path.startswith("s3://"):
            logger.error(f"❌ Invalid storage_path format: {storage_path}")
            raise BadRequestException("storage_path debe comenzar con 's3://'")

        cleaned_path = storage_path[5:]  # más eficiente que replace
        parts = cleaned_path.split("/", 1)

        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise BadRequestException("Formato de storage_path inválido")

        return parts[0], parts[1]
        
        
    def exists(self, storage_path: str) -> bool:
        bucket, key = self._extract_bucket_and_key(storage_path)
    
        s3_client = self._get_s3_client()
    
        try:
            s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
    
            if error_code in ("404", "NoSuchKey"):
                return False
    
            raise MinIOStorageException(
                "Error verificando existencia del objeto", str(exc)
            )
    

    def get_video_url(self, storage_path: str, expires_in: int = 3600) -> str:

        bucket, key = self._extract_bucket_and_key(storage_path)

        logger.info(f"💾 Generando URL presignada para bucket '{bucket}', key '{key}' con expiración de {expires_in} segundos")
        
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires_in
        )


    def get_video_public_url(self, storage_path: str, expires_in: int = 3600) -> str:

        bucket, object_key = self._extract_bucket_and_key(storage_path)

        # Generar URL presignada usando endpoint público
        public_endpoint = settings.MINIO_PUBLIC_ENDPOINT or settings.MINIO_ENDPOINT
        public_secure = (
            settings.MINIO_SECURE
            if settings.MINIO_PUBLIC_SECURE is None
            else settings.MINIO_PUBLIC_SECURE
        )

        logger.info(f"💾 Generando URL pública con endpoint {public_endpoint} (secure={public_secure})"
        )

        logger.info(f"MINIO_PUBLIC_ENDPOINT: {settings.MINIO_PUBLIC_ENDPOINT}")

        s3_client = self._get_s3_client(endpoint=public_endpoint, secure=public_secure)
        try:
            url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": object_key},
                ExpiresIn=expires_in,
            )
        except ClientError as exc:
            raise MinIOStorageException("Error generando URL presignada", str(exc))
        return url


    def upload_local_video_to_minio(self, local_path: str, filename: str) -> tuple[str, str, str]:
        """
        Sube un video local a MinIO y devuelve la ruta S3.

        Args:
            local_path: Ruta al archivo local
            filename: Nombre del archivo (ej: ejemplo.mp4)

        Returns:
            storage_path: s3://bucket/object_key,
                bucket: Nombre del bucket donde se subió,
                object_key: Clave del objeto dentro del bucket

        Raises:
            MinIOStorageException: Si falla la subida
        """
        bucket = settings.MINIO_BUCKET_VIDEOS
        object_key = f"processed/{uuid4()}_{filename}"

        s3_client = self._get_s3_client()
        self._ensure_bucket_exists(s3_client, bucket)

        # Detectar ContentType
        if filename.lower().endswith(".mp4"):
            content_type = "video/mp4"
        elif filename.lower().endswith(".srt"):
            content_type = "text/plain"
        else:
            content_type = "application/octet-stream"

        logger.info(f"💾 Subiendo archivo {filename} a MinIO con ContentType {content_type}")

        try:
            with open(local_path, "rb") as f:
                s3_client.upload_fileobj(
                    f, bucket, object_key, ExtraArgs={"ContentType": content_type})
        except ClientError as exc:
            raise MinIOStorageException("Error subiendo archivo a MinIO", str(exc))
        except Exception as exc:
            raise MinIOStorageException("Error inesperado durante subida", str(exc))

        storage_path = f"s3://{bucket}/{object_key}"
        return storage_path, bucket, object_key


    def upload_fileobj_to_minio(self, file_obj, filename: str) -> tuple[str, str, str]:
        """
        Sube un file-like object (ej: UploadFile.file de FastAPI) a MinIO y devuelve la ruta S3.
        Pensado para endpoints HTTP sin escribir archivos en disco.
    
        Args:
            file_obj: Objeto file-like (debe soportar read())
            filename: Nombre del archivo (ej: ejemplo.mp4)
    
        Returns:
            storage_path: s3://bucket/object_key,
            bucket: Nombre del bucket donde se subió,
            object_key: Clave del objeto dentro del bucket
    
        Raises:
            MinIOStorageException: Si falla la subida
        """
        bucket = settings.MINIO_BUCKET_VIDEOS
        object_key = f"processed/{uuid4()}_{filename}"
    
        s3_client = self._get_s3_client()
        self._ensure_bucket_exists(s3_client, bucket)
    
        logger.info(f"💾 Subiendo archivo a MinIO desde file-like object")
    
        try:
            s3_client.upload_fileobj(
                file_obj, bucket, object_key, ExtraArgs={"ContentType": "video/mp4"}
            )
        except ClientError as exc:
            raise MinIOStorageException("Error subiendo archivo a MinIO", str(exc))
        except Exception as exc:
            raise MinIOStorageException("Error inesperado durante subida", str(exc))
    
        storage_path = f"s3://{bucket}/{object_key}"
        return storage_path, bucket, object_key


    def delete_video_from_storage(self, storage_path: str) -> None:
        
        bucket, object_key = self._extract_bucket_and_key(storage_path)

        s3_client = self._get_s3_client()
        try:
            s3_client.delete_object(Bucket=bucket, Key=object_key)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code not in {"NoSuchKey", "404"}:
                raise MinIOStorageException(
                    "Error eliminando archivo de MinIO", str(exc)
                )