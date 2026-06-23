# P-012 — Notificaciones en Tiempo Real (WebSocket)
## Proceso Automatizado | ISO 9001:2015 — Cláusula 8.4

**Sistema:** Linku — DRTPE-Junín
**Módulo:** M08 — Notificaciones
**RF Cubiertos:** RF126–RF135
**Sprint de implementación:** Sprint 3
**Componentes clave:**
- `backend/app/api/v1/ws_notifications.py`
- `backend/app/models/notification.py`

---

## 1. Propósito

Entregar notificaciones en tiempo real a los usuarios del sistema mediante WebSocket autenticado con Redis pub/sub como broker, eliminando la necesidad de polling y mejorando la experiencia de usuario en flujos críticos (nuevo match, actualización de postulación, CV listo).

---

## 2. Arquitectura WebSocket + Redis Pub/Sub

```
[Proceso que genera evento]           [Usuario conectado]
  (matching, CV, alerta, etc.)              │
              │                              │
              ▼                              ▼
  publish_notification(user_id, ...) ──► Canal Redis pub/sub
  redis.publish("notifications:{user_id}", payload)
                                             │
                                             ▼
                                   [ws_notifications.py]
                                   Subscriptor escucha el canal
                                             │
                                             ▼
                                   WebSocket.send_json(payload)
                                             │
                                             ▼
                                   [Cliente Frontend]
                                   NotificationBell actualizada
```

---

## 3. Tipos de Notificación Soportados

| Tipo | Descripción | Trigger |
|------|-------------|---------|
| `new_match` | Hay nuevas ofertas compatibles con el perfil | Motor de matching (P-008) |
| `application_update` | El estado de una postulación cambió (ej. "En revisión") | Empleador actualiza status |
| `alert_job` | Una nueva oferta coincide con una alerta configurada | P-011 al crear oferta |
| `message` | Mensaje del empleador al trabajador | Sistema de mensajería |
| `cv_ready` | El CV PDF fue generado exitosamente | Tarea Celery `generate_cv_task` |

---

## 4. Flujo del Proceso

### 4.1 Establecimiento de Conexión
```
[Cliente] GET /ws/notifications/{user_id}?token=<access_token>
    │
    ├─► verify_token(token) → payload del JWT
    ├─► Verificar user_id == payload.sub (403 si no coincide)
    │
    ├─► _check_ws_connection_limit(user_id, redis):
    │       ├─► INCR "ws_connections:{user_id}" en Redis (TTL 3600s)
    │       └─► [Si count > 3] DECR + close(code=4029) "Too Many Connections"
    │
    ├─► websocket.accept()
    ├─► Subscribir a canal Redis "notifications:{user_id}"
    │
    └─► [Loop]: esperar mensajes del canal pub/sub
            │
            ├─► [Mensaje recibido] → websocket.send_json(payload)
            └─► [Cliente desconectado] → _release_ws_connection(user_id, redis) (DECR)
```

### 4.2 Publicación de Notificación (desde cualquier proceso)
```python
await publish_notification(
    user_id=user_id,
    notification_type="new_match",
    title="Nuevas ofertas compatibles",
    body="Encontramos 3 ofertas que coinciden con tu perfil",
    payload={"match_count": 3},
    redis=redis
)
# Internamente: redis.publish(f"notifications:{user_id}", json.dumps(payload))
```

---

## 5. Control de Conexiones Simultáneas

| Límite | Valor | Mecanismo |
|--------|-------|-----------|
| Conexiones por usuario | Máximo 3 | Redis INCR/DECR con clave `ws_connections:{user_id}` |
| Código al rechazar | 4029 | "Too Many WebSocket Connections" |
| TTL de la clave | 3600 segundos | Por si la conexión no se decrementa correctamente |

---

## 6. Modelo de Datos — `notifications`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | Identificador |
| `user_id` | UUID (FK users) | Destinatario |
| `notification_type` | VARCHAR(30) | new_match / application_update / alert_job / message / cv_ready |
| `title` | VARCHAR(200) | Título corto |
| `body` | TEXT | Mensaje descriptivo |
| `payload` | JSONB | Datos adicionales (match_count, job_id, etc.) |
| `is_read` | BOOLEAN | Estado de lectura |

---

## 7. Controles de Calidad

| Control | Descripción |
|---------|-------------|
| Autenticación obligatoria | Token JWT en query param; `verify_token` antes de `accept()` |
| Código de cierre 4001 | Token inválido → cierre inmediato sin `accept()` |
| Límite de conexiones | Previene abuso y consumo excesivo de recursos |
| Cierre graceful | `finally: _release_ws_connection` garantiza el DECR en Redis |
| Redis pub/sub como broker | Desacopla el emisor del receptor; soporta múltiples instancias de la app |

---

## 8. Indicadores de Desempeño

| Indicador | Objetivo | Fuente |
|-----------|---------|--------|
| Latencia de entrega de notificación | < 1 segundo desde el evento | Redis pub/sub es sub-milisecond |
| Conexiones WebSocket activas | Monitorear picos | Redis `ws_connections:*` |
| Notificaciones no leídas acumuladas | Alerta si > 50 por usuario | `notifications WHERE is_read=False` |

---

## 9. Pruebas Automatizadas

Archivo: `backend/tests/integration/test_websocket_notifications.py`
- `test_publish_notification_reaches_subscriber`
- `test_redis_channel_isolated_per_user`
- `test_ws_connection_limit_rejects_4th` → código 4029
- `test_invalid_token_closes_with_4001`

---

*P-012 | Linku DRTPE-Junín · Implementado Sprint 3–4 · RF126–RF135*
