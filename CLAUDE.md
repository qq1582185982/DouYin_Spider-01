# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains two distinct tools for video platform management:

1. **Douyin Spider** (Root directory) - A Python-based tool for Douyin (TikTok) data collection
   - Collects user profiles, video details, and live stream data
   - Located in the root directory with Python files
   - NEW: Web UI built with SvelteKit in `web/` directory
   - Flask API server in `app.py`

2. **bili-sync-01** - A Rust-based Bilibili video synchronization tool
   - Downloads and manages videos from Bilibili
   - Web interface built with Svelte
   - Located in the `bili-sync-01/` subdirectory

## Common Commands

### Douyin Spider Commands
```bash
# Install dependencies
pip install -r requirements.txt
npm install

# Run the main spider (CLI mode)
python main.py

# Run live stream monitoring server
python dy_live/server.py

# Run Flask API server
python app.py

# Run web UI (in a new terminal)
cd web
npm install
npm run dev

# Or use the batch file
start-web.bat
```

### Douyin Spider Web UI Commands
```bash
cd web

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Type checking
npm run check

# Format code
npm run format

# Lint code
npm run lint
```

### bili-sync-01 Commands
```bash
cd bili-sync-01

# Setup development environment
./make.bat setup

# Run development servers (Rust backend + Svelte frontend)
./make.bat dev

# Run tests
./make.bat test

# Format code
./make.bat fmt

# Lint code
./make.bat lint

# Build for production
./make.bat build

# Build release version
./make.bat release

# Clean build artifacts
./make.bat clean

# Run documentation server
./make.bat docs

# Build documentation
./make.bat docs-build

# Docker operations
./make.bat docker    # Build Docker image
./make.bat compose   # Run with Docker Compose
```

### bili-sync-01 Web Frontend Commands
```bash
cd bili-sync-01/web

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run type checks
npm run check

# Format code
npm run format

# Lint code
npm run lint
```

## Architecture Overview

### Douyin Spider Architecture
- **Entry Point**: `main.py` - Main entry for the spider functionality
- **API Layer**: `dy_apis/douyin_api.py` - Contains all Douyin API interfaces
- **Live Monitoring**: `dy_live/server.py` - WebSocket server for live stream monitoring
- **Utilities**: `utils/` - Common utilities for cookies, data processing
- **Builders**: `builder/` - Request builders for auth, headers, params
- **Static**: `static/` - Protocol buffer files and JavaScript utilities
- **Flask API**: `app.py` - REST API server for web UI
- **Web UI**: `web/` - SvelteKit-based management interface
  - Built with SvelteKit + TypeScript + Tailwind CSS
  - Provides user-friendly interface for spider operations
  - Real-time task monitoring and management

### bili-sync-01 Architecture
- **Backend (Rust)**:
  - `crates/bili_sync/` - Main application logic
  - `crates/bili_sync_entity/` - Database entities (SeaORM)
  - `crates/bili_sync_migration/` - Database migrations
  - Entry point: `crates/bili_sync/src/main.rs`
  - HTTP server on port 12345

- **Frontend (Svelte)**:
  - `web/` - SvelteKit application
  - Uses Tailwind CSS and custom UI components
  - Communicates with backend via REST API and WebSocket

- **Key Features**:
  - Video source management (favorites, UP submissions, watch later, bangumi)
  - Download queue management with persistence
  - Danmaku (bullet comments) download and conversion
  - Web-based configuration interface

## Important Notes

1. **Authentication**: Both tools require platform cookies for authentication. Configure via:
   - Douyin: `.env` file with cookies from www.douyin.com and live.douyin.com
   - bili-sync: Web interface login or manual cookie configuration

2. **bili-sync Development**: When developing the frontend, changes require:
   - Running `npx svelte-kit sync` after modifying routes
   - Building frontend before testing with backend

3. **Database**: bili-sync uses SQLite with SeaORM for persistence

4. **Port Usage**:
   - Douyin Spider Flask API: 8000
   - Douyin Spider Web UI dev: 5173
   - bili-sync API: 12345
   - bili-sync frontend dev: 5173