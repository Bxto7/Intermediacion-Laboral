# Research Context — Tesis de Investigación
# NO MODIFICAR ESTE ARCHIVO SIN AUTORIZACIÓN DEL EQUIPO INVESTIGADOR

## Título
Implementación de un Sistema de Intermediación Laboral mediante Machine Learning y NLP
para la Reducción de Brechas Económicas Sectoriales en Articulación con la
Dirección Regional de Trabajo y Promoción del Empleo Junín (DRTPE-Junín)

## Investigadores
- Rojas Peña, William Mikeiel
- Tovar Sanchez, Carlos Alberto

## Período: 2026–2027 | Ciudad: Huancayo, Perú

---

## Variables de Investigación

### Variable Independiente (VI)
**Inteligencia Artificial — Machine Learning y NLP**

| Dimensión | Indicadores | Cómo se mide en el sistema |
|---|---|---|
| Filtrado Algorítmico | Precision, Recall, F1-score | `GET /api/v1/model/metrics` |
| Procesamiento NLP | Exactitud extracción NER, Similitud coseno | Módulo evaluación NLP |
| Alineación Semántica | % emparejamientos exitosos, Top-K relevancia | `recommendation_log` |
| Métricas Cuantitativas | Tiempo respuesta (ms), Tasa reducción sesgo | Dashboard métricas |

### Variable Intermedia (VM)
**Plataforma Web de Intermediación Laboral**

| Dimensión | Indicadores | Cómo se mide en el sistema |
|---|---|---|
| Propiedades Plataforma | N° perfiles registrados, Índice SUS | `workers` table, cuestionario SUS |
| Velocidad Reclutamiento | Tasa contrataciones (%), Tiempo reclutamiento (días) | `contracts` table |
| Visibilidad Empleador | Nivel visibilidad perfil, % demanda cubierta | `search_logs` table |
| Exactitud Recuperación | Precisión IR, Calidad de Servicio (QoS) | Stress testing |

### Variable Dependiente (VD)
**Reducción de Brechas Económicas Sectoriales**

| Dimensión | Indicadores | Cómo se mide en el sistema |
|---|---|---|
| Desempeño Económico | Variación ingreso mensual (S/.), N° contratos formalizados | `economic_surveys` |
| Visibilidad Laboral | Índice visibilidad perfil, N° trabajadores mercado formal | `search_logs` |
| Velocidad Inserción | Velocidad inserción laboral (días), Tasa formalización (%) | `contracts` |
| Equidad | Percepción equidad (1-5), Reducción brecha salarial (%) | `economic_surveys` |

---

## Hipótesis

### Hipótesis General
La implementación de un sistema de intermediación laboral basado en Machine Learning y NLP
influye **significativamente** en la reducción de brechas económicas sectoriales de los
trabajadores de oficios del ámbito urbano de Huancayo durante 2026–2027.

### Hipótesis Específicas

**H1 — Filtrado Algorítmico:**
La aplicación de técnicas de filtrado algorítmico mediante ML mejora significativamente
la precisión del emparejamiento entre oferta laboral y demanda del mercado sectorial.
- Indicadores: Precision, Recall, F1-score ≥ 0.75

**H2 — Alineación Semántica NLP:**
La extracción y alineación semántica de competencias laborales mediante NLP influye
significativamente en la reducción de brechas económicas sectoriales.
- Indicadores: Similitud coseno, exactitud NER, % emparejamientos exitosos

**H3 — Visibilidad y Velocidad:**
La visibilidad laboral y la velocidad de reclutamiento generadas por la plataforma
influyen significativamente en la reducción de brechas económicas sectoriales.
- Indicadores: IVP, VIL, tasa formalización

---

## KPIs de Investigación — Fórmulas EXACTAS (no modificar)

```python
# 1. Velocidad de Inserción Laboral (VIL)
# Días entre registro en plataforma y primer contrato confirmado
def VIL(worker_id):
    registro = workers.created_at WHERE id = worker_id
    primer_contrato = MIN(contracts.created_at) WHERE worker_id = worker_id
    return (primer_contrato - registro).days  # None si no tiene contratos

# 2. Índice de Visibilidad del Perfil (IVP)
# % de veces que el perfil apareció en resultados de búsqueda (últimos 30 días)
def IVP(worker_id):
    apariciones = COUNT(*) FROM search_logs WHERE worker_id = worker_id AND appeared_in_results = TRUE AND created_at >= NOW() - INTERVAL '30 days'
    total_consultas = COUNT(DISTINCT job_request_id) FROM search_logs WHERE created_at >= NOW() - INTERVAL '30 days'
    return (apariciones / total_consultas) * 100

# 3. Tasa de Formalización (TF)
# % trabajadores con al menos 1 contrato registrado
def TF():
    con_contrato = COUNT(DISTINCT worker_id) FROM contracts WHERE status = 'COMPLETED'
    total_trabajadores = COUNT(*) FROM workers WHERE is_active = TRUE
    return (con_contrato / total_trabajadores) * 100

# 4. Reducción de Brecha Salarial (RBS)
# Variación porcentual del ingreso mensual promedio pre vs post
def RBS(worker_id):
    ingreso_pre = economic_surveys.monthly_income_before WHERE worker_id = worker_id AND survey_type = 'PRE'
    ingreso_post = economic_surveys.monthly_income_after WHERE worker_id = worker_id AND survey_type = 'POST'
    return ((ingreso_post - ingreso_pre) / ingreso_pre) * 100

# 5. Reputation Score (RS)
# Promedio ponderado: peso x2 para últimas 5 calificaciones
def RS(worker_id):
    todas = ratings WHERE rated_id = worker_id ORDER BY created_at DESC
    ultimas_5 = todas[:5]
    resto = todas[5:]
    suma = SUM(r.overall_score * 2 for r in ultimas_5) + SUM(r.overall_score for r in resto)
    peso_total = len(ultimas_5) * 2 + len(resto)
    return suma / peso_total if peso_total > 0 else 0.0
```

---

## Score Combinado del Motor de Matching (FÓRMULA FIJA)

```python
# NO MODIFICAR SIN VALIDAR IMPACTO EN F1-SCORE
score = α × cosine_similarity + β × ml_classifier_score + γ × (reputation_score / 5.0)

# Valores por defecto (configurables en system_config):
α = 0.50  # matching_alpha
β = 0.30  # matching_beta
γ = 0.20  # matching_gamma
```

---

## Umbrales del Sistema (No bajar sin justificación)

| Parámetro | Valor mínimo | Acción si se viola |
|---|---|---|
| F1-score producción | ≥ 0.75 | No desplegar nuevo modelo |
| F1-score alerta | < 0.70 | Alerta email al equipo |
| Disparate Impact Ratio | ≥ 0.80 | Activar re-ranking equitativo |
| Completitud perfil para matching | ≥ 60% | Excluir del motor |
| Similitud coseno mínima | ≥ 0.30 | No recomendar |
| SUS score objetivo | ≥ 70 pts | Rediseñar UX si no se alcanza |

---

## Diseño de Investigación

- **Enfoque:** Cuantitativo
- **Tipo:** Aplicada
- **Nivel:** Explicativo-causal
- **Diseño:** No experimental, transversal
- **Muestra:** n ≈ 291 trabajadores (95% confianza, 5% error, N=1200)
- **Período evaluación:** Pre-test al registro | Post-test a los 90 días
- **Análisis estadístico:** Prueba t Student (pre/post), Regresión lineal múltiple, Pearson
- **Software estadístico:** IBM SPSS Statistics v.29
- **Software ML:** Python 3.11, scikit-learn, sentence-transformers, spaCy

---

## Cuestionario de Impacto (28 ítems — NO modificar estructura)

Secciones:
1. Datos sociodemográficos (ítems 1-6)
2. Situación económica PRE-implementación (ítems 7-12)
3. Usabilidad SUS (ítems 13-22, escala 1-5)
4. Situación económica POST-implementación (ítems 23-26)
5. Percepción de equidad (ítems 27-28)

Tabla BD: `economic_surveys`
Survey PRE: se aplica al registrarse
Survey POST: se activa automáticamente a los 90 días de uso

---

## Contexto Local — Huancayo, Junín, Perú

- **Informalidad laboral regional:** > 75% de la PEA
- **Área de estudio:** Ámbito urbano de Huancayo (Huancayo, El Tambo, Chilca)
- **Institución articuladora:** DRTPE-Junín
- **Población objetivo:** Trabajadores de oficios manuales (electricistas, gasfiteros,
  carpinteros, albañiles, pintores, soldadores, techeros)
- **Salario mínimo vital 2026:** S/. 1,025.00
- **Moneda:** Sol peruano (S/. | PEN)
