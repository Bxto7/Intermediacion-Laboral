"""
Seed data para el sistema de intermediación laboral — DRTPE-Junín, Huancayo
Genera: 100 trabajadores, 30 empleadores, 50 solicitudes, 20 contratos + calificaciones + encuestas PRE-TEST
Uso: docker exec intermediacion_api python scripts/seed_data.py
"""
import asyncio
import os
import random
import string
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import encrypt_field, hash_password

fake = Faker("es")
random.seed(42)

OFICIOS = [
    ("electricista", 15),
    ("gasfitero", 14),
    ("carpintero", 14),
    ("albañil", 14),
    ("pintor", 14),
    ("soldador", 15),
    ("techero", 14),
]

ZONAS = ["Huancayo", "El Tambo", "Chilca"]

SECTORES = ["hogar", "empresa", "construcción", "industria"]

PAYMENT_METHODS = ["YAPE", "PLIN", "TRANSFER", "CASH"]

BIOS = {
    "electricista": [
        "Especialista en instalaciones eléctricas residenciales e industriales con {years} años de experiencia en la región Junín.",
        "Técnico electricista certificado. Trabajo en instalaciones, mantenimiento y reparaciones en {zone}.",
        "Electricista con experiencia en tableros eléctricos, circuitos monofásicos y trifásicos.",
    ],
    "gasfitero": [
        "Gasfitero experto en instalación y reparación de tuberías, sanitarios y sistemas de agua.",
        "Plomero con {years} años de experiencia. Servicio rápido y garantizado en {zone}.",
        "Especialista en instalaciones de agua y desagüe. Atención de emergencias 24 horas.",
    ],
    "carpintero": [
        "Carpintero artesanal con {years} años elaborando muebles a medida y estructuras de madera.",
        "Maestro carpintero especializado en puertas, ventanas, closets y cocinas de madera.",
        "Trabajo en carpintería fina y estructural. Materiales de primera calidad.",
    ],
    "albañil": [
        "Maestro de obras con {years} años en construcción y remodelación de viviendas.",
        "Constructor con experiencia en edificaciones, tarrajeos, enchapes y acabados en general.",
        "Albañil especializado en construcción de muros, losas y acabados de interiores.",
    ],
    "pintor": [
        "Pintor profesional en acabados interiores y exteriores con {years} años de experiencia.",
        "Especialista en pintura decorativa, empaste y pintura al temple en {zone}.",
        "Pintor con técnicas modernas y tradicionales. Trabajo limpio y de calidad.",
    ],
    "soldador": [
        "Fierrero con {years} años en estructuras metálicas, rejas, portones y escaleras.",
        "Soldador certificado MIG/TIG. Fabricación de estructuras y mantenimiento industrial.",
        "Maestro soldador especializado en acero inoxidable y estructuras a medida.",
    ],
    "techero": [
        "Techero con experiencia en coberturas de calamina, teja y pvc en {zone}.",
        "Especialista en techado, impermeabilización y mantenimiento de techos.",
        "Techista con {years} años de experiencia en construcción y reparación de techos.",
    ],
}


def gen_referral_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def calc_profile_completeness(worker_data: dict) -> int:
    score = 0
    if worker_data.get("full_name"):
        score += 15
    if worker_data.get("bio"):
        score += 20
    if worker_data.get("hourly_rate"):
        score += 15
    if worker_data.get("years_experience"):
        score += 15
    if worker_data.get("zone"):
        score += 10
    if worker_data.get("office"):
        score += 15
    if worker_data.get("availability_schedule"):
        score += 10
    return min(score, 100)


async def seed(session: AsyncSession):
    print("🌱 Iniciando seed data para Sistema de Intermediación Laboral...")

    # ── 1. Crear usuario ADMIN ────────────────────────────────
    from app.models.contract import Contract, Rating
    from app.models.employer import Employer
    from app.models.job import JobRequest
    from app.models.tracking import EconomicSurvey
    from app.models.user import User
    from app.models.worker import Worker

    admin_user = User(
        email="admin@drtpe-junin.gob.pe",
        hashed_password=hash_password("Admin2026!"),
        role="ADMIN",
        is_active=True,
        is_verified=True,
    )
    session.add(admin_user)
    await session.flush()
    print(f"  ✓ Admin: {admin_user.email}")

    # ── 2. Crear 100 trabajadores ─────────────────────────────
    workers = []
    worker_users = []
    idx = 0
    for oficio, count in OFICIOS:
        for _ in range(count):
            zone = random.choice(ZONAS)
            years = random.randint(1, 20)
            bio_template = random.choice(BIOS[oficio])
            bio = bio_template.format(years=years, zone=zone)
            hourly_rate = round(random.uniform(20, 80), 2)

            user = User(
                email=f"trabajador_{oficio}_{idx:03d}@ejemplo.pe",
                hashed_password=hash_password("Trabajador2026!"),
                phone_encrypted=encrypt_field(f"+519{random.randint(10000000, 99999999)}"),
                role="WORKER",
                is_active=True,
                is_verified=random.choice([True, True, False]),
            )
            session.add(user)
            await session.flush()

            worker_data = {
                "full_name": fake.name(),
                "bio": bio,
                "hourly_rate": hourly_rate,
                "years_experience": years,
                "zone": zone,
                "office": oficio,
                "availability_schedule": {
                    "lunes": [{"start": "08:00", "end": "17:00"}],
                    "martes": [{"start": "08:00", "end": "17:00"}],
                    "miercoles": [{"start": "08:00", "end": "17:00"}],
                    "jueves": [{"start": "08:00", "end": "17:00"}],
                    "viernes": [{"start": "08:00", "end": "17:00"}],
                },
            }
            completeness = calc_profile_completeness(worker_data)

            worker = Worker(
                user_id=user.id,
                full_name=worker_data["full_name"],
                dni_encrypted=encrypt_field(f"{random.randint(10000000, 99999999)}"),
                office=oficio,
                secondary_offices=random.sample(
                    [o for o, _ in OFICIOS if o != oficio], k=random.randint(0, 2)
                ),
                years_experience=years,
                bio=bio,
                zone=zone,
                hourly_rate=Decimal(str(hourly_rate)),
                project_rate=Decimal(str(round(hourly_rate * random.uniform(6, 10), 2))),
                is_available=random.choice([True, True, True, False]),
                availability_schedule=worker_data["availability_schedule"],
                profile_completeness=completeness,
                avg_rating=Decimal(str(round(random.uniform(3.5, 5.0), 2))),
                identity_verified=random.choice([True, False]),
                referral_code=gen_referral_code(),
            )
            session.add(worker)
            await session.flush()

            workers.append(worker)
            worker_users.append(user)
            idx += 1

    print(f"  ✓ {len(workers)} trabajadores creados")

    # ── 3. Crear 30 empleadores ───────────────────────────────
    employers = []
    employer_users = []
    for i in range(30):
        zone = random.choice(ZONAS)
        etype = random.choice(["PERSON", "PERSON", "COMPANY"])

        user = User(
            email=f"empleador_{i:03d}@ejemplo.pe",
            hashed_password=hash_password("Empleador2026!"),
            phone_encrypted=encrypt_field(f"+519{random.randint(10000000, 99999999)}"),
            role="EMPLOYER",
            is_active=True,
            is_verified=random.choice([True, True, False]),
        )
        session.add(user)
        await session.flush()

        employer = Employer(
            user_id=user.id,
            full_name=fake.company() if etype == "COMPANY" else fake.name(),
            ruc_encrypted=encrypt_field(f"20{random.randint(100000000, 999999999)}"),
            employer_type=etype,
            sector=random.choice(SECTORES),
            zone=zone,
            avg_budget=Decimal(str(round(random.uniform(100, 2000), 2))),
            is_verified=random.choice([True, False]),
            total_hires=random.randint(0, 10),
            avg_rating=Decimal(str(round(random.uniform(3.5, 5.0), 2))),
        )
        session.add(employer)
        await session.flush()
        employers.append(employer)
        employer_users.append(user)

    print(f"  ✓ {len(employers)} empleadores creados")

    # ── 4. Crear 50 solicitudes de trabajo ────────────────────
    job_titles = {
        "electricista": ["Instalación eléctrica residencial", "Cambio de tablero eléctrico", "Reparación de cortocircuito", "Instalación de tomacorrientes"],
        "gasfitero": ["Instalación de baño completo", "Reparación de fuga de agua", "Instalación de calentador", "Mantenimiento de tuberías"],
        "carpintero": ["Fabricación de closet empotrado", "Instalación de puertas", "Muebles de cocina a medida", "Reparación de techo de madera"],
        "albañil": ["Construcción de muro perimetral", "Remodelación de cocina", "Tarrajeo y pintura de fachada", "Construcción de baño adicional"],
        "pintor": ["Pintura interior de departamento", "Pintura exterior de casa", "Empaste y pintura de sala", "Pintura de fachada comercial"],
        "soldador": ["Fabricación de reja de seguridad", "Portón corredizo de fierro", "Escalera metálica", "Estructura para techo"],
        "techero": ["Instalación de techo de calamina", "Reparación de techo con filtraciones", "Cobertura de almacén", "Impermeabilización de azotea"],
    }

    jobs = []
    for i in range(50):
        employer = random.choice(employers)
        oficio = random.choice([o for o, _ in OFICIOS])
        title = random.choice(job_titles[oficio])
        zone = employer.zone

        job = JobRequest(
            employer_id=employer.id,
            title=title,
            description=f"{title}. Se requiere {oficio} con experiencia mínima de 2 años en la zona de {zone}. Trabajo de calidad garantizada. Traer materiales propios si es posible.",
            office_required=oficio,
            zone=zone,
            required_date=(datetime.now(UTC) + timedelta(days=random.randint(1, 30))).date(),
            duration_days=random.randint(1, 5),
            max_budget=Decimal(str(round(random.uniform(80, 500), 2))),
            status=random.choice(["PUBLISHED", "PUBLISHED", "PUBLISHED", "IN_PROGRESS", "COMPLETED"]),
            sector=employer.sector,
        )
        session.add(job)
        await session.flush()
        jobs.append(job)

    print(f"  ✓ {len(jobs)} solicitudes de trabajo creadas")

    # ── 5. Crear 20 contratos con calificaciones ──────────────
    contracts_created = []
    completed_jobs = [j for j in jobs if j.status in ("IN_PROGRESS", "COMPLETED")]
    selected_jobs = random.sample(completed_jobs, min(20, len(completed_jobs)))

    for job in selected_jobs:
        # Seleccionar un trabajador del mismo oficio y zona (si posible)
        matching_workers = [
            w for w in workers
            if w.office == job.office_required and w.zone == job.zone
        ]
        if not matching_workers:
            matching_workers = [w for w in workers if w.office == job.office_required]
        if not matching_workers:
            matching_workers = workers

        worker = random.choice(matching_workers)
        employer = next(e for e in employers if e.id == job.employer_id)

        start = datetime.now(UTC) - timedelta(days=random.randint(10, 90))
        end = start + timedelta(days=random.randint(1, 5))
        rate = float(worker.hourly_rate or 35)

        contract = Contract(
            job_request_id=job.id,
            worker_id=worker.id,
            employer_id=employer.id,
            status="COMPLETED",
            agreed_rate=Decimal(str(rate)),
            rate_type=random.choice(["HOURLY", "PROJECT", "DAILY"]),
            start_date=start.date(),
            end_date=end.date(),
            final_amount=Decimal(str(round(rate * random.uniform(4, 12), 2))),
            payment_method=random.choice(PAYMENT_METHODS),
            payment_confirmed=True,
            description_done=f"Se completó satisfactoriamente el trabajo de {job.office_required}.",
        )
        session.add(contract)
        await session.flush()
        contracts_created.append((contract, worker, employer))

        # Calificación del empleador al trabajador
        score = round(random.uniform(3.5, 5.0), 1)
        rating = Rating(
            contract_id=contract.id,
            rater_id=employer_users[employers.index(employer)].id,
            rated_id=worker_users[workers.index(worker)].id,
            rater_role="EMPLOYER",
            overall_score=Decimal(str(score)),
            quality_score=Decimal(str(round(random.uniform(3, 5), 1))),
            punctuality_score=Decimal(str(round(random.uniform(3, 5), 1))),
            communication_score=Decimal(str(round(random.uniform(3, 5), 1))),
            comment=random.choice([
                "Excelente trabajo, muy puntual y profesional.",
                "Buen trabajo. Recomendado.",
                "Cumplió con lo acordado. Trabajo de calidad.",
                "Muy buen profesional, volvería a contratar.",
                "Trabajo correcto, llegó a tiempo y en presupuesto.",
            ]),
            sentiment="POSITIVE" if score >= 4.0 else "NEUTRAL",
        )
        session.add(rating)

        # Actualizar avg_rating y total_contracts del trabajador
        worker.total_contracts = (worker.total_contracts or 0) + 1
        worker.avg_rating = Decimal(str(score))

    print(f"  ✓ {len(contracts_created)} contratos y calificaciones creados")

    # ── 6. Encuestas PRE-TEST (una por trabajador) ────────────
    devices = ["smartphone", "tablet", "laptop", "smartphone", "smartphone"]
    connectivity = ["good", "regular", "poor", "regular", "good"]

    for worker in workers:
        income_pre = round(random.uniform(800, 2000), 2)
        formal_6m = random.randint(0, 3)
        informal_6m = random.randint(1, 8)

        survey = EconomicSurvey(
            worker_id=worker.id,
            survey_type="PRE",
            monthly_income_before=Decimal(str(income_pre)),
            formal_contracts_6m=formal_6m,
            informal_contracts_6m=informal_6m,
            digital_barrier_device=random.choice(devices),
            digital_barrier_connectivity=random.choice(connectivity),
            equity_perception=random.randint(2, 4),
            consent_given=True,
        )
        session.add(survey)

    print(f"  ✓ {len(workers)} encuestas PRE-TEST creadas")

    await session.commit()
    print("\n✅ Seed completado exitosamente.")
    print(f"   👷 Trabajadores: {len(workers)}")
    print(f"   🏢 Empleadores:  {len(employers)}")
    print(f"   📋 Solicitudes:  {len(jobs)}")
    print(f"   📄 Contratos:    {len(contracts_created)}")
    print(f"   📊 Encuestas:    {len(workers)}")
    print("\n   Credenciales de prueba:")
    print("   Admin: admin@drtpe-junin.gob.pe / Admin2026!")
    print("   Trabajador: trabajador_electricista_000@ejemplo.pe / Trabajador2026!")
    print("   Empleador: empleador_000@ejemplo.pe / Empleador2026!")


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_local = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_local() as session:
        await seed(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
