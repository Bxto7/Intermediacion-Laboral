"""
Seed de empleos y empleadores de ejemplo para la región Huancayo.
RF: RF036-RF055 (M03 Empleadores y Ofertas)

Uso:
  docker compose exec api python -m app.utils.seed_jobs
  docker compose exec api python -m app.utils.seed_jobs --clear
"""
# ruff: noqa: T201
import argparse
import asyncio
import sys
from datetime import datetime, timedelta, UTC

import bcrypt
import structlog
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import encrypt_field
from app.models.employer import Employer
from app.models.job_offer import JobOffer
from app.models.user import User

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Datos de empleadores de ejemplo
# ---------------------------------------------------------------------------
EMPLOYERS_DATA = [
    {
        "email": "rrhh@constructoralosandes.pe",
        "company_name": "Constructora Los Andes S.A.C.",
        "ruc": "20487632100",
        "contact_name": "Marco Quispe Rojas",
        "district": "Huancayo",
        "sector": "Construcción",
    },
    {
        "email": "talento@comercialcentro.pe",
        "company_name": "Comercial Centro S.R.L.",
        "ruc": "20512345678",
        "contact_name": "Ana Flores Mendoza",
        "district": "El Tambo",
        "sector": "Comercio",
    },
    {
        "email": "empleo@restaurantesdeljunin.pe",
        "company_name": "Restaurantes del Junín E.I.R.L.",
        "ruc": "20563210987",
        "contact_name": "Luis Huanca Torres",
        "district": "Huancayo",
        "sector": "Gastronomía",
    },
    {
        "email": "personal@textilhuancayo.pe",
        "company_name": "Textil Huancayo S.A.C.",
        "ruc": "20498761234",
        "contact_name": "Carmen Palomino Vega",
        "district": "Chilca",
        "sector": "Manufactura",
    },
]

# ---------------------------------------------------------------------------
# Datos de ofertas laborales
# ---------------------------------------------------------------------------
_future = (datetime.now(UTC) + timedelta(days=60)).isoformat()

JOBS_DATA = [
    # ── PRIMER EMPLEO ──────────────────────────────────────────────────────
    {
        "employer_idx": 1,  # Comercial Centro
        "title": "Asistente de tienda sin experiencia",
        "description": (
            "Buscamos jóvenes con ganas de aprender para atención al cliente en "
            "nuestra tienda de Huancayo. Capacitación interna completa. "
            "Horario flexible compatible con estudios. Buen trato garantizado."
        ),
        "required_skills": ["atención al cliente", "puntualidad", "trabajo en equipo"],
        "preferred_skills": ["manejo de caja", "idioma quechua"],
        "district": "Huancayo",
        "modality": "presencial",
        "salary_min": 1025,
        "salary_max": 1200,
        "worker_type_target": "primer_empleo",
        "expires_at": _future,
    },
    {
        "employer_idx": 2,  # Restaurantes del Junín
        "title": "Ayudante de cocina — primer empleo bienvenido",
        "description": (
            "Restaurante familiar en El Tambo busca ayudante de cocina. "
            "No se requiere experiencia previa, solo disposición para aprender. "
            "Enseñamos desde cero. Ambiente familiar y equipo unido."
        ),
        "required_skills": ["puntualidad", "higiene personal", "trabajo en equipo"],
        "preferred_skills": ["cocina básica", "orden y limpieza"],
        "district": "El Tambo",
        "modality": "presencial",
        "salary_min": 1025,
        "salary_max": 1100,
        "worker_type_target": "primer_empleo",
        "expires_at": _future,
    },
    {
        "employer_idx": 1,  # Comercial Centro
        "title": "Repositor de mercadería — jóvenes recién egresados",
        "description": (
            "Oportunidad ideal para jóvenes que buscan su primer trabajo formal. "
            "Funciones: acomodar productos en góndolas, control de stock básico, "
            "apoyo en inventarios. Contrato con beneficios de ley desde el día 1."
        ),
        "required_skills": ["orden", "responsabilidad", "disponibilidad"],
        "preferred_skills": ["Excel básico"],
        "district": "Chilca",
        "modality": "presencial",
        "salary_min": 1025,
        "salary_max": 1025,
        "worker_type_target": "primer_empleo",
        "expires_at": _future,
    },
    # ── EXPERIENCIA ────────────────────────────────────────────────────────
    {
        "employer_idx": 0,  # Constructora Los Andes
        "title": "Asistente de Ingeniería Civil",
        "description": (
            "Empresa constructora con proyectos en toda la región Junín busca "
            "Asistente de Ingeniería Civil con 1-2 años de experiencia. "
            "Participación en supervisión de obras, elaboración de informes, "
            "control de calidad de materiales y coordinación con proveedores."
        ),
        "required_skills": ["AutoCAD", "S10", "supervisión de obras", "control de calidad"],
        "preferred_skills": ["MS Project", "normas técnicas peruanas", "seguridad en obra"],
        "district": "Huancayo",
        "modality": "presencial",
        "salary_min": 2000,
        "salary_max": 2800,
        "worker_type_target": "experiencia",
        "expires_at": _future,
    },
    {
        "employer_idx": 1,  # Comercial Centro
        "title": "Administrador(a) de tienda — retail",
        "description": (
            "Cadena de tiendas en expansión busca Administrador/a con experiencia "
            "en retail. Gestión de personal, cierres de caja, atención de "
            "reclamaciones, coordinación con almacén central. Línea de carrera real."
        ),
        "required_skills": ["gestión de personal", "control de caja", "Excel intermedio", "liderazgo"],
        "preferred_skills": ["sistema ERP", "visual merchandising"],
        "district": "Huancayo",
        "modality": "presencial",
        "salary_min": 2200,
        "salary_max": 3000,
        "worker_type_target": "experiencia",
        "expires_at": _future,
    },
    {
        "employer_idx": 3,  # Textil Huancayo
        "title": "Jefe de Producción Textil",
        "description": (
            "Empresa textil con 20 años en el mercado busca Jefe de Producción. "
            "Requisito: mínimo 3 años en manufactura textil o confecciones. "
            "Responsable de planificar órdenes de producción, optimizar procesos "
            "y gestionar equipo de 15 operarias."
        ),
        "required_skills": ["gestión de producción", "control de calidad textil", "liderazgo de equipos"],
        "preferred_skills": ["ERP manufactura", "lean manufacturing", "ISO 9001"],
        "district": "Chilca",
        "modality": "presencial",
        "salary_min": 3000,
        "salary_max": 4000,
        "worker_type_target": "experiencia",
        "expires_at": _future,
    },
    {
        "employer_idx": 1,  # Comercial Centro
        "title": "Analista Contable",
        "description": (
            "Buscamos Analista Contable con titulación en Contabilidad y mínimo "
            "2 años de experiencia. Funciones: registro de operaciones, "
            "elaboración de estados financieros, declaraciones tributarias SUNAT, "
            "conciliaciones bancarias y soporte en auditorías."
        ),
        "required_skills": ["contabilidad general", "SUNAT PDT", "Excel avanzado", "PCGE"],
        "preferred_skills": ["CONCAR", "NIIF", "auditoría"],
        "district": "El Tambo",
        "modality": "hibrido",
        "salary_min": 1800,
        "salary_max": 2500,
        "worker_type_target": "experiencia",
        "expires_at": _future,
    },
    {
        "employer_idx": 0,  # Constructora Los Andes
        "title": "Especialista en Seguridad y Salud en el Trabajo",
        "description": (
            "Proyectos de construcción residencial y civil en Junín. Buscamos "
            "profesional SST con registro en MTPE y experiencia en obras. "
            "Elaboración de IPERC, capacitaciones a operarios, inspecciones "
            "diarias y reporte a gerencia."
        ),
        "required_skills": ["IPERC", "norma G050", "SST en construcción", "registro MTPE"],
        "preferred_skills": ["OHSAS 18001", "manejo de crisis", "primeros auxilios"],
        "district": "Huancayo",
        "modality": "presencial",
        "salary_min": 2500,
        "salary_max": 3500,
        "worker_type_target": "experiencia",
        "expires_at": _future,
    },
    {
        "employer_idx": 2,  # Restaurantes del Junín
        "title": "Chef de cocina peruana",
        "description": (
            "Grupo gastronómico con 4 locales en Huancayo busca Chef Principal. "
            "Experiencia mínima 3 años en cocina peruana / regional. "
            "Creación de cartas estacionales, control de costos, gestión de "
            "brigada de cocina y mantenimiento de estándares BPM."
        ),
        "required_skills": ["cocina peruana", "gestión de brigada", "BPM", "costeo de recetas"],
        "preferred_skills": ["cocina regional andina", "pastelería", "HACCP"],
        "district": "Huancayo",
        "modality": "presencial",
        "salary_min": 2800,
        "salary_max": 4000,
        "worker_type_target": "experiencia",
        "expires_at": _future,
    },
    # ── OFICIO ─────────────────────────────────────────────────────────────
    {
        "employer_idx": 0,  # Constructora Los Andes
        "title": "Electricista instalador para obra residencial",
        "description": (
            "Proyecto de 40 viviendas en Huancayo necesita electricistas con "
            "experiencia en instalaciones domiciliarias. Trabajo en cableado "
            "estructurado, tableros, tomacorrientes y puntos de alumbrado. "
            "Contrato por obra con todos los beneficios de ley."
        ),
        "required_skills": ["instalación eléctrica residencial", "tableros eléctricos", "cableado"],
        "preferred_skills": ["lectura de planos eléctricos", "certificación CITE"],
        "district": "Huancayo",
        "modality": "presencial",
        "salary_min": 1500,
        "salary_max": 2200,
        "worker_type_target": "oficio",
        "expires_at": _future,
    },
    {
        "employer_idx": 0,  # Constructora Los Andes
        "title": "Gasfitero para instalaciones sanitarias en obra",
        "description": (
            "Necesitamos gasfiteros / plomeros para trabajos de instalación "
            "sanitaria en proyecto habitacional. Redes de agua fría, agua caliente, "
            "desagüe y aparatos sanitarios. Trabajo estable de 6 meses mínimo."
        ),
        "required_skills": ["instalación sanitaria", "redes de agua", "desagüe"],
        "preferred_skills": ["agua caliente solar", "lectura de planos sanitarios"],
        "district": "El Tambo",
        "modality": "presencial",
        "salary_min": 1400,
        "salary_max": 2000,
        "worker_type_target": "oficio",
        "expires_at": _future,
    },
    {
        "employer_idx": 0,  # Constructora Los Andes
        "title": "Carpintero para acabados de interiores",
        "description": (
            "Carpinteros para fabricación e instalación de puertas, ventanas, "
            "closets y muebles de cocina en proyecto residencial. Se requiere "
            "experiencia comprobable en carpintería de madera y melanina."
        ),
        "required_skills": ["carpintería de madera", "melanina", "instalación de puertas"],
        "preferred_skills": ["tornería", "barnizado", "diseño de muebles"],
        "district": "Huancayo",
        "modality": "presencial",
        "salary_min": 1300,
        "salary_max": 1900,
        "worker_type_target": "oficio",
        "expires_at": _future,
    },
    {
        "employer_idx": 3,  # Textil Huancayo
        "title": "Costurera / Operaria de confección",
        "description": (
            "Fábrica textil en Chilca busca operarias de confección con manejo "
            "de máquina recta, remalladora y recubridora. Producción de prendas "
            "en alpaca y mezclas para exportación. Turno diurno completo."
        ),
        "required_skills": ["máquina recta", "remalladora", "confección de prendas"],
        "preferred_skills": ["recubridora", "tejido a mano", "control de calidad textil"],
        "district": "Chilca",
        "modality": "presencial",
        "salary_min": 1100,
        "salary_max": 1600,
        "worker_type_target": "oficio",
        "expires_at": _future,
    },
    {
        "employer_idx": 1,  # Comercial Centro
        "title": "Técnico en mantenimiento de locales comerciales",
        "description": (
            "Cadena de tiendas busca técnico de mantenimiento polivalente para "
            "sus locales en Huancayo, El Tambo y Chilca. Tareas: electricidad "
            "básica, gasfitería, pintura, pequeñas reparaciones de carpintería "
            "e instalación de señalética."
        ),
        "required_skills": ["electricidad básica", "gasfitería", "pintura", "reparaciones generales"],
        "preferred_skills": ["soldadura", "albañilería básica"],
        "district": "Huancayo",
        "modality": "presencial",
        "salary_min": 1300,
        "salary_max": 1800,
        "worker_type_target": "oficio",
        "expires_at": _future,
    },
    # ── CUALQUIERA ─────────────────────────────────────────────────────────
    {
        "employer_idx": 2,  # Restaurantes del Junín
        "title": "Mozo / Mesero para restaurante",
        "description": (
            "Restaurante de cocina peruana en Huancayo busca mozos con o sin "
            "experiencia. Capacitación en carta y protocolo de servicio incluida. "
            "Propinas y beneficios de ley. Buen ambiente laboral."
        ),
        "required_skills": ["atención al cliente", "trabajo en equipo"],
        "preferred_skills": ["experiencia en servicio", "idioma quechua"],
        "district": "Huancayo",
        "modality": "presencial",
        "salary_min": 1025,
        "salary_max": 1300,
        "worker_type_target": "cualquiera",
        "expires_at": _future,
    },
    {
        "employer_idx": 3,  # Textil Huancayo
        "title": "Almacenero / Auxiliar de logística",
        "description": (
            "Empresa manufacturera en Chilca busca Almacenero para control de "
            "ingresos y salidas de materiales. Se valora experiencia previa, "
            "pero no es indispensable. Manejo de kardex manual y sistema básico."
        ),
        "required_skills": ["orden y limpieza", "responsabilidad", "conteo de inventario"],
        "preferred_skills": ["Excel básico", "sistema WMS", "manejo de montacargas"],
        "district": "Chilca",
        "modality": "presencial",
        "salary_min": 1100,
        "salary_max": 1500,
        "worker_type_target": "cualquiera",
        "expires_at": _future,
    },
    {
        "employer_idx": 1,  # Comercial Centro
        "title": "Promotor(a) de ventas — productos de consumo",
        "description": (
            "Empresa distribuidora busca promotores de ventas para puntos de "
            "venta en los tres distritos. Comisiones atractivas + sueldo base. "
            "Con o sin experiencia en ventas. Se provee uniforme y materiales."
        ),
        "required_skills": ["comunicación efectiva", "proactividad"],
        "preferred_skills": ["experiencia en ventas", "conocimiento de la zona"],
        "district": "El Tambo",
        "modality": "presencial",
        "salary_min": 1025,
        "salary_max": 2000,
        "worker_type_target": "cualquiera",
        "expires_at": _future,
    },
]


# ---------------------------------------------------------------------------
# Lógica de inserción
# ---------------------------------------------------------------------------

async def run_seed(clear: bool = False) -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        if clear:
            await db.execute(delete(JobOffer))
            await db.execute(delete(Employer))
            await db.execute(
                delete(User).where(
                    User.email.in_([e["email"] for e in EMPLOYERS_DATA])
                )
            )
            await db.commit()
            print("[seed_jobs] Datos anteriores eliminados.")

        # Crear usuarios empleadores
        employer_ids: list[str] = []
        for emp_data in EMPLOYERS_DATA:
            existing = await db.execute(select(User).where(User.email == emp_data["email"]))
            user = existing.scalar_one_or_none()
            if not user:
                pw_hash = bcrypt.hashpw(b"SeedPass2026!", bcrypt.gensalt(rounds=12)).decode()
                user = User(
                    email=emp_data["email"],
                    hashed_password=pw_hash,
                    role="employer",
                    is_active=True,
                    email_verified=True,
                )
                db.add(user)
                await db.flush()

            # Crear employer vinculado al user
            emp_existing = await db.execute(
                select(Employer).where(Employer.user_id == user.id)
            )
            employer = emp_existing.scalar_one_or_none()
            if not employer:
                employer = Employer(
                    user_id=user.id,
                    company_name=emp_data["company_name"],
                    ruc=encrypt_field(emp_data["ruc"]),
                    contact_name=encrypt_field(emp_data["contact_name"]),
                    district=emp_data["district"],
                    sector=emp_data["sector"],
                    is_verified=True,
                )
                db.add(employer)
                await db.flush()

            employer_ids.append(employer.id)
            print(f"  empleador: {emp_data['company_name']} — id={employer.id}")

        # Crear ofertas laborales
        for job in JOBS_DATA:
            emp_id = employer_ids[job["employer_idx"]]
            offer = JobOffer(
                employer_id=emp_id,
                title=job["title"],
                description=job["description"],
                required_skills=job["required_skills"],
                preferred_skills=job.get("preferred_skills", []),
                district=job["district"],
                modality=job["modality"],
                salary_min=job.get("salary_min"),
                salary_max=job.get("salary_max"),
                worker_type_target=job["worker_type_target"],
                is_active=True,
                expires_at=datetime.fromisoformat(job["expires_at"]),
            )
            db.add(offer)
            print(f"  oferta: [{job['worker_type_target']:12}] {job['title'][:60]}")

        await db.commit()
        print(f"\n[seed_jobs] ✓ {len(EMPLOYERS_DATA)} empleadores, {len(JOBS_DATA)} ofertas insertadas.")

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed de empleos de ejemplo.")
    parser.add_argument("--clear", action="store_true", help="Eliminar datos existentes antes de insertar.")
    args = parser.parse_args()
    asyncio.run(run_seed(clear=args.clear))
