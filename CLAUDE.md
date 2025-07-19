# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Bot
```bash
# With Nix (recommended)
nix develop
python manage.py discord_bot

# Without Nix
uv sync
python manage.py discord_bot
```

### Code Quality
```bash
# Format and lint code
ruff format .
ruff check . --fix

# Check for linting issues without fixing
ruff check .
```

### Project Setup
```bash
# Initialize standalone mode (no database)
make init-standalone

# Initialize with database
make init
```

### Building Docker Image
```bash
nix build .#docker
docker load < result
```

### Management Commands
```bash
# Provision a server with integrations
python manage.py provision --server-vendor discord --server-uid <guild_id> --tier free --integrations tiktok instagram

# Purge old posts
python manage.py purge_posts
```

## Architecture Overview

This is a Django-based Discord bot that embeds media from various social platforms. The bot uses a plugin-style architecture with integrations for different platforms.

### Key Components

**Bot Core (`bot/`)**
- `adapters/discord/`: Discord bot implementation and configuration
- `service/service.py`: Main business logic for processing URLs and fetching posts
- `integrations/`: Platform-specific clients (Instagram, TikTok, Twitter, etc.)
- `models/`: Django models for servers, users, and posts
- `repository.py`: Data access layer

**Integration System**
- Each platform has its own client in `bot/integrations/`
- Registry pattern in `bot/integrations/registry.py` manages all integrations
- Base classes in `bot/integrations/base.py` define the integration interface
- Singleton pattern for client instances

**Configuration**
- Two modes: standalone (no DB) and full (with DB and caching)
- Settings in `conf/` directory
- Integration configs in `conf/_settings_app.py`
- User settings go in root `settings.py`

**Supported Platforms**
Instagram, TikTok, Reddit, Twitter, YouTube Shorts, Twitch, Threads, 24ur.com, 4chan, LinkedIn, Bluesky, Truth Social, Facebook (flaky)

### Development Patterns

- Django management commands for operations
- Async/await for integration clients
- Caching layer for performance
- Rate limiting and server tiers
- Structured logging with django-structlog
- Single-quote string formatting (Ruff configured)

### Key Files
- `bot/service/service.py`: Main post processing logic
- `bot/integrations/registry.py`: Integration discovery and routing
- `manage.py`: Django management entry point
- `pyproject.toml`: Project dependencies and tool configuration