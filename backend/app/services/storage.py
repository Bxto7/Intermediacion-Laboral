# RF: RNF009, RNF010 — Almacenamiento GCS con URLs firmadas (máx 60 min)
# Fotos de portfolio y CVs generados nunca se almacenan en BD ni en base64.
from __future__ import annotations

import mimetypes
import uuid
from datetime import timedelta
from pathlib import Path

import structlog

logger = structlog.get_logger()

ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_PHOTO_BYTES = 5 * 1024 * 1024  # 5 MB
SIGNED_URL_TTL = timedelta(minutes=60)


def _get_bucket():
    """Retorna el bucket GCS configurado. Lazy import para no romper tests sin credenciales."""
    from google.cloud import storage as gcs
    from app.core.config import settings
    client = gcs.Client()
    return client.bucket(settings.GCS_BUCKET_NAME)


def upload_file(
    file_content: bytes,
    destination_path: str,
    content_type: str,
) -> str:
    """Sube un archivo a GCS y retorna el nombre del blob (no la URL pública)."""
    bucket = _get_bucket()
    blob = bucket.blob(destination_path)
    blob.upload_from_string(file_content, content_type=content_type)
    logger.info("gcs_upload", path=destination_path, size=len(file_content))
    return destination_path


def generate_signed_url(blob_name: str, expiration: timedelta = SIGNED_URL_TTL) -> str:
    """Genera una URL firmada válida por `expiration` (default 60 min)."""
    bucket = _get_bucket()
    blob = bucket.blob(blob_name)
    url = blob.generate_signed_url(expiration=expiration, method="GET", version="v4")
    return url


def delete_file(blob_name: str) -> None:
    """Elimina un archivo de GCS."""
    bucket = _get_bucket()
    blob = bucket.blob(blob_name)
    blob.delete()
    logger.info("gcs_delete", path=blob_name)


def upload_portfolio_photo(
    file_content: bytes,
    worker_id: str,
    original_filename: str,
) -> str:
    """Valida MIME y tamaño, luego sube foto de portfolio. Retorna blob_name."""
    if len(file_content) > MAX_PHOTO_BYTES:
        raise ValueError(f"Foto excede el límite de {MAX_PHOTO_BYTES // 1024 // 1024} MB.")

    suffix = Path(original_filename).suffix.lower()
    mime = mimetypes.types_map.get(suffix, "application/octet-stream")
    if mime not in ALLOWED_PHOTO_TYPES:
        raise ValueError(f"Tipo de archivo no permitido: {mime}. Solo JPEG, PNG o WEBP.")

    blob_name = f"portfolio/{worker_id}/{uuid.uuid4()}{suffix}"
    return upload_file(file_content, blob_name, content_type=mime)


def upload_generated_cv(file_content: bytes, worker_id: str) -> str:
    """Sube un CV generado en PDF. Retorna blob_name."""
    blob_name = f"cvs/{worker_id}/{uuid.uuid4()}.pdf"
    return upload_file(file_content, blob_name, content_type="application/pdf")
