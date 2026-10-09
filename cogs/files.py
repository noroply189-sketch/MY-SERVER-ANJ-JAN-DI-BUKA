from __future__ import annotations

import os
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from services.file_generator import (
    write_csv_file,
    write_docx_file,
    write_json_file,
    write_pdf_file,
    write_pptx_file,
    write_text_file,
    write_xlsx_file,
)
from services.file_reader import read_document, summarize_document


class FilesCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="read-file")
    @app_commands.describe(file_path="Path to the file to read")
    async def read_file(self, interaction: discord.Interaction, file_path: str) -> None:
        await interaction.response.defer(thinking=True)
        try:
            content = read_document(file_path)
            await interaction.followup.send(content[:2000])
        except Exception as exc:
            await interaction.followup.send(f"Failed to read file: {exc}")

    @app_commands.command(name="summarize")
    @app_commands.describe(file_path="Path to the file to summarize")
    async def summarize(self, interaction: discord.Interaction, file_path: str) -> None:
        await interaction.response.defer(thinking=True)
        try:
            summary = summarize_document(file_path)
            await interaction.followup.send(summary[:2000])
        except Exception as exc:
            await interaction.followup.send(f"Summary failed: {exc}")

    @app_commands.command(name="make-pdf")
    @app_commands.describe(title="Document title", content="Document text")
    async def make_pdf(self, interaction: discord.Interaction, title: str, content: str) -> None:
        await interaction.response.defer(thinking=True)
        output = write_pdf_file(f"{title.replace(' ', '_')}.pdf", f"{title}\n\n{content}")
        await interaction.followup.send(file=discord.File(str(output)))

    @app_commands.command(name="make-docx")
    @app_commands.describe(title="Document title", content="Document text")
    async def make_docx(self, interaction: discord.Interaction, title: str, content: str) -> None:
        await interaction.response.defer(thinking=True)
        output = write_docx_file(f"{title.replace(' ', '_')}.docx", [title, content])
        await interaction.followup.send(file=discord.File(str(output)))

    @app_commands.command(name="make-excel")
    @app_commands.describe(title="File name", rows="Rows as CSV-like content")
    async def make_excel(self, interaction: discord.Interaction, title: str, rows: str) -> None:
        await interaction.response.defer(thinking=True)
        parsed = [line.split("|") for line in rows.split("\n") if line.strip()]
        output = write_xlsx_file(f"{title.replace(' ', '_')}.xlsx", parsed)
        await interaction.followup.send(file=discord.File(str(output)))

    @app_commands.command(name="make-pptx")
    @app_commands.describe(title="Presentation title", content="Slide body")
    async def make_pptx(self, interaction: discord.Interaction, title: str, content: str) -> None:
        await interaction.response.defer(thinking=True)
        output = write_pptx_file(f"{title.replace(' ', '_')}.pptx", [title, content])
        await interaction.followup.send(file=discord.File(str(output)))

    @app_commands.command(name="make-code")
    @app_commands.describe(filename="Filename", code="Source code")
    async def make_code(self, interaction: discord.Interaction, filename: str, code: str) -> None:
        await interaction.response.defer(thinking=True)
        output = write_text_file(filename, code)
        await interaction.followup.send(file=discord.File(str(output)))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FilesCog(bot))
