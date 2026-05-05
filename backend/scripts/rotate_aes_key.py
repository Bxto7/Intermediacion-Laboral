"""AES key rotation script — RNF001, RNF002.

Generates a new AES-256 key, re-encrypts all BYTEA fields in workers and employers,
logs the result to audit_logs, and prints the new key in base64 for .env update.
"""

import asyncio
import base64
import os
import sys
from pathlib import Path

import structlog

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.database import engine
from app.models.audit_log import AuditLog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = structlog.get_logger()


def _encrypt_with_key(value: str, key: bytes) -> bytes:
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, value.encode("utf-8"), None)
    return nonce + ciphertext


def _decrypt_with_key(value: bytes, key: bytes) -> str:
    aesgcm = AESGCM(key)
    nonce = value[:12]
    ciphertext = value[12:]
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


async def rotate_keys() -> None:
    old_key = base64.b64decode(settings.AES_KEY)
    new_raw = os.urandom(32)
    new_key_b64 = base64.b64encode(new_raw).decode("ascii")

    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as db:
        async with db.begin():
            workers_result = await db.execute(
                text("SELECT id, full_name, dni, phone FROM workers")
            )
            workers = workers_result.fetchall()

            employers_result = await db.execute(
                text("SELECT id, ruc, contact_name, phone FROM employers")
            )
            employers = employers_result.fetchall()

            migrated_workers = 0
            for row in workers:
                wid = row[0]
                updates: dict = {}
                for col_idx, col_name in [(1, "full_name"), (2, "dni"), (3, "phone")]:
                    raw = row[col_idx]
                    if raw is not None:
                        plaintext = _decrypt_with_key(bytes(raw), old_key)
                        updates[col_name] = _encrypt_with_key(plaintext, new_raw)

                if updates:
                    set_clauses = ", ".join(f"{k} = :{k}" for k in updates)
                    await db.execute(
                        text(f"UPDATE workers SET {set_clauses} WHERE id = :id"),
                        {"id": wid, **{k: v for k, v in updates.items()}},
                    )
                    migrated_workers += 1

            migrated_employers = 0
            for row in employers:
                eid = row[0]
                updates = {}
                for col_idx, col_name in [(1, "ruc"), (2, "contact_name"), (3, "phone")]:
                    raw = row[col_idx]
                    if raw is not None:
                        plaintext = _decrypt_with_key(bytes(raw), old_key)
                        updates[col_name] = _encrypt_with_key(plaintext, new_raw)

                if updates:
                    set_clauses = ", ".join(f"{k} = :{k}" for k in updates)
                    await db.execute(
                        text(f"UPDATE employers SET {set_clauses} WHERE id = :id"),
                        {"id": eid, **{k: v for k, v in updates.items()}},
                    )
                    migrated_employers += 1

            audit = AuditLog(
                user_id=None,
                action="aes_key_rotated",
                details={
                    "workers_migrated": migrated_workers,
                    "employers_migrated": migrated_employers,
                },
            )
            db.add(audit)

    logger.info(
        "aes_key_rotation_complete",
        workers_migrated=migrated_workers,
        employers_migrated=migrated_employers,
        new_key_b64=new_key_b64,
    )
    logger.info("new_aes_key_for_env", key=new_key_b64)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(rotate_keys())
