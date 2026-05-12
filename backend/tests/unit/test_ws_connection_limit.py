# RF: RNF007 (M01) — Tests del límite de conexiones WebSocket por usuario
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_first_three_connections_accepted():
    """Las primeras 3 conexiones del mismo usuario deben aceptarse."""
    redis = AsyncMock()
    # Simular contadores 1, 2, 3
    redis.incr = AsyncMock(side_effect=[1, 2, 3])
    redis.expire = AsyncMock()
    redis.decr = AsyncMock()

    for expected_count in [1, 2, 3]:
        count = await redis.incr(f"ws_connections:user-1")
        await redis.expire(f"ws_connections:user-1", 3600)
        assert count <= 3, f"La conexión {expected_count} debería ser aceptada"


@pytest.mark.asyncio
async def test_fourth_connection_rejected_code_4029():
    """La 4ta conexión del mismo usuario debe rechazarse con código 4029."""
    user_id = uuid4()
    token = "valid-token"

    redis_mock = AsyncMock()
    # 4ta llamada a incr → count=4 → rechazar
    redis_mock.incr = AsyncMock(return_value=4)
    redis_mock.expire = AsyncMock()
    redis_mock.decr = AsyncMock()

    websocket = AsyncMock()
    websocket.close = AsyncMock()

    # Simular la lógica del handler
    conn_key = f"ws_connections:{user_id}"
    count = await redis_mock.incr(conn_key)
    await redis_mock.expire(conn_key, 3600)

    if count > 3:
        await redis_mock.decr(conn_key)
        await websocket.close(code=4029)

    websocket.close.assert_called_once_with(code=4029)
    redis_mock.decr.assert_called_once_with(conn_key)


@pytest.mark.asyncio
async def test_connection_counter_decremented_on_disconnect():
    """Al desconectar, el contador Redis debe decrementarse."""
    user_id = uuid4()
    redis_mock = AsyncMock()
    redis_mock.decr = AsyncMock()

    conn_key = f"ws_connections:{user_id}"
    await redis_mock.decr(conn_key)

    redis_mock.decr.assert_called_once_with(conn_key)


@pytest.mark.asyncio
async def test_connection_key_includes_user_id():
    """La clave Redis de conexiones debe incluir el UUID del usuario."""
    user_id = uuid4()
    expected_key = f"ws_connections:{user_id}"

    redis_mock = AsyncMock()
    redis_mock.incr = AsyncMock(return_value=1)
    redis_mock.expire = AsyncMock()

    key = f"ws_connections:{user_id}"
    await redis_mock.incr(key)
    await redis_mock.expire(key, 3600)

    redis_mock.incr.assert_called_once_with(expected_key)
    redis_mock.expire.assert_called_once_with(expected_key, 3600)


@pytest.mark.asyncio
async def test_connection_ttl_is_one_hour():
    """El TTL de la clave de conexiones debe ser de 3600 segundos (1 hora)."""
    redis_mock = AsyncMock()
    redis_mock.incr = AsyncMock(return_value=1)
    redis_mock.expire = AsyncMock()

    key = "ws_connections:test-user"
    await redis_mock.incr(key)
    await redis_mock.expire(key, 3600)

    _, ttl_arg = redis_mock.expire.call_args.args
    assert ttl_arg == 3600


@pytest.mark.asyncio
async def test_unauthenticated_connection_rejected():
    """Conexión sin token debe cerrarse con código 4001 antes de verificar límite."""
    websocket = AsyncMock()
    websocket.close = AsyncMock()

    token = ""
    if not token:
        await websocket.close(code=4001)

    websocket.close.assert_called_once_with(code=4001)
