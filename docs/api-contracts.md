# API Contracts — Sistema de Intermediación Laboral
# Base URL: /api/v1 | Auth: Bearer JWT RS256

## Convenciones
- Todas las respuestas: `Content-Type: application/json`
- Errores: `{ "detail": "mensaje", "code": "ERROR_CODE" }`
- Fechas: ISO 8601 UTC
- Moneda: Numérico decimal (S/.)
- IDs: UUID v4

---

## M1 — Autenticación

### POST /auth/register/worker
Registra un nuevo trabajador.
```json
// Request
{
  "email": "william@example.com",
  "phone": "+51987654321",
  "password": "Min8chars1!",
  "full_name": "William Rojas",
  "dni": "12345678",
  "office": "electricista",
  "zone": "El Tambo"
}
// Response 201
{
  "id": "uuid",
  "email": "william@example.com",
  "role": "WORKER",
  "message": "Revisa tu correo para verificar tu cuenta"
}
```

### POST /auth/register/employer
```json
// Request
{ "email", "phone", "password", "full_name", "ruc", "employer_type": "PERSON|COMPANY", "zone" }
// Response 201 — mismo esquema que worker con role: "EMPLOYER"
```

### POST /auth/login
```json
// Request
{ "email": "william@example.com", "password": "Min8chars1!" }
// Response 200
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "user": { "id": "uuid", "role": "WORKER", "full_name": "William Rojas" }
}
// Error 401: { "detail": "Credenciales incorrectas", "code": "INVALID_CREDENTIALS" }
```

### POST /auth/refresh
```json
// Request: { "refresh_token": "eyJ..." }
// Response 200: { "access_token": "eyJ...", "expires_in": 86400 }
```

### POST /auth/logout
```json
// Header: Authorization: Bearer {access_token}
// Response 200: { "message": "Sesión cerrada correctamente" }
```

### POST /auth/forgot-password
```json
// Request: { "email": "william@example.com" }
// Response 200: { "message": "OTP enviado al correo (expira en 30 min)" }
```

### POST /auth/reset-password
```json
// Request: { "token": "otp_token", "new_password": "NewPass1!" }
// Response 200: { "message": "Contraseña actualizada" }
```

### POST /auth/verify-phone
```json
// Request: { "phone": "+51987654321", "otp": "123456" }
// Response 200: { "verified": true }
```

---

## M2 — Perfiles de Trabajador

### GET /workers/me
```json
// Response 200
{
  "id": "uuid",
  "full_name": "William Rojas",
  "office": "electricista",
  "secondary_offices": ["gasfitero"],
  "years_experience": 8,
  "bio": "Especialista en instalaciones eléctricas...",
  "zone": "El Tambo",
  "hourly_rate": 35.00,
  "is_available": true,
  "profile_completeness": 85,
  "avg_rating": 4.7,
  "total_contracts": 23,
  "identity_verified": true,
  "embedding_updated_at": "2026-05-01T10:00:00Z"
}
```

### PUT /workers/me
```json
// Request (todos los campos opcionales)
{
  "bio": "Nueva descripción...",
  "hourly_rate": 40.00,
  "is_available": false,
  "zone": "Huancayo"
}
// Response 200: perfil actualizado
// SIDE EFFECT: dispara tarea Celery para regenerar embedding
```

### GET /workers/{worker_id}/profile
Perfil público de un trabajador (visible para empleadores autenticados).
```json
// Response 200
{
  "id": "uuid",
  "full_name": "William R.",     // apellido abreviado si no es público
  "office": "electricista",
  "years_experience": 8,
  "bio": "...",
  "zone": "El Tambo",
  "hourly_rate": 35.00,
  "avg_rating": 4.7,
  "total_contracts": 23,
  "identity_verified": true,
  "badges": ["PRIMER_CONTRATO", "5_ESTRELLAS"],
  "ratings_summary": { "total": 23, "distribution": {"5": 18, "4": 4, "3": 1} }
}
```

### POST /workers/me/certifications
```json
// Request: multipart/form-data
{ "file": <archivo PDF/JPG>, "title": "Certificado electricidad industrial" }
// Response 201: { "id": "uuid", "url": "https://storage.../cert.pdf", "title": "..." }
```

### PATCH /workers/me/availability
```json
// Request
{
  "is_available": true,
  "schedule": {
    "lunes": [{"start": "08:00", "end": "17:00"}],
    "sabado": [{"start": "09:00", "end": "13:00"}]
  }
}
// Response 200: { "is_available": true, "schedule": {...} }
```

### GET /workers/me/stats
```json
// Response 200
{
  "ivp": 34.5,                    // Índice Visibilidad Perfil %
  "searches_appeared": 120,
  "applications_active": 3,
  "contracts_completed": 23,
  "avg_rating": 4.7,
  "total_income_registered": 4500.00,
  "vil_days": 4,                  // Velocidad Inserción Laboral
  "monthly_trend": [...]
}
```

---

## M4 + M5 — Matching y NLP

### POST /match
Endpoint principal del motor de emparejamiento.
```json
// Request (rol: EMPLOYER)
{
  "job_request_id": "uuid",
  "top_k": 10,
  "filters": {
    "max_budget": 150.00,
    "zones": ["El Tambo", "Huancayo"],
    "min_rating": 4.0,
    "verified_only": false
  }
}
// Response 200
{
  "job_request_id": "uuid",
  "candidates": [
    {
      "worker_id": "uuid",
      "full_name": "William R.",
      "office": "electricista",
      "zone": "El Tambo",
      "avg_rating": 4.7,
      "hourly_rate": 35.00,
      "cosine_similarity": 0.8934,
      "ml_score": 0.82,
      "reputation_score": 4.7,
      "combined_score": 0.8612,
      "rank": 1,
      "explanation": [
        "Coincidencia semántica con el perfil requerido",
        "Habilidades específicas coincidentes",
        "Tarifa dentro del presupuesto"
      ]
    }
  ],
  "total_evaluated": 145,
  "algorithm_response_ms": 187,
  "model_version": "v2.1"
}
```

### POST /match/feedback
Feedback explícito sobre una recomendación.
```json
// Request
{
  "recommendation_log_id": "uuid",
  "is_relevant": true
}
// Response 200: { "message": "Feedback registrado" }
```

### GET /workers/me/feed
Feed personalizado de solicitudes activas para el trabajador.
```json
// Query params: ?page=1&limit=20&min_budget=50&zone=El+Tambo
// Response 200
{
  "items": [
    {
      "id": "uuid",
      "title": "Instalación eléctrica residencial",
      "description": "...",
      "zone": "El Tambo",
      "max_budget": 150.00,
      "required_date": "2026-05-10",
      "compatibility_score": 0.89,
      "employer": { "name": "Carlos T.", "avg_rating": 4.5, "is_verified": true }
    }
  ],
  "total": 47,
  "page": 1
}
```

---

## M6 — Publicación de Demanda

### POST /job-requests
```json
// Request (rol: EMPLOYER)
{
  "title": "Instalación eléctrica residencial urgente",
  "description": "Necesito instalar 5 tomacorrientes y 3 interruptores...",
  "office_required": "electricista",
  "zone": "El Tambo",
  "required_date": "2026-05-10",
  "duration_days": 1,
  "max_budget": 150.00
}
// Response 201
{
  "id": "uuid",
  "status": "PUBLISHED",
  "sector": "hogar",             // clasificado automáticamente por NLP
  "created_at": "2026-05-01T...",
  "message": "Solicitud publicada. Recibirás candidatos en breve."
}
// SIDE EFFECT: genera embedding y dispara matching automático
```

### GET /job-requests/{id}
```json
// Response 200: detalle completo de la solicitud + estado
```

### PATCH /job-requests/{id}/status
```json
// Request: { "status": "CANCELLED", "reason": "SERVICE_NO_LONGER_NEEDED" }
// Response 200: { "id": "uuid", "status": "CANCELLED" }
```

### POST /job-requests/{id}/apply
```json
// Request (rol: WORKER)
{
  "message": "Tengo 8 años de experiencia en instalaciones...",
  "proposed_rate": 130.00
}
// Response 201: { "application_id": "uuid", "status": "PENDING" }
```

### POST /job-requests/{id}/select-worker
```json
// Request (rol: EMPLOYER)
{ "worker_id": "uuid", "agreed_rate": 140.00, "rate_type": "PROJECT" }
// Response 201
{
  "contract_id": "uuid",
  "status": "CONFIRMED",
  "message": "Trabajador seleccionado. Se notificó a ambas partes."
}
```

---

## M7 — Reputación y Calificaciones

### POST /contracts/{id}/rate
```json
// Request
{
  "overall_score": 5,
  "quality_score": 5,
  "punctuality_score": 4,
  "communication_score": 5,
  "comment": "Excelente trabajo, muy puntual y profesional."
}
// Response 201: { "rating_id": "uuid", "message": "Calificación registrada" }
// SIDE EFFECT: recalcula reputation_score del trabajador
```

### POST /contracts/{id}/close
```json
// Request (rol: EMPLOYER)
{
  "description_done": "Se instalaron 5 tomacorrientes y 3 interruptores.",
  "final_amount": 140.00,
  "payment_method": "YAPE",
  "payment_confirmed": true
}
// Response 200: { "contract_id": "uuid", "status": "COMPLETED" }
```

---

## M8 — Dashboard y Métricas

### GET /dashboard/worker
```json
// Response 200: stats completos del trabajador (ver RF055)
```

### GET /dashboard/employer
```json
// Response 200: stats completos del empleador (ver RF056)
```

### GET /model/metrics
```json
// Response 200 (rol: ADMIN | RESEARCHER)
{
  "precision": 0.82,
  "recall": 0.79,
  "f1_score": 0.80,
  "auc_roc": 0.88,
  "avg_response_ms": 187,
  "successful_matches_pct": 73.4,
  "disparate_impact": {
    "gender": 0.91,
    "zone": 0.87,
    "education": 0.84
  },
  "model_version": "v2.1",
  "last_trained": "2026-04-28T02:00:00Z"
}
```

### GET /research/dataset
```json
// Response 200 (rol: RESEARCHER) — dataset anonimizado para SPSS
// Query params: ?format=json|csv&period_start=2026-01-01&period_end=2026-12-31
```

---

## M9 — Notificaciones

### GET /notifications
```json
// Query params: ?page=1&limit=20&unread_only=true
// Response 200: { "items": [...], "unread_count": 5 }
```

### PATCH /notifications/{id}/read
```json
// Response 200: { "id": "uuid", "is_read": true }
```

### PUT /notifications/preferences
```json
// Request
{
  "email": { "new_match": true, "contract_confirmed": true },
  "push": { "new_match": true, "new_application": false },
  "in_app": { "all": true }
}
```

---

## Códigos de Error Estándar

| HTTP | Code | Descripción |
|---|---|---|
| 400 | VALIDATION_ERROR | Datos inválidos en el request |
| 401 | UNAUTHORIZED | Token ausente o inválido |
| 403 | FORBIDDEN | Sin permisos para esta acción |
| 404 | NOT_FOUND | Recurso no encontrado |
| 409 | CONFLICT | Recurso ya existe (email duplicado, etc.) |
| 422 | UNPROCESSABLE | Lógica de negocio violada |
| 429 | RATE_LIMITED | Demasiadas peticiones |
| 500 | INTERNAL_ERROR | Error del servidor |

---

## Rate Limits

| Endpoint | Límite |
|---|---|
| POST /auth/login | 5 req/min por IP |
| POST /match | 10 req/min por token |
| POST /job-requests | 20 req/hora por usuario |
| GET * (general) | 60 req/min por token |
