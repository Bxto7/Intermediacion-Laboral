"""
Script de usuarios demo — Sistema de Intermediación Laboral DRTPE-Junín
Crea un usuario por cada tipo de trabajador + admin + empleador.

Uso:
    docker exec intermediacion_api python scripts/create_demo_users.py

Credenciales creadas:
    admin@demo.pe          / Demo2026!  (rol ADMIN)
    empleador@demo.pe      / Demo2026!  (rol EMPLOYER)
    primer.empleo@demo.pe  / Demo2026!  (PRIMER_EMPLEO — wizard en paso 3)
    experiencia@demo.pe    / Demo2026!  (EXPERIENCIA — perfil completo)
    oficio@demo.pe         / Demo2026!  (OFICIO — portfolio + listing activo)
"""
import asyncio
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import encrypt_field, hash_password
from app.models.employer import Employer
from app.models.job_offer import JobOffer
from app.models.portfolio import PortfolioEntry
from app.models.service_listing import ServiceListing
from app.models.user import User
from app.models.wizard import WizardProgress
from app.models.worker import Worker

PASSWORD = "Demo2026!"
HASHED = hash_password(PASSWORD)


async def create_demo(session: AsyncSession) -> None:
    print("Creando usuarios demo...")

    # ── ADMIN ────────────────────────────────────────────────────────────────
    admin = User(
        email="admin@demo.pe",
        hashed_password=HASHED,
        role="admin",
        is_active=True,
        email_verified=True,
    )
    session.add(admin)
    await session.flush()
    print(f"  admin:      {admin.email}")

    # ── EMPLOYER ─────────────────────────────────────────────────────────────
    emp_user = User(
        email="empleador@demo.pe",
        hashed_password=HASHED,
        role="employer",
        is_active=True,
        email_verified=True,
    )
    session.add(emp_user)
    await session.flush()

    employer = Employer(
        user_id=emp_user.id,
        company_name="Constructora Junín SAC",
        ruc=encrypt_field("20601234567"),
        contact_name=encrypt_field("María Torres Quispe"),
        phone=encrypt_field("+51987654321"),
        district="Huancayo",
        sector="Construcción",
        is_verified=True,
    )
    session.add(employer)
    await session.flush()
    print(f"  empleador:  {emp_user.email}")

    # Ofertas de trabajo para que el matching tenga contra qué comparar
    job_offers = [
        JobOffer(
            employer_id=employer.id,
            title="Asistente Administrativo — Sin Experiencia",
            description=(
                "Buscamos joven para primer empleo en área administrativa. "
                "Brindaremos capacitación completa. Buen ambiente laboral. "
                "Habilidades: responsabilidad, puntualidad, trabajo en equipo."
            ),
            required_skills=["responsabilidad", "puntualidad", "comunicación"],
            preferred_skills=["computación básica", "Excel básico"],
            district="Huancayo",
            modality="presencial",
            salary_min=Decimal("930.00"),
            salary_max=Decimal("1200.00"),
            worker_type_target="primer_empleo",
            is_active=True,
        ),
        JobOffer(
            employer_id=employer.id,
            title="Contador Junior — 2 años experiencia",
            description=(
                "Se solicita contador con experiencia mínima de 2 años en "
                "contabilidad de empresas constructoras. Manejo de SIIGO y PDT. "
                "Trabajo presencial en El Tambo."
            ),
            required_skills=["contabilidad", "SIIGO", "PDT", "declaración tributaria"],
            preferred_skills=["SUNAT", "CONCAR", "planillas"],
            district="El Tambo",
            modality="presencial",
            salary_min=Decimal("1800.00"),
            salary_max=Decimal("2500.00"),
            worker_type_target="experiencia",
            is_active=True,
        ),
        JobOffer(
            employer_id=employer.id,
            title="Electricista Residencial — Proyecto 3 meses",
            description=(
                "Necesitamos electricista para proyecto de habilitación eléctrica "
                "de conjunto residencial en Chilca. Tableros, cableado, tomacorrientes. "
                "Conocimiento de norma EM.010. Ofrecemos S/. 80 por día."
            ),
            required_skills=["instalación eléctrica", "tableros eléctricos", "cableado"],
            preferred_skills=["norma EM.010", "multímetro", "trabajo en altura"],
            district="Chilca",
            modality="presencial",
            salary_min=Decimal("1600.00"),
            salary_max=Decimal("2000.00"),
            worker_type_target="oficio",
            is_active=True,
        ),
        JobOffer(
            employer_id=employer.id,
            title="Gasfitero — Mantenimiento de planta",
            description=(
                "Buscamos gasfitero / plomero con experiencia en sistemas "
                "de agua fría y caliente para mantenimiento de planta industrial "
                "en Huancayo. Disponibilidad inmediata."
            ),
            required_skills=["gasfitería", "tuberías", "instalación sanitaria"],
            preferred_skills=["soldadura de cobre", "sistemas de presión"],
            district="Huancayo",
            modality="presencial",
            salary_min=Decimal("1400.00"),
            salary_max=Decimal("1800.00"),
            worker_type_target="oficio",
            is_active=True,
        ),
    ]
    for offer in job_offers:
        session.add(offer)
    await session.flush()
    print(f"  ofertas:    {len(job_offers)} creadas")

    # ── PRIMER_EMPLEO ─────────────────────────────────────────────────────────
    pe_user = User(
        email="primer.empleo@demo.pe",
        hashed_password=HASHED,
        role="worker",
        is_active=True,
        email_verified=True,
    )
    session.add(pe_user)
    await session.flush()

    pe_worker = Worker(
        user_id=pe_user.id,
        worker_type="primer_empleo",
        full_name=encrypt_field("Lucía Quispe Mamani"),
        dni=encrypt_field("71234567"),
        phone=encrypt_field("+51912345678"),
        district="Huancayo",
        years_experience=0,
        is_available=True,
        profile_completeness=45,
        education_level="secundaria_completa",
        username="lucia.quispe",
    )
    session.add(pe_worker)
    await session.flush()

    # Wizard en paso 3 (habilidades blandas) con respuestas parciales
    wizard = WizardProgress(
        worker_id=pe_worker.id,
        current_step=3,
        answers={
            "paso1": {
                "district": "Huancayo",
                "birth_year": 2005,
                "has_photo": False,
            },
            "paso2": {
                "education_level": "secundaria_completa",
                "institution": "I.E. Santa Isabel",
                "graduation_year": 2023,
            },
            "paso3_raw": (
                "Soy muy puntual, nunca llego tarde. "
                "Me gusta trabajar en equipo y aprendo rápido. "
                "Ayudo a mi mamá en su negocio de comida."
            ),
        },
        extracted_skills=["puntualidad", "trabajo en equipo", "aprendizaje rápido", "atención al cliente"],
        job_interests=["administración", "ventas", "atención al cliente"],
    )
    session.add(wizard)
    print(f"  primer_emp: {pe_user.email}  (wizard paso 3/6)")

    # ── EXPERIENCIA ───────────────────────────────────────────────────────────
    exp_user = User(
        email="experiencia@demo.pe",
        hashed_password=HASHED,
        role="worker",
        is_active=True,
        email_verified=True,
    )
    session.add(exp_user)
    await session.flush()

    exp_worker = Worker(
        user_id=exp_user.id,
        worker_type="experiencia",
        full_name=encrypt_field("Carlos Rojas Ávila"),
        dni=encrypt_field("43876543"),
        phone=encrypt_field("+51987654320"),
        district="El Tambo",
        years_experience=5,
        avg_rating=Decimal("4.30"),
        is_available=True,
        profile_completeness=85,
        job_title="Contador Público Colegiado",
        bio=(
            "Contador público con 5 años de experiencia en empresas del sector "
            "construcción y comercio en la región Junín. Especialista en declaraciones "
            "tributarias, planillas y análisis financiero. Manejo avanzado de SIIGO, "
            "CONCAR y PDT. Dispuesto a trabajo remoto o presencial en Huancayo y El Tambo."
        ),
        education_level="universitaria",
        username="carlos.rojas.conta",
    )
    session.add(exp_worker)
    await session.flush()
    print(f"  experiencia: {exp_user.email}  (perfil completo, 85%)")

    # ── OFICIO ────────────────────────────────────────────────────────────────
    of_user = User(
        email="oficio@demo.pe",
        hashed_password=HASHED,
        role="worker",
        is_active=True,
        email_verified=True,
    )
    session.add(of_user)
    await session.flush()

    of_worker = Worker(
        user_id=of_user.id,
        worker_type="oficio",
        full_name=encrypt_field("Juan Pablo Huamán Cóndor"),
        dni=encrypt_field("41234560"),
        phone=encrypt_field("+51964321098"),
        district="Chilca",
        trade_category="Electricidad",
        years_experience=8,
        avg_rating=Decimal("4.75"),
        is_available=True,
        profile_completeness=90,
        bio=(
            "Electricista con 8 años de experiencia en instalaciones residenciales "
            "e industriales en toda la provincia de Huancayo. Certificado por SENATI. "
            "Trabajo garantizado."
        ),
        username="juan.huaman.elec",
    )
    session.add(of_worker)
    await session.flush()

    # Entradas del portfolio
    portfolio_entries = [
        PortfolioEntry(
            worker_id=of_worker.id,
            title="Instalación eléctrica completa — Casa 2 pisos en El Tambo",
            description=(
                "Instalé el cableado completo de una casa de 2 pisos en El Tambo. "
                "Puse el tablero de 12 polos, todos los tomacorrientes, puntos de luz "
                "y sistema de tierra. Duró 4 días, quedó todo en regla."
            ),
            extracted_skills=[
                "instalación eléctrica residencial",
                "tableros eléctricos",
                "cableado estructurado",
                "tomacorrientes",
                "sistema de puesta a tierra",
            ],
            photos=[],
            period_start=date(2024, 8, 1),
            period_end=date(2024, 8, 5),
            client_rating=Decimal("5.0"),
            is_public=True,
        ),
        PortfolioEntry(
            worker_id=of_worker.id,
            title="Cambio de tablero eléctrico — Local comercial Huancayo",
            description=(
                "Cambié el tablero viejo de 6 polos por uno nuevo de 20 polos "
                "trifásico en un local comercial del centro de Huancayo. "
                "Incluye breakers termo magnéticos y diferencial. Trabajo en 1 día."
            ),
            extracted_skills=[
                "tableros trifásicos",
                "breakers termo magnéticos",
                "diferencial",
                "instalación eléctrica comercial",
            ],
            photos=[],
            period_start=date(2024, 11, 15),
            period_end=date(2024, 11, 15),
            client_rating=Decimal("4.8"),
            is_public=True,
        ),
        PortfolioEntry(
            worker_id=of_worker.id,
            title="Instalación de paneles solares — Vivienda rural en Chilca",
            description=(
                "Instalé 4 paneles solares de 300W con inversor de 1.5kW y batería "
                "de respaldo para una vivienda en las afueras de Chilca. "
                "Sistema funciona perfectamente hace 6 meses."
            ),
            extracted_skills=[
                "paneles solares",
                "energía fotovoltaica",
                "inversores",
                "sistemas de batería",
                "instalación rural",
            ],
            photos=[],
            period_start=date(2024, 6, 10),
            period_end=date(2024, 6, 12),
            client_rating=Decimal("5.0"),
            is_public=True,
        ),
    ]
    for entry in portfolio_entries:
        session.add(entry)
    await session.flush()

    # Listing en el marketplace
    listing = ServiceListing(
        worker_id=of_worker.id,
        trade_category="Electricidad",
        title="Instalación eléctrica residencial e industrial — Huancayo",
        description=(
            "Electricista certificado por SENATI con 8 años de experiencia. "
            "Realizo instalaciones completas, tableros eléctricos, tomacorrientes, "
            "iluminación LED y sistemas de tierra. Atiendo Huancayo, El Tambo y Chilca. "
            "Garantía de 1 año en trabajos realizados. Contactar para presupuesto gratuito."
        ),
        enriched_keywords=[
            "electricista",
            "instalación eléctrica",
            "tablero eléctrico",
            "cableado",
            "tomacorrientes",
            "SENATI",
            "Huancayo",
        ],
        districts=["Huancayo", "El Tambo", "Chilca"],
        price_reference=Decimal("80.00"),
        price_unit="día",
        availability="inmediata",
        is_active=True,
        views_count=47,
    )
    session.add(listing)
    print(f"  oficio:     {of_user.email}  (3 portfolio entries + listing marketplace)")

    await session.commit()

    print("\nDemo completado.")
    print("─" * 50)
    print("CREDENCIALES DE PRUEBA  (contraseña: Demo2026!)")
    print("─" * 50)
    print(f"  Admin:        admin@demo.pe")
    print(f"  Empleador:    empleador@demo.pe")
    print(f"  Primer empleo: primer.empleo@demo.pe  (wizard paso 3/6)")
    print(f"  Experiencia:  experiencia@demo.pe     (perfil 85% completo)")
    print(f"  Oficio:       oficio@demo.pe           (portfolio 3 trabajos)")
    print("─" * 50)


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_local = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_local() as session:
        await create_demo(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
