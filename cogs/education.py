from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from services.ai_router import AIRequest, router


class EducationCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="solve")
    @app_commands.describe(problem="Solve a math or science problem")
    async def solve(self, interaction: discord.Interaction, problem: str) -> None:
        await interaction.response.defer(thinking=True)
        response = await router.route(AIRequest(
            prompt=f"Solve this problem carefully with steps, formulas, substitutions, and final result: {problem}",
            system_prompt="You are a helpful educational tutor for math, physics, chemistry, biology, and other school subjects. Include units where relevant.",
        ))
        await interaction.followup.send(response[:2000])

    @app_commands.command(name="translate")
    @app_commands.describe(text="Translate a text", target="Target language")
    async def translate(self, interaction: discord.Interaction, text: str, target: str = "English") -> None:
        await interaction.response.defer(thinking=True)
        response = await router.route(AIRequest(
            prompt=f"Translate the following text to {target}: {text}",
            system_prompt="You translate text accurately and preserve meaning.",
        ))
        await interaction.followup.send(response[:2000])

    @app_commands.command(name="quiz")
    @app_commands.describe(topic="Generate a quiz topic")
    async def quiz(self, interaction: discord.Interaction, topic: str) -> None:
        await interaction.response.defer(thinking=True)
        response = await router.route(AIRequest(
            prompt=f"Create a short quiz about {topic} with 5 questions, answer options, and an answer key.",
            system_prompt="You create educational quizzes.",
        ))
        await interaction.followup.send(response[:2000])

    @app_commands.command(name="homework")
    @app_commands.describe(task="Get homework help")
    async def homework(self, interaction: discord.Interaction, task: str) -> None:
        await interaction.response.defer(thinking=True)
        response = await router.route(AIRequest(
            prompt=f"Help with this school task step by step: {task}",
            system_prompt="You are a patient education tutor and explain concepts simply.",
        ))
        await interaction.followup.send(response[:2000])


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EducationCog(bot))
