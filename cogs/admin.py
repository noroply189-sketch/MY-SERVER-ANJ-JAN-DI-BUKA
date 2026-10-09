from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from config.settings import get_settings

settings = get_settings()


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="admin-status")
    async def admin_status(self, interaction: discord.Interaction) -> None:
        if interaction.user.id not in settings.admin_ids:
            await interaction.response.send_message("You are not authorized to use admin commands.", ephemeral=True)
            return
        await interaction.response.send_message("Admin controls are active.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
