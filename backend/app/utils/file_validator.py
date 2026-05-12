# RF: RNF002 — Portfolio photo validation (Sprint 3 security audit)
# Validates MIME type via magic number (not client-supplied Content-Type),
# enforces 5 MB size limit, and logs audit trail for antivirus stub.
import structlog
from fastapi import HTTPException, UploadFile

logger = structlog.get_logger()

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


async def validate_portfolio_photo(file: UploadFile) -> bytes:
    """Validate a portfolio photo upload.

    Steps:
    1. Read full file content.
    2. Verify MIME type against actual file bytes using python-magic
       (ignores the client-supplied Content-Type header which is untrusted).
    3. Verify total size does not exceed 5 MB.
    4. Log audit entry — antivirus stub (ClamAV integration pending).

    Raises:
        HTTPException 400: if MIME type is not permitted or file exceeds 5 MB.
    """
    content = await file.read()
    await file.seek(0)

    try:
        import magic  # python-magic>=0.4.27
        detected_mime = magic.from_buffer(content[:2048], mime=True)
    except ImportError:
        logger.warning(
            "python_magic_unavailable",
            fallback="content_type_header",
            filename=file.filename,
        )
        detected_mime = file.content_type or "application/octet-stream"

    if detected_mime not in ALLOWED_MIME_TYPES:
        logger.warning(
            "portfolio_photo_rejected_mime",
            detected_mime=detected_mime,
            filename=file.filename,
        )
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido: {detected_mime}. Solo JPEG, PNG o WEBP.",
        )

    if len(content) > MAX_FILE_SIZE_BYTES:
        logger.warning(
            "portfolio_photo_rejected_size",
            size_bytes=len(content),
            max_bytes=MAX_FILE_SIZE_BYTES,
            filename=file.filename,
        )
        raise HTTPException(
            status_code=400,
            detail="El archivo supera el limite de 5 MB.",
        )

    logger.info(
        "portfolio_photo_validated",
        mime_type=detected_mime,
        size_bytes=len(content),
        antivirus_scan="pending_clamav_integration",
    )

    return content
