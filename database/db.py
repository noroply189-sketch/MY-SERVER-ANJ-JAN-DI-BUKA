from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import aiosqlite

from config.settings import get_settings

settings = get_settings()


async def get_connection() -> aiosqlite.Connection:
    db_path = settings.database_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return await aiosqlite.connect(db_path)


async def initialize_database() -> None:
    db = await get_connection()
    try:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                preferences TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                provider TEXT,
                model TEXT,
                kind TEXT,
                tokens INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS vps_hosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                host TEXT NOT NULL,
                user TEXT,
                ssh_key_path TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS monitoring_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vps_host_id INTEGER,
                cpu_percent REAL,
                ram_percent REAL,
                disk_percent REAL,
                latency_ms REAL,
                status TEXT,
                recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                alert TEXT
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vps_host_id INTEGER,
                metric TEXT,
                threshold REAL,
                observed REAL,
                message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.commit()
    finally:
        await db.close()
