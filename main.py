from __future__ import annotations

import asyncio
import logging
import os
import traceback

import discord
import uvicorn
from discord.ext import commands

from config.settings import get_settings
from database.db import initialize_database
from web.admin import app as admin_app
from workers.monitoring_worker import monitoring_loop

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("discord_ai_agent")


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


async def load_cogs() -> None:
    for module_name in [
        "cogs.chat",
        "cogs.education",
        "cogs.files",
        "cogs.video",
        "cogs.admin",
        "cogs.vps",
    ]:
        try:
            await bot.load_extension(module_name)
            logger.info("Loaded extension: %s", module_name)
        except Exception:
            logger.exception("Failed to load extension: %s", module_name)


@bot.event
async def on_ready() -> None:
    logger.info("Logged in as %s (%s)", bot.user, bot.user.id)
    try:
        await bot.tree.sync(guild=None)
        logger.info("Synced application commands")
    except Exception:
        logger.exception("Failed to sync application commands")


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception) -> None:
    if isinstance(error, commands.CommandNotFound):
        return
    logger.exception("Unhandled command error: %s", error)
    await ctx.reply(f"An error occurred: {error}")


async def main() -> None:
    if not settings.discord_token:
        raise RuntimeError("DISCORD_TOKEN is not configured. Add it to your .env file.")

    await initialize_database()
    await load_cogs()
    admin_app.state.bot = bot
    monitor_task = asyncio.create_task(monitoring_loop(), name="vps-monitor")
    dashboard = uvicorn.Server(uvicorn.Config(
        admin_app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        log_level="info",
        access_log=False,
    ))
    try:
        await asyncio.gather(bot.start(settings.discord_token), dashboard.serve())
    finally:
        monitor_task.cancel()
        await asyncio.gather(monitor_task, return_exceptions=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested.")
    except Exception:
        logger.exception("Bot crashed")
        traceback.print_exc()
