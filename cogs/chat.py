from __future__ import annotations

import asyncio
import logging
import discord
from discord import app_commands
from discord.ext import commands

from config.settings import get_settings
from services.ai_router import AIRequest, router
from services.session_manager import session_manager

settings = get_settings()
logger = logging.getLogger(__name__)


class ChatCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if message.guild is not None and (self.bot.user is None or self.bot.user not in message.mentions):
            return

        prompt = message.content
        if self.bot.user is not None:
            prompt = prompt.replace(self.bot.user.mention, "").strip()
        if not prompt:
            return

        try:
            async with message.channel.typing():
                response = await router.route(
                    AIRequest(prompt=prompt, system_prompt="You are a helpful assistant.")
                )
            chunks = [response[index:index + 1900] for index in range(0, len(response), 1900)]
            for chunk in chunks:
                await message.reply(chunk, mention_author=False)
        except Exception:
            logger.exception("Direct-message AI request failed")
            await message.reply("AI sedang tidak tersedia. Coba lagi sebentar.", mention_author=False)

    @app_commands.command(name="ask")
    @app_commands.describe(question="Ask the AI a question")
    async def ask(self, interaction: discord.Interaction, question: str) -> None:
        await interaction.response.defer(thinking=True)
        try:
            response = await router.route(AIRequest(prompt=question, system_prompt="You are a helpful assistant."))
            await interaction.followup.send(response[:2000])
        except Exception as exc:
            await interaction.followup.send(f"AI request failed: {exc}")

    @app_commands.command(name="search")
    @app_commands.describe(query="Search the web for current information")
    async def search(self, interaction: discord.Interaction, query: str) -> None:
        await interaction.response.defer(thinking=True)
        try:
            from services.web_search import quick_search

            results = await quick_search(query)
            lines = [f"{item['title']} — {item['url']}\n{item['snippet']}" for item in results[:5]]
            await interaction.followup.send("\n\n".join(lines)[:4000])
        except Exception as exc:
            await interaction.followup.send(f"Search failed: {exc}")

    @app_commands.command(name="explain")
    @app_commands.describe(topic="Explain a topic step by step")
    async def explain(self, interaction: discord.Interaction, topic: str) -> None:
        await interaction.response.defer(thinking=True)
        response = await router.route(AIRequest(prompt=f"Explain this topic clearly with examples and step-by-step guidance: {topic}", system_prompt="You are a teacher."))
        await interaction.followup.send(response[:2000])

    @app_commands.command(name="status")
    async def status(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"Bot online. Guilds: {len(self.bot.guilds)}")

    @app_commands.command(name="reset")
    async def reset(self, interaction: discord.Interaction) -> None:
        await session_manager.get_session(interaction.user.id)
        session_manager._sessions.pop(interaction.user.id, None)
        await interaction.response.send_message("Your session history has been reset.")

    @app_commands.command(name="help")
    async def help_cmd(self, interaction: discord.Interaction) -> None:
        help_text = "Available commands: /ask, /search, /explain, /solve, /vision, /read-file, /summarize, /translate, /quiz, /homework, /model, /provider, /status, /reset, /help, /settings, /make-pdf, /make-docx, /make-excel, /make-pptx, /make-video, /make-slideshow, /make-code, /ping, /vps-history, /vps-stats, /vps-alert-config, /vps-alert-test, /vps-alert-history."
        await interaction.response.send_message(help_text)

    @app_commands.command(name="settings")
    async def settings_cmd(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "Current settings: primary provider is "
            f"{settings.ai_primary_provider}, fallback order: {', '.join(settings.ai_fallback_order) or 'none'}."
        )

    @app_commands.command(name="provider")
    @app_commands.describe(provider="Set primary provider")
    async def provider(self, interaction: discord.Interaction, provider: str) -> None:
        allowed = {"openrouter", "groq", "gemini"}
        if provider.lower() not in allowed:
            await interaction.response.send_message("Provider must be one of: openrouter, groq, gemini.")
            return
        settings.ai_primary_provider = provider.lower()
        await interaction.response.send_message(f"Primary provider set to {provider.lower()}.")

    @app_commands.command(name="model")
    @app_commands.describe(model="Set model name for the current primary provider")
    async def model(self, interaction: discord.Interaction, model: str) -> None:
        await interaction.response.send_message(f"Model request recorded: {model}. Configure provider-specific values in your environment file.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ChatCog(bot))
