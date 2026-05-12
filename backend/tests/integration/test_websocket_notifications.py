# RF: RF126-RF135 (M08) — notificaciones WebSocket
"""Integration tests for WebSocket notifications."""
import json
from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_publish_notification_sends_to_redis():
    """publish_notification debe llamar redis.publish con el canal correcto."""
    from app.api.v1.ws_notifications import publish_notification

    redis = AsyncMock()
    redis.publish = AsyncMock()

    await publish_notification(
        user_id="test-user-123",
        notification_type="new_match",
        title="Nueva coincidencia",
        body="Hay una oferta compatible con tu perfil",
        payload={"job_id": "abc-123"},
        redis=redis,
    )

    redis.publish.assert_called_once()
    call_args = redis.publish.call_args
    channel = call_args[0][0]
    message_str = call_args[0][1]

    assert channel == "notifications:test-user-123"
    message = json.loads(message_str)
    assert message["type"] == "new_match"
    assert message["title"] == "Nueva coincidencia"
    assert message["payload"]["job_id"] == "abc-123"


@pytest.mark.asyncio
async def test_publish_notification_types():
    """Verificar todos los tipos de notificacion validos."""
    from app.api.v1.ws_notifications import publish_notification

    valid_types = ["new_match", "application_update", "alert_job", "message", "cv_ready"]

    for notif_type in valid_types:
        redis = AsyncMock()
        redis.publish = AsyncMock()

        await publish_notification(
            user_id="user-456",
            notification_type=notif_type,
            title="Test",
            body="Test body",
            payload={},
            redis=redis,
        )
        redis.publish.assert_called_once()


@pytest.mark.asyncio
async def test_notification_channel_format():
    """El canal Redis debe tener formato 'notifications:{user_id}'."""
    from app.api.v1.ws_notifications import CHANNEL_PREFIX, publish_notification

    redis = AsyncMock()
    redis.publish = AsyncMock()

    user_id = "550e8400-e29b-41d4-a716-446655440000"
    await publish_notification(
        user_id=user_id,
        notification_type="message",
        title="Hola",
        body="Mensaje de prueba",
        payload={},
        redis=redis,
    )

    expected_channel = f"{CHANNEL_PREFIX}{user_id}"
    actual_channel = redis.publish.call_args[0][0]
    assert actual_channel == expected_channel


@pytest.mark.asyncio
async def test_notification_payload_serialized_as_json():
    """El mensaje publicado debe ser JSON valido."""
    from app.api.v1.ws_notifications import publish_notification

    redis = AsyncMock()
    redis.publish = AsyncMock()

    complex_payload = {
        "job_id": "abc",
        "score": 0.85,
        "worker_type": "oficio",
        "skills": ["electricidad", "cableado"],
    }

    await publish_notification(
        user_id="user-789",
        notification_type="alert_job",
        title="Oferta disponible",
        body="Nueva oferta en Huancayo",
        payload=complex_payload,
        redis=redis,
    )

    message_str = redis.publish.call_args[0][1]
    parsed = json.loads(message_str)
    assert parsed["payload"]["score"] == 0.85
    assert "electricidad" in parsed["payload"]["skills"]
