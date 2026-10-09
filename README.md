# Discord AI Agent

This project is a modular Discord AI assistant with multi-provider AI routing, file handling, web search, education workflows, and VPS monitoring.

## Features

- Multi-provider routing for OpenRouter, Groq, and Google Gemini
- Slash commands for AI, file generation, and VPS monitoring
- Real document/file reading for common formats
- File generation for PDF, DOCX, XLSX, PPTX, code, and ZIP
- FFmpeg-based video generation and slideshow workflow
- SQLite-backed session and telemetry storage
- VPS metrics using psutil and network checks
- Admin authorization via configured Discord IDs
- Security checks for file size, extension, and temporary file cleanup

## Project layout

- `main.py` – bot entry point
- `config/settings.py` – centralized environment settings
- `providers/` – provider-specific API connectors
- `services/` – business logic for AI router, search, file handling, and VPS
- `cogs/` – Discord slash command groups
- `database/db.py` – SQLite initialization and helpers
- `utils/` – validation, logger, and security helpers
- `workers/` – task queue and monitoring workers

## Installation

### Linux / VPS

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip ffmpeg tesseract-ocr
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### Windows

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
```

## Environment setup

Copy `.env.example` to `.env` and fill values.

```bash
cp .env.example .env
```

Set the required Discord, provider, and VPS monitoring variables before running.

## Running the bot

```bash
python main.py
```

## Slash command registration

Use the application command deployment in `main.py` with the configured `DISCORD_GUILD_ID` or global registration.

## Security notes

- Keep API keys in `.env` only.
- Do not run untrusted files or code on production hosts.
- Validate attachment types and sanitize filenames.
- Avoid exposing credentials in logs or Discord embeds.

## Troubleshooting

- Missing Discord intents: enable Guild Messages, Message Content, and server members when needed.
- Provider errors: verify keys and selected model names.
- File upload issues: check size and allowed extension rules.
- SSH failures: verify host key, authentication, and allowed hosts.

## Notes

Some features require real external API keys and network access. They remain disabled or fail gracefully until configured.
"# my-server-" 
