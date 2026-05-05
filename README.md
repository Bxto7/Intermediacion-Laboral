# Sistema de Intermediación Laboral ML/NLP 🚀
**Dirección Regional de Trabajo y Promoción del Empleo (DRTPE) - Junín | Huancayo, Perú**

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL_15-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![React](https://img.shields.io/badge/React_18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

Plataforma integral desarrollada para reducir las brechas de acceso al empleo formal en la región Junín. Utiliza inteligencia artificial (Machine Learning y Procesamiento de Lenguaje Natural) para optimizar la conexión entre ciudadanos e instituciones empleadoras, reconociendo tres grandes perfiles con barreras laborales distintas.

---

## 🎯 Visión del Producto y Perfiles

El sistema no asume un modelo único de trabajador, sino que clasifica a los usuarios en tres flujos especializados para resolver sus problemas específicos:

### 1. 🌱 Primer Empleo
Orientado a jóvenes sin historial laboral.
- **Problema:** No saben cómo describir sus habilidades ni estructurar un CV.
- **Solución:** Asistente guiado por NLP que convierte experiencias informales (voluntariados, ayuda familiar) en competencias transferibles. Generación de CV automatizada.

### 2. 💼 Experiencia
Orientado a trabajadores con trayectoria.
- **Problema:** Perfil disperso o puramente físico, difícil de visibilizar.
- **Solución:** Creación rápida de perfil, parsing de CV (PDF/DOCX) mediante NLP, y motor de emparejamiento (matching) con ofertas formales.

### 3. 🛠️ Oficio
Orientado a trabajadores con competencias prácticas (electricistas, gasfiteros, etc.).
- **Problema:** Competencias no certificadas e invisibilidad digital.
- **Solución:** Portfolio visual de trabajos realizados (donde el NLP extrae habilidades técnicas desde descripciones coloquiales) y un **Marketplace de Servicios** institucional.

---

## ⚙️ Stack Tecnológico

### Backend
- **Framework:** FastAPI (Python 3.11)
- **Base de Datos:** PostgreSQL 15 + `pgvector` (búsqueda semántica)
- **ORM:** SQLAlchemy 2.x + Alembic (Migraciones)
- **Procesamiento en background:** Celery + Redis
- **IA/ML:** `sentence-transformers` (Embeddings), spaCy (NER), scikit-learn (Matching y Re-ranking equitativo).

### Frontend
- **Framework:** React 18 + Vite
- **Estilos:** Tailwind CSS
- **Estado y Formularios:** react-hook-form + zod
- **Gráficos:** Recharts

### Infraestructura
- **Contenedores:** Docker y Docker Compose
- **Despliegue planeado:** GCP Cloud Run / AWS ECS

---

## 🏗️ Arquitectura del Sistema

La arquitectura está dividida por módulos siguiendo los requerimientos funcionales de la DRTPE-Junín:
- `backend/app/api`: Routers agrupados por dominio.
- `backend/app/services`: Lógica de negocio (onboarding, cv builder, job board).
- `backend/app/nlp`: Extracción de skills, parsing de CVs y embeddings vectoriales.
- `backend/app/ml`: Motores de recomendación (cold-start, matching engine, explicabilidad).
- `frontend/src/modules`: Aplicaciones React separadas por el tipo de flujo.

---

## 🚀 Instalación y Despliegue Local

Este proyecto está contenerizado para facilitar su desarrollo. Para iniciarlo localmente:

### Requisitos
- [Docker](https://www.docker.com/products/docker-desktop)
- [Docker Compose](https://docs.docker.com/compose/)

### Pasos

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/Bxto7/Intermediacion-Laboral.git
   cd Intermediacion-Laboral
   ```

2. **Configurar variables de entorno**
   Copia el archivo de ejemplo para configurar tus credenciales (el archivo real `.env` está ignorado en Git):
   ```bash
   cp .env.example .env
   ```

3. **Levantar los servicios con Docker**
   ```bash
   docker-compose up --build
   ```

4. **Acceso a los servicios**
   - **Frontend:** http://localhost:5173
   - **Backend API Docs (Swagger):** http://localhost:8000/docs
   - **PGAdmin (Base de datos):** http://localhost:5050

---

## 👥 Equipo de Investigación e Implementación
- **Investigadores:** Rojas Peña, William Mikeiel | Tovar Sanchez, Carlos Alberto
- **Institución socia:** Dirección Regional de Trabajo y Promoción del Empleo (DRTPE) - Junín.

> *Proyecto enmarcado bajo metodología Scrum (Sprints de 2 semanas) y parte de una investigación aplicada cuantitativa.*
