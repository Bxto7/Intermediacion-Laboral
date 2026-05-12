# RF: RF126-RF135 (M08) — notificaciones WebSocket + Redis pub/sub
import asyncio
import json
from uuid import UUID

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = structlog.get_logger()
router = APIRouter(tags=["notifications"])

CHANNEL_PREFIX = "notifications:"


@router.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: UUID,
    token: str = "",
):
    """
    WebSocket de notificaciones en tiempo real.
    El cliente envia ?token=... para autenticarse.
    El servidor publica notificaciones via Redis pub/sub.
    """
    from app.core.redis_client import get_redis
    from app.core.security import verify_token

    if not token:
        await websocket.close(code=4001)
        return

    try:
        payload = await verify_token(token)
        token_user_id = payload.get("sub", "")
        if token_user_id != str(user_id):
            await websocket.close(code=4001)
            return
    except Exception:
        await websocket.close(code=4001)
        return

    redis = get_redis()
    conn_key = f"ws_connections:{user_id}"
    conn_count = await redis.incr(conn_key)
    await redis.expire(conn_key, 3600)
    if conn_count > 3:
        await redis.decr(conn_key)
        await websocket.close(code=4029)
        logger.warning("ws_connection_limit_exceeded", user_id=str(user_id), count=conn_count)
        return

    await websocket.accept()
    channel = f"{CHANNEL_PREFIX}{user_id}"
    logger.info("ws_connected", user_id=str(user_id))

    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)

    try:
        async def redis_listener():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode()
                    await websocket.send_text(data)

        async def ws_listener():
            while True:
                try:
                    msg = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                    if msg == "ping":
                        await websocket.send_text("pong")
                except TimeoutError:
                    pass

        await asyncio.gather(redis_listener(), ws_listener())

    except WebSocketDisconnect:
        logger.info("ws_disconnected", user_id=str(user_id))
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
        try:
            await redis.decr(conn_key)
        except Exception:
            pass


async def publish_notification(
    user_id: str | UUID,
    notification_type: str,
    title: str,
    body: str,
    payload: dict,
    redis,
) -> None:
    """
    Publica una notificacion al canal Redis del usuario.
    Tipos validos: 'new_match', 'application_update', 'alert_job', 'message', 'cv_ready'.
    """
    channel = f"{CHANNEL_PREFIX}{user_id}"
    message = json.dumps({
        "type": notification_type,
        "title": title,
        "body": body,
        "payload": payload,
    })
    await redis.publish(channel, message)
    logger.info(
        "notification_published",
        user_id=str(user_id),
        notification_type=notification_type,
    )
