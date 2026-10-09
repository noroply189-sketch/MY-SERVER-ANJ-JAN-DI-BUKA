from __future__ import annotations

import asyncio
import contextlib
import logging

from config.settings import get_settings
from services.vps_monitor import collect_vps_snapshot, record_snapshot

logger = logging.getLogger("vps_worker")
settings = get_settings()


async def monitoring_loop(interval_seconds: int | None = None) -> None:
    interval = interval_seconds or settings.vps_monitor_interval_seconds
    while True:
        try:
            snapshot = collect_vps_snapshot()
            await record_snapshot(snapshot)
            logger.info("Recorded VPS snapshot: %s", snapshot.get("status"))
        except Exception as exc:
            logger.exception("Monitoring loop encountered an error: %s", exc)
        await asyncio.sleep(interval)


__all__ = ["monitoring_loop"]
