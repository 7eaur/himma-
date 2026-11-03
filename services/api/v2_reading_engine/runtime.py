"""Native speech loop hosted by the existing Himma FastAPI process.

Enabled only for the final V2-only release and a configured PostgreSQL/Azure
resource. There is no separate service, scheduler, Redis, Vercel or lab runtime.
Parallel API replicas coordinate via PostgreSQL SKIP LOCKED and job leases.
"""
from __future__ import annotations

import asyncio
import logging
import os
import secrets

import httpx

from .azure_provider import AzureSpeechConfig, AzureSpeechProvider
from .worker import run_one


log = logging.getLogger("himma.v2_reading")


def native_runtime_configuration() -> AzureSpeechConfig | None:
    enabled = os.getenv("HIMMA_V2_NATIVE_READING_ENABLED", "0").strip()
    if enabled not in {"0", "1"}:
        raise ValueError("HIMMA_V2_NATIVE_READING_ENABLED must be 0 or 1")
    if enabled == "0":
        return None
    url = os.getenv("DATABASE_URL", "")
    if not url.startswith(("postgresql:", "postgresql+")):
        raise ValueError("Native V2 reading requires the existing PostgreSQL database")
    return AzureSpeechConfig.from_environment()


async def run_native_reading_forever(config: AzureSpeechConfig) -> None:
    """Bounded sequential worker; cancellation gracefully frees the API task."""
    from db.database import SessionLocal

    worker_id = "himma-native-" + secrets.token_hex(12)
    async with httpx.AsyncClient() as http:
        provider = AzureSpeechProvider(config, http)
        while True:
            try:
                result = await run_one(
                    SessionLocal, provider, worker_id=worker_id,
                    finalize_academic=True,
                )
                if result == "academic_deferred":
                    log.warning("Native reading grade deferred; preserved for retry")
                    delay = 10.0
                else:
                    delay = 1.5 if result != "idle" else 4.0
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("Native reading worker cycle failed; academic result unchanged")
                delay = 10.0
            await asyncio.sleep(delay)
