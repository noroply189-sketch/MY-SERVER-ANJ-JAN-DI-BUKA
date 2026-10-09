from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from services.web_search import quick_search


class SearchCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="search")
    @app_commands.describe(query="Search the web")
    async def search(self, interaction: discord.Interaction, query: str) -> None:
        await interaction.response.defer(thinking=True)
        try:
            results = await quick_search(query)
            lines = [f"{item['title']} — {item['url']}\n{item['snippet']}" for item in results[:5]]
            await interaction.followup.send("\n\n".join(lines)[:4000])
        except Exception as exc:
            await interaction.followup.send(f"Search failed: {exc}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SearchCog(bot))
