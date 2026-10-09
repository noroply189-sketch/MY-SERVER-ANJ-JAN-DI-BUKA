from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
import time
from collections.abc import Iterable
from pathlib import Path

import psutil

from database.db import get_connection


def _safe_mb(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value / (1024 * 1024):.1f} MB"


def detect_cpu_model() -> str:
    cpuinfo = "/proc/cpuinfo"
    if os.path.exists(cpuinfo):
        try:
            with open(cpuinfo, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
            for line in text.splitlines():
                if line.lower().startswith("model name"):
                    _, _, value = line.partition(":")
                    return value.strip() or "Unknown"
        except OSError:
            pass
    return platform.processor() or "Unknown"


def uptime_seconds() -> float:
    try:
        return time.time() - psutil.boot_time()
    except Exception:
        return 0.0


def collect_network_latency(host: str = "1.1.1.1") -> dict[str, object]:
    status = "online"
    method = "TCP socket"
    latency_ms = None
    packet_loss = None

    try:
        ping_cmd = ["ping", "-c", "1", host]
        if os.name == "nt":
            ping_cmd = ["ping", "-n", "1", host]
        result = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            method = "ICMP ping"
            output = result.stdout + result.stderr
            for token in output.split():
                if token.endswith("ms"):
                    try:
                        latency_ms = float(token.replace("ms", ""))
                        break
                    except ValueError:
                        continue
            packet_loss = 0.0
    except Exception:
        latency_ms = None

    if latency_ms is None:
        try:
            start = time.perf_counter()
            with socket.create_connection((host, 443), timeout=5):
                latency_ms = round((time.perf_counter() - start) * 1000, 2)
            method = "TCP connection"
        except Exception:
            status = "offline"
            latency_ms = None

    if latency_ms is None:
        latency_ms = "N/A"
    return {"latency_ms": latency_ms, "method": method, "status": status, "packet_loss": packet_loss}


def collect_vps_snapshot(bot_latency_ms: float | None = None) -> dict[str, object]:
    cpu_percent = psutil.cpu_percent(interval=None)
    cpu_count_physical = psutil.cpu_count(logical=False)
    cpu_count_logical = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq()
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage("/")
    partitions = psutil.disk_partitions(all=False)
    main_mount = partitions[0].mountpoint if partitions else "/"
    net = collect_network_latency()
    uptime = uptime_seconds()

    snapshot = {
        "status": "ONLINE" if net.get("status") != "offline" else "OFFLINE",
        "bot_latency_ms": bot_latency_ms if bot_latency_ms is not None else "N/A",
        "vps_latency_ms": net.get("latency_ms"),
        "network_method": net.get("method", "N/A"),
        "network_status": net.get("status", "unknown"),
        "packet_loss": net.get("packet_loss", "N/A"),
        "cpu_model": detect_cpu_model(),
        "cpu_vendor": platform.python_implementation(),
        "physical_cores": cpu_count_physical if cpu_count_physical is not None else "N/A",
        "logical_cores": cpu_count_logical if cpu_count_logical is not None else "N/A",
        "cpu_usage": cpu_percent,
        "cpu_frequency_mhz": round(cpu_freq.current, 2) if cpu_freq else "N/A",
        "load_average": os.getloadavg() if hasattr(os, "getloadavg") else "N/A",
        "ram_total_gb": round(vm.total / (1024**3), 2),
        "ram_used_gb": round((vm.total - vm.available) / (1024**3), 2),
        "ram_available_gb": round(vm.available / (1024**3), 2),
        "ram_percent": vm.percent,
        "swap_total_gb": round(swap.total / (1024**3), 2),
        "swap_used_gb": round(swap.used / (1024**3), 2),
        "disk_total_gb": round(disk.total / (1024**3), 2),
        "disk_used_gb": round(disk.used / (1024**3), 2),
        "disk_available_gb": round(disk.free / (1024**3), 2),
        "disk_percent": disk.percent,
        "disk_mount": main_mount,
        "os_name": platform.system() or "Unknown",
        "os_version": platform.release() or "Unknown",
        "kernel": platform.version() or "Unknown",
        "architecture": platform.machine() or "Unknown",
        "uptime_seconds": uptime,
        "hostname": platform.node() or "Unknown",
        "monitoring_status": "ENABLED",
        "last_checked": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    }
    return snapshot


async def record_snapshot(snapshot: dict[str, object]) -> None:
    conn = await get_connection()
    try:
        await conn.execute(
            "INSERT INTO monitoring_history (cpu_percent, ram_percent, disk_percent, latency_ms, status, recorded_at, alert) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                snapshot.get("cpu_usage"),
                snapshot.get("ram_percent"),
                snapshot.get("disk_percent"),
                snapshot.get("vps_latency_ms"),
                snapshot.get("status"),
                snapshot.get("last_checked"),
                "",
            ),
        )
        await conn.commit()
    finally:
        await conn.close()


__all__ = [
    "collect_network_latency",
    "collect_vps_snapshot",
    "record_snapshot",
    "detect_cpu_model",
    "uptime_seconds",
]
