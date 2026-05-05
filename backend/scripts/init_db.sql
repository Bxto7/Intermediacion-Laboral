-- Extensiones requeridas por el sistema de intermediación laboral
-- Este script se ejecuta automáticamente al iniciar el contenedor PostgreSQL

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
