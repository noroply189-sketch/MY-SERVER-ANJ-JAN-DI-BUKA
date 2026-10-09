from __future__ import annotations

import importlib

MODULES = [
    "config.settings",
    "database.db",
    "providers.openrouter",
    "providers.groq",
    "providers.gemini",
    "services.ai_router",
    "services.web_search",
    "services.vision",
    "services.file_reader",
    "services.file_generator",
    "services.video_generator",
    "services.session_manager",
    "services.vps_monitor",
    "workers.task_queue",
    "workers.monitoring_worker",
    "utils.security",
    "utils.validators",
    "utils.logger",
]


def test_imports() -> None:
    for name in MODULES:
        module = importlib.import_module(name)
        assert module is not None
