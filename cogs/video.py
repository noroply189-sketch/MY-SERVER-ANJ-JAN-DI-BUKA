from __future__ import annotations

import os
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from services.video_generator import video_generator


class VideoCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="make-video")
    @app_commands.describe(output_name="Output filename", image_path="Image path to use")
    async def make_video(self, interaction: discord.Interaction, output_name: str, image_path: str) -> None:
        await interaction.response.defer(thinking=True)
        output = Path("storage/output") / output_name
        try:
            result = video_generator.render_video_from_images([image_path], output)
            await interaction.followup.send(file=discord.File(str(result)))
        except Exception as exc:
            await interaction.followup.send(f"Video generation failed: {exc}")

    @app_commands.command(name="make-slideshow")
    @app_commands.describe(output_name="Output filename", image_files="Comma-separated image file paths")
    async def make_slideshow(self, interaction: discord.Interaction, output_name: str, image_files: str) -> None:
        await interaction.response.defer(thinking=True)
        image_list = [part.strip() for part in image_files.split(",") if part.strip()]
        output = Path("storage/output") / output_name
        try:
            result = video_generator.build_slideshow_video(image_list, output)
            await interaction.followup.send(file=discord.File(str(result)))
        except Exception as exc:
            await interaction.followup.send(f"Slideshow generation failed: {exc}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VideoCog(bot))
