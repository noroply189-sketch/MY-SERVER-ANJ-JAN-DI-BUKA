from __future__ import annotations

import asyncio
import logging
import secrets
from typing import Annotated
from urllib.parse import urlsplit

import discord
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field

from config.settings import get_settings
from database.db import get_connection
from services.vps_monitor import collect_vps_snapshot

settings = get_settings()
logger = logging.getLogger(__name__)
security = HTTPBasic(auto_error=False)
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.state.bot = None


DASHBOARD = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>Agent 01 | Operations</title>
<style>
:root{font-family:Inter,"Segoe UI",sans-serif;color:#e8eee9;background:#101411;font-synthesis:none;text-rendering:optimizeLegibility;--muted:#9aa79d;--line:#29332b;--lime:#c7f36b;--red:#ff867b;--panel:#171d18}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(ellipse at 78% -10%,#233624 0,transparent 40%),#101411}header{height:68px;padding:0 30px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;background:#111713e8;position:sticky;top:0;z-index:2}.brand{display:flex;align-items:center;gap:12px;font-weight:700}.mark{display:grid;place-items:center;width:32px;height:32px;background:var(--lime);color:#172016;font-weight:900;border-radius:8px}.subtle{color:var(--muted);font-size:13px}.status{display:flex;align-items:center;gap:8px;color:var(--lime);font-size:13px}.dot{width:8px;height:8px;border-radius:50%;background:var(--lime);box-shadow:0 0 12px #c7f366}main{max-width:1180px;padding:34px 26px 56px;margin:auto}.heading{display:flex;justify-content:space-between;align-items:end;gap:16px;margin-bottom:24px}.eyebrow{text-transform:uppercase;color:var(--lime);font-size:11px;font-weight:700;letter-spacing:1.4px}h1{font-size:26px;line-height:1.2;margin:8px 0 0}button{background:#253027;color:#e8eee9;border:1px solid #354238;border-radius:7px;padding:10px 14px;font-size:13px;font-weight:600;cursor:pointer}button:hover{border-color:var(--lime);color:var(--lime)}.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border:1px solid var(--line);border-radius:9px;overflow:hidden;background:var(--panel)}.metric{padding:19px 20px;border-right:1px solid var(--line)}.metric:last-child{border:0}.label{font-size:12px;color:var(--muted)}.value{font-size:25px;font-weight:650;margin:13px 0 10px}.unit{font-size:13px;color:var(--muted);font-weight:400}.bar{height:4px;background:#303932;border-radius:3px;overflow:hidden}.bar i{display:block;height:100%;background:var(--lime);width:0%;transition:width .3s}.grid{display:grid;grid-template-columns:1.35fr 1fr;gap:16px;margin-top:16px}.section{border:1px solid var(--line);border-radius:9px;background:var(--panel);padding:19px 20px;min-width:0}.section h2{font-size:14px;margin:0 0 17px}.facts{display:grid;grid-template-columns:1fr 1fr;gap:0 20px}.fact{padding:11px 0;border-bottom:1px solid #263028;display:flex;justify-content:space-between;gap:12px;font-size:12px}.fact span:first-child{color:var(--muted)}.fact span:last-child{text-align:right;overflow-wrap:anywhere}.chart{height:180px;width:100%;display:block}.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%;font-size:12px;white-space:nowrap}th{text-align:left;color:var(--muted);font-weight:500;padding:9px 8px;border-bottom:1px solid var(--line)}td{padding:10px 8px;border-bottom:1px solid #252e27}.empty{color:var(--muted);font-size:12px;padding:10px 0}.notice{color:var(--muted);font-size:12px;margin:15px 0 0}.error{color:var(--red)}footer{margin-top:20px;color:#819087;font-size:11px;display:flex;justify-content:space-between;gap:12px} @media(max-width:780px){header{padding:0 16px}main{padding:24px 14px}.metrics{grid-template-columns:1fr 1fr}.metric:nth-child(2){border-right:0}.metric:nth-child(-n+2){border-bottom:1px solid var(--line)}.grid{grid-template-columns:1fr}.heading{align-items:start;flex-direction:column}.facts{grid-template-columns:1fr}}
label{display:block;color:var(--muted);font-size:12px;margin:0 0 7px}input,textarea{display:block;width:100%;background:#101612;color:#e8eee9;border:1px solid #354238;border-radius:6px;padding:11px 12px;font:inherit;font-size:13px;margin-bottom:14px}input:focus,textarea:focus{outline:1px solid var(--lime);border-color:var(--lime)}textarea{min-height:112px;resize:vertical}.broadcast-row{display:grid;grid-template-columns:minmax(190px,1fr) 2fr;gap:16px}.broadcast-actions{display:flex;align-items:center;gap:14px}.broadcast-result{font-size:12px;color:var(--muted)}.broadcast-result.error{color:var(--red)}
</style>
</head>
<body>
<header><div class="brand"><span class="mark">A1</span><span>AGENT 01 <span class="subtle">/ OPERATIONS</span></span></div><div style="display:flex;align-items:center;gap:22px"><time id="utc-clock" class="subtle">UTC --:--:--</time><div class="status"><i class="dot"></i><span id="service-state">Loading</span></div></div></header>
<main>
<div class="heading"><div><div class="eyebrow">Runtime overview</div><h1>Service dashboard</h1><div class="subtle" id="host-line">Connecting to service metrics</div></div><button id="refresh">Refresh data</button></div>
<section class="metrics" aria-label="Live resource usage">
<div class="metric"><div class="label">CPU utilization</div><div class="value"><span id="cpu">--</span><span class="unit"> %</span></div><div class="bar"><i id="cpu-bar"></i></div></div>
<div class="metric"><div class="label">Memory used</div><div class="value"><span id="ram">--</span><span class="unit"> GB</span></div><div class="bar"><i id="ram-bar"></i></div></div>
<div class="metric"><div class="label">Root disk used</div><div class="value"><span id="disk">--</span><span class="unit"> GB</span></div><div class="bar"><i id="disk-bar"></i></div></div>
<div class="metric"><div class="label">Network latency</div><div class="value"><span id="latency">--</span><span class="unit"> ms</span></div><div class="subtle" id="network-method">Checking network</div></div>
</section>
<div class="grid">
<section class="section"><h2>System information</h2><div class="facts" id="facts"></div></section>
<section class="section"><h2>Resource history</h2><canvas class="chart" id="chart" aria-label="CPU, RAM, and disk history chart"></canvas><p class="notice" id="history-note">Loading stored samples</p></section>
</div>
<section class="section" style="margin-top:16px"><h2>Discord broadcast</h2><form id="broadcast-form"><div class="broadcast-row"><div><label for="channel-id">Text channel ID</label><input id="channel-id" name="channel_id" inputmode="numeric" pattern="[0-9]{15,22}" maxlength="22" placeholder="Copy channel ID" required></div><div><label for="broadcast-message">Message</label><textarea id="broadcast-message" name="message" maxlength="2000" placeholder="Write the announcement" required></textarea></div></div><div class="broadcast-actions"><button id="broadcast-submit" type="submit">Send broadcast</button><span id="broadcast-result" class="broadcast-result" role="status"></span></div></form></section>
<section class="section" style="margin-top:16px"><h2>Recent samples</h2><div class="table-wrap"><table><thead><tr><th>Recorded</th><th>CPU</th><th>RAM</th><th>Disk</th><th>Latency</th><th>Status</th></tr></thead><tbody id="rows"></tbody></table></div></section>
<footer><span>Metrics describe this Railway container, not external VPS hosts.</span><span id="updated">Waiting for first update</span></footer>
</main>
<script>
const $=id=>document.getElementById(id);const fmt=(v,s='')=>v===null||v===undefined?'N/A':`${v}${s}`;const setBar=(id,v)=>$(id).style.width=`${Math.max(0,Math.min(100,Number(v)||0))}%`;
function draw(samples){const c=$('chart'),ctx=c.getContext('2d'),dpr=window.devicePixelRatio||1,w=c.clientWidth,h=c.clientHeight;c.width=w*dpr;c.height=h*dpr;ctx.scale(dpr,dpr);ctx.clearRect(0,0,w,h);const pad=20,iw=w-pad*2,ih=h-pad*2;ctx.strokeStyle='#2b352d';ctx.lineWidth=1;for(let i=0;i<5;i++){const y=pad+i*ih/4;ctx.beginPath();ctx.moveTo(pad,y);ctx.lineTo(w-pad,y);ctx.stroke();ctx.fillStyle='#8f9b91';ctx.font='10px Segoe UI';ctx.fillText(`${100-i*25}%`,1,y+3)}const series=[['cpu_percent','#c7f36b'],['ram_percent','#76bdff'],['disk_percent','#ffad70']];for(const [key,color] of series){if(!samples.length)continue;ctx.beginPath();ctx.strokeStyle=color;ctx.lineWidth=2;samples.slice().reverse().forEach((s,i)=>{const x=pad+(samples.length<2?iw/2:i*iw/(samples.length-1));const y=pad+ih-(Math.max(0,Math.min(100,Number(s[key])||0))*ih/100);if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)});ctx.stroke()}if(!samples.length){ctx.fillStyle='#9aa79d';ctx.font='12px Segoe UI';ctx.fillText('No samples recorded yet',pad+10,h/2)}}
async function load(){ $('service-state').textContent='Refreshing';try{const r=await fetch('/api/overview',{cache:'no-store'});if(!r.ok)throw new Error(`Metrics request returned ${r.status}`);const d=await r.json(),s=d.snapshot;$('service-state').textContent=d.bot_ready?'BOT ONLINE':'BOT CONNECTING';$('host-line').textContent=`${s.hostname} · ${s.os_name} ${s.os_version} · ${s.architecture}`;$('cpu').textContent=fmt(s.cpu_usage);$('ram').textContent=fmt(s.ram_used_gb);$('disk').textContent=fmt(s.disk_used_gb);$('latency').textContent=fmt(s.vps_latency_ms);setBar('cpu-bar',s.cpu_usage);setBar('ram-bar',s.ram_percent);setBar('disk-bar',s.disk_percent);$('network-method').textContent=`${s.network_status} · ${s.network_method}`;const facts=[['CPU model',s.cpu_model],['CPU cores',`${s.physical_cores} physical / ${s.logical_cores} logical`],['RAM total',`${s.ram_total_gb} GB`],['RAM available',`${s.ram_available_gb} GB`],['Disk total',`${s.disk_total_gb} GB`],['Disk mount',s.disk_mount],['Kernel',s.kernel],['Uptime',`${Math.floor(s.uptime_seconds/3600)} hours`],['Bot latency',fmt(s.bot_latency_ms,' ms')],['Users in database',d.user_count]];$('facts').innerHTML=facts.map(([k,v])=>`<div class="fact"><span>${k}</span><span>${v??'N/A'}</span></div>`).join('');const samples=d.history||[];$('rows').innerHTML=samples.map(x=>`<tr><td>${x.recorded_at||'N/A'}</td><td>${fmt(x.cpu_percent,'%')}</td><td>${fmt(x.ram_percent,'%')}</td><td>${fmt(x.disk_percent,'%')}</td><td>${fmt(x.latency_ms,' ms')}</td><td>${x.status||'N/A'}</td></tr>`).join('');$('history-note').textContent=samples.length?`Showing ${samples.length} stored samples`:'No monitoring samples have been recorded yet';draw(samples);$('updated').textContent=`Last refreshed ${new Date().toLocaleTimeString()}`}catch(e){$('service-state').textContent='METRICS ERROR';$('service-state').classList.add('error');$('history-note').textContent=`Could not load dashboard data: ${e.message}`;$('history-note').classList.add('error')}}
function tickUTC(){$('utc-clock').textContent=`UTC ${new Date().toISOString().slice(11,19)}`};tickUTC();setInterval(tickUTC,1000);
$('broadcast-form').addEventListener('submit',async event=>{event.preventDefault();if(!confirm('Send this message to the selected Discord channel?'))return;const button=$('broadcast-submit'),result=$('broadcast-result');button.disabled=true;result.textContent='Sending…';result.classList.remove('error');try{const response=await fetch('/api/broadcast',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({channel_id:$('channel-id').value,message:$('broadcast-message').value})});const data=await response.json();if(!response.ok)throw new Error(data.detail||`Request failed (${response.status})`);result.textContent=`Sent to #${data.channel_name} · ${data.sent_at_utc}`;$('broadcast-message').value=''}catch(error){result.textContent=error.message;result.classList.add('error')}finally{button.disabled=false}});
$('refresh').addEventListener('click',load);window.addEventListener('resize',()=>load());load();setInterval(load,5000);
</script>
</body>
</html>'''


def require_admin(
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
) -> str:
    if not settings.admin_username or not settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin portal is disabled: configure ADMIN_USERNAME and ADMIN_PASSWORD.",
        )
    username_ok = credentials is not None and secrets.compare_digest(
        credentials.username.encode("utf-8"), settings.admin_username.encode("utf-8")
    )
    password_ok = credentials is not None and secrets.compare_digest(
        credentials.password.encode("utf-8"), settings.admin_password.encode("utf-8")
    )
    if not username_ok or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/", response_class=HTMLResponse)
async def dashboard(_: Annotated[str, Depends(require_admin)]) -> str:
    return DASHBOARD


@app.get("/api/overview")
async def overview(_: Annotated[str, Depends(require_admin)]) -> dict[str, object]:
    bot = app.state.bot
    bot_latency = round(bot.latency * 1000, 2) if bot and bot.latency else None
    snapshot = await asyncio.to_thread(collect_vps_snapshot, bot_latency)

    conn = await get_connection()
    try:
        cursor = await conn.execute("SELECT COUNT(*) FROM users")
        user_row = await cursor.fetchone()
        cursor = await conn.execute(
            "SELECT recorded_at, cpu_percent, ram_percent, disk_percent, latency_ms, status "
            "FROM monitoring_history ORDER BY id DESC LIMIT 24"
        )
        history_rows = await cursor.fetchall()
    finally:
        await conn.close()

    history = [
        {
            "recorded_at": row[0],
            "cpu_percent": row[1],
            "ram_percent": row[2],
            "disk_percent": row[3],
            "latency_ms": row[4],
            "status": row[5],
        }
        for row in history_rows
    ]
    return {
        "bot_ready": bool(bot and bot.is_ready()),
        "user_count": user_row[0] if user_row else 0,
        "snapshot": snapshot,
        "history": history,
    }


class BroadcastPayload(BaseModel):
    channel_id: int = Field(gt=0)
    message: str = Field(min_length=1, max_length=2000)


@app.post("/api/broadcast")
async def broadcast(
    payload: BroadcastPayload,
    request: Request,
    username: Annotated[str, Depends(require_admin)],
) -> dict[str, str]:
    origin = request.headers.get("origin", "")
    origin_parts = urlsplit(origin)
    request_host = request.headers.get("host", "").lower()
    if not origin_parts.netloc or origin_parts.netloc.lower() != request_host:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-origin request rejected.")

    bot = app.state.bot
    if bot is None or not bot.is_ready():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Discord bot is not ready.")

    channel = bot.get_channel(payload.channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(payload.channel_id)
        except (discord.NotFound, discord.Forbidden):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found or bot has no access.") from None

    if not isinstance(channel, (discord.TextChannel, discord.Thread)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose a server text channel or thread.")

    try:
        sent = await channel.send(payload.message, allowed_mentions=discord.AllowedMentions.none())
    except discord.Forbidden:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bot cannot send messages in that channel.") from None
    except discord.HTTPException:
        logger.exception("Discord broadcast failed for channel %s", payload.channel_id)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Discord rejected the broadcast.") from None

    logger.info("Admin %s sent broadcast to channel %s", username, payload.channel_id)
    return {
        "message_id": str(sent.id),
        "channel_name": channel.name,
        "sent_at_utc": sent.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
    }
