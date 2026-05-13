"""Crea usuario admin DRTPE-Junín para pruebas. Ejecutar una sola vez."""
import asyncio
import sys
sys.path.insert(0, "/app")

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@drtpe-junin.gob.pe"))
        if result.scalar_one_or_none():
            print("Admin ya existe")
            return
        admin = User(
            email="admin@drtpe-junin.gob.pe",
            hashed_password=hash_password("Admin2026!"),
            role="admin",
            is_active=True,
            email_verified=True,
        )
        db.add(admin)
        await db.commit()
        print("Admin creado: admin@drtpe-junin.gob.pe / Admin2026!")

asyncio.run(main())
