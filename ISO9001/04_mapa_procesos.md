# ISO 9001:2015 — Cláusula 8
## Mapa de Procesos del Sistema Linku

**Sistema:** Linku — Sistema de Intermediación Laboral DRTPE-Junín
**Revisión:** 1.0 | Fecha: 2026-06-23

---

## Visión General

El sistema Linku automatiza el ciclo completo de intermediación laboral a través de **20 procesos interconectados**, agrupados en cuatro macro-procesos:

```
[USUARIO] ──► [REGISTRO/AUTH] ──► [ONBOARDING] ──► [PERFIL] ──► [MATCHING] ──► [COLOCACIÓN]
                                                        │               │
                                               [NLP/EMBEDDINGS]  [EQUIDAD/EXPLICABILIDAD]
                                                                        │
                                              [EMPLEADOR] ──► [OFERTAS] ──► [POSTULACIONES]
                                                                        │
                                              [ADMIN DRTPE] ──► [KPIs] ──► [REPORTES]
```

---

## Macro-Proceso 1: Gestión de Identidad y Acceso

```
Entrada: datos de registro (email, contraseña, rol)
  │
  ▼
P-001: Registro y Autenticación
  │   JWT RS256 / bcrypt / blacklist Redis
  │
  ▼
P-002: Onboarding y Clasificación de Tipo
  │   Algoritmo: is_first_job + is_trade_worker → worker_type
  │
  └──► primer_empleo → P-003
  └──► oficio        → P-004
  └──► experiencia   → P-005
```

**Procesos:** P-001, P-002
**Seguridad transversal:** P-018 (en todas las operaciones)

---

## Macro-Proceso 2: Construcción de Perfil y Representación Vectorial

```
P-003 (Primer Empleo) ──► Wizard 6 pasos ──┐
P-004 (Oficio)         ──► Portafolio    ──┤──► P-006 (NLP Extracción de Skills)
P-005 (Experiencia)    ──► Parseo CV     ──┘           │
                                                        ▼
                                               P-007 (Embeddings pgvector 384-dim)
                                                        │
                                                        ▼
                                               Perfil vectorial en BD
                                                        │
                                                        ▼
                                               P-009 (Generación CV PDF)
```

**Procesos:** P-003, P-004, P-005, P-006, P-007, P-009

---

## Macro-Proceso 3: Emparejamiento y Colocación Laboral

```
Empleador ──► P-010 (Gestión de Ofertas) ──► Oferta + embedding
                      │
                      ▼
              P-011 (Alertas Empleo) ──► notifica trabajadores con alertas
                      │
                      ▼
[Trabajador + Oferta] ──► P-008 (Motor Matching)
                              │  combined_score = α·coseno + β·ml + γ·reputación
                              │
                              ▼
                         P-014 (Equidad Algorítmica)
                              │  disparate_impact ≥ 0.80
                              │
                              ▼
                         Ranking de ofertas (top-K)
                              │
                              ▼
                    Trabajador postula ──► P-012 (Notificaciones WS)
```

**Procesos:** P-008, P-010, P-011, P-012, P-014

---

## Macro-Proceso 4: Marketplace de Servicios de Oficio

```
Trabajador OFICIO ──► P-015 (Marketplace) ──► Listing público
                              │
                              ▼
                    Usuario reporta ──► P-016 (Moderación)
                              │             │
                              │         Moderador revisa
                              │             │
                              ▼             ▼
                    P-015 Contrato ──► P-019 (Encuesta económica)
```

**Procesos:** P-015, P-016, P-019

---

## Macro-Proceso 5: Administración DRTPE y Trazabilidad

```
Datos de BD (workers, contracts, applications, search_logs)
              │
              ▼
P-013 (Panel Admin DRTPE) ──► P-020 (Reportes Investigación)
              │
              ▼
         KPIs calculados:
         VIL · IVP · TF · RBS · TCC · IVM · TCSS
              │
              ▼
P-017 (Integración DRTPE) ──► Sincronización Bolsa de Trabajo
```

**Procesos:** P-013, P-017, P-019, P-020

---

## Relaciones entre Procesos (Entradas y Salidas)

| Proceso Origen | Salida | Proceso Destino | Entrada |
|---------------|--------|-----------------|---------|
| P-001 | `access_token` + registro `workers/employers` | P-002 | token para onboarding |
| P-002 | `worker_type` determinado + perfil base | P-003/P-004/P-005 | tipo para flujo específico |
| P-003 | `wizard_progress.extracted_skills` | P-006 | texto coloquial por paso |
| P-004 | `portfolio_entries` con descripción | P-006 | descripción del trabajo |
| P-005 | CV subido (PDF/DOCX) | P-006 | texto extraído del CV |
| P-006 | Lista de skills estandarizadas | P-007 | texto de perfil normalizado |
| P-007 | `embedding Vector(384)` en BD | P-008 | vector del trabajador |
| P-010 | `job_offers` con embedding | P-007 | descripción de oferta |
| P-008 | `combined_score` por oferta | P-014 | scores por grupo |
| P-014 | ranking re-ordenado | P-012 | notificación de nuevos matches |
| P-008 | top-K matches | P-011 | verificación contra alertas activas |
| P-009 | PDF bytes | P-012 | notificación `cv_ready` |
| P-015 | `contract` creado | P-019 | encuesta económica post-contrato |
| P-019 | `monthly_income` cifrado | P-013 | cálculo KPI RBS |
| P-013 | KPIs calculados | P-020 | dataset de investigación |

---

## Infraestructura de Soporte (Cláusula 7 — Recursos)

| Componente | Versión | Función en los Procesos |
|-----------|---------|------------------------|
| FastAPI | 0.115 | Motor de todos los endpoints REST/WebSocket |
| PostgreSQL + pgvector | 15 + pgvector | Almacenamiento de perfiles y embeddings Vector(384) |
| Redis | 7 | Broker Celery, caché, blacklist JWT, rate limiting, pub/sub WS |
| Celery | 5.4 | Procesamiento asíncrono de embeddings, CV, notificaciones |
| sentence-transformers | 3.3 | Modelo `paraphrase-multilingual-MiniLM-L12-v2` (384 dims) |
| spaCy | 3.8 | NER para extracción de entidades en CV y wizard |
| WeasyPrint | ≥62.3 | Renderizado de PDF desde plantillas HTML/Jinja2 |
| Docker Compose | — | 4 workers Celery + Beat + Flower + Prometheus + Grafana |
| SonarQube | LTS Community | Análisis estático de calidad y seguridad |
| pytest | 8.2 | Suite de pruebas: 266 tests, cobertura ≥80% |

---

*Linku — DRTPE-Junín · ISO 9001:2015 Cláusula 8 — Mapa de Procesos · Huancayo 2026*
