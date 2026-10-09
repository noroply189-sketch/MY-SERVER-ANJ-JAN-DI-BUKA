from __future__ import annotations

import asyncio
import sqlite3
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config.settings import get_settings
from database.db import get_connection
from services.vps_monitor import collect_vps_snapshot

settings = get_settings()


class VPSView(discord.ui.View):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(timeout=120)
        self.bot = bot

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.primary)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        snapshot = collect_vps_snapshot()
        embed = self._build_embed(snapshot)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="CPU", style=discord.ButtonStyle.secondary)
    async def cpu(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        snapshot = collect_vps_snapshot()
        await interaction.response.send_message(f"CPU usage: {snapshot.get('cpu_usage')}%, model: {snapshot.get('cpu_model')}", ephemeral=True)

    @discord.ui.button(label="RAM", style=discord.ButtonStyle.secondary)
    async def ram(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        snapshot = collect_vps_snapshot()
        await interaction.response.send_message(f"RAM: {snapshot.get('ram_used_gb')} / {snapshot.get('ram_total_gb')} GB ({snapshot.get('ram_percent')}%)", ephemeral=True)

    @discord.ui.button(label="Disk", style=discord.ButtonStyle.secondary)
    async def disk(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        snapshot = collect_vps_snapshot()
        await interaction.response.send_message(f"Disk: {snapshot.get('disk_used_gb')} / {snapshot.get('disk_total_gb')} GB ({snapshot.get('disk_percent')}%)", ephemeral=True)

    @discord.ui.button(label="Network", style=discord.ButtonStyle.secondary)
    async def network(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        snapshot = collect_vps_snapshot()
        await interaction.response.send_message(f"Network: {snapshot.get('network_method')} / {snapshot.get('vps_latency_ms')} ms", ephemeral=True)

    @discord.ui.button(label="OS Info", style=discord.ButtonStyle.secondary)
    async def os_info(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        snapshot = collect_vps_snapshot()
        await interaction.response.send_message(f"OS: {snapshot.get('os_name')} {snapshot.get('os_version')} | Kernel: {snapshot.get('kernel')} | Arch: {snapshot.get('architecture')}", ephemeral=True)

    def _build_embed(self, snapshot: dict) -> discord.Embed:
        embed = discord.Embed(title="VPS SYSTEM MONITOR", color=discord.Color.green())
        embed.add_field(name="Status", value=str(snapshot.get("status", "ONLINE")), inline=True)
        embed.add_field(name="Bot Latency", value=f"{snapshot.get('bot_latency_ms', 'N/A')} ms", inline=True)
        embed.add_field(name="VPS Latency", value=f"{snapshot.get('vps_latency_ms', 'N/A')} ms", inline=True)
        embed.add_field(name="CPU", value=f"{snapshot.get('cpu_model', 'Unknown')} | {snapshot.get('cpu_usage', 'N/A')}%", inline=True)
        embed.add_field(name="RAM", value=f"{snapshot.get('ram_used_gb', 'N/A')} / {snapshot.get('ram_total_gb', 'N/A')} GB", inline=True)
        embed.add_field(name="Disk", value=f"{snapshot.get('disk_used_gb', 'N/A')} / {snapshot.get('disk_total_gb', 'N/A')} GB", inline=True)
        embed.add_field(name="OS", value=f"{snapshot.get('os_name', 'Unknown')} {snapshot.get('os_version', '')}", inline=True)
        embed.add_field(name="Kernel", value=str(snapshot.get('kernel', 'Unknown')), inline=True)
        embed.add_field(name="Architecture", value=str(snapshot.get('architecture', 'Unknown')), inline=True)
        embed.set_footer(text=f"Last checked: {snapshot.get('last_checked', 'Unknown')}")
        return embed


class VpsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping")
    async def ping(self, interaction: discord.Interaction) -> None:
        snapshot = collect_vps_snapshot(bot_latency_ms=round(self.bot.latency * 1000, 2) if self.bot.latency else None)
        await interaction.response.send_message(embed=VPSView(self.bot)._build_embed(snapshot), view=VPSView(self.bot))

    @app_commands.command(name="vps-history")
    async def vps_history(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        conn = await get_connection()
        try:
            cursor = await conn.execute("SELECT recorded_at, cpu_percent, ram_percent, disk_percent, latency_ms, status FROM monitoring_history ORDER BY id DESC LIMIT 10")
            rows = await cursor.fetchall()
        finally:
            await conn.close()
        if not rows:
            await interaction.followup.send("No monitoring history has been recorded yet.")
            return
        text = "\n".join(f"{row[0]} | CPU {row[1]}% | RAM {row[2]}% | Disk {row[3]}% | Latency {row[4]} ms | {row[5]}" for row in rows)
        await interaction.followup.send(text[:2000])

    @app_commands.command(name="vps-stats")
    async def vps_stats(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        conn = await get_connection()
        try:
            cursor = await conn.execute("SELECT AVG(cpu_percent), AVG(ram_percent), AVG(disk_percent), AVG(latency_ms) FROM monitoring_history")
            row = await cursor.fetchone()
        finally:
            await conn.close()
        if row is None or all(value is None for value in row):
            await interaction.followup.send("No stats available yet.")
            return
        await interaction.followup.send(f"Average CPU: {row[0]}% | Average RAM: {row[1]}% | Average Disk: {row[2]}% | Avg latency: {row[3]} ms")

    @app_commands.command(name="vps-alert-config")
    async def vps_alert_config(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Alert configuration can be added via environment variables and the backing database. No remote alerting has been configured yet.")

    @app_commands.command(name="vps-alert-test")
    async def vps_alert_test(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Alert test request received. Monitoring will trigger alerts only once configured thresholds are active.")

    @app_commands.command(name="vps-alert-history")
    async def vps_alert_history(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        conn = await get_connection()
        try:
            cursor = await conn.execute("SELECT created_at, metric, threshold, observed, message FROM alerts ORDER BY id DESC LIMIT 10")
            rows = await cursor.fetchall()
        finally:
            await conn.close()
        if not rows:
            await interaction.followup.send("No alert history is available.")
            return
        text = "\n".join(f"{row[0]} | {row[1]} | threshold {row[2]} | observed {row[3]} | {row[4]}" for row in rows)
        await interaction.followup.send(text[:2000])


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VpsCog(bot))
