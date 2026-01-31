# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool to download all public songs from a user's Suno.ai library.

## Architecture

### Authentication
The app uses manual auth extraction from browser DevTools (no CAPTCHA service dependency):
- User captures headers from a working request to `studio-api.prod.suno.com` in browser Network tab
- Required headers: `Authorization` (Bearer token), `Device-Id`
- Optional header: `Cookie` (may not be needed for v3 API)
- Auth stored in `~/.suno-download/auth.json` or via environment variables

### API Endpoints
- **Base URL:** `https://studio-api.prod.suno.com`
- **List songs:** `POST /api/feed/v3` - cursor-based pagination, returns user's library
  - Request body: `{"cursor": null, "limit": 20, "filters": {...}}`
  - Response: `{"clips": [...], "cursor": "..."}`
- **Download URL:** `https://cdn1.suno.ai/{SONG_ID}.mp3`

### Song Data Structure
Key fields from API response (in `clips` array):
- `id` - unique song identifier (used for download URL)
- `title` - song title
- `is_public` - boolean, filter criteria for downloads
- `audio_url` - full CDN URL to MP3
- `status` - generation status (complete/streaming/error)
- `created_at` - timestamp

### App Flow
1. Load auth config from `~/.suno-download/auth.json` or env vars
2. Parse CLI arg for output directory (default: `~/Music/suno-download`)
3. Fetch all songs via cursor-based pagination to `/api/feed/v3` (POST requests with 1.5s delay to avoid rate limiting)
4. Save complete library snapshot to `suno_library.json`
5. Filter to songs where `is_public == true`
6. Download each MP3 to `{output_dir}/{title}_{id}.mp3`
7. Skip already-downloaded files (by checking existence)

## CLI Usage
```
python -m suno_download [OUTPUT_DIR]
```
- If no argument provided, prompts for directory (default: `~/Music/suno-download`)

## Configuration

### Auth file (`~/.suno-download/auth.json`)
```json
{
  "authorization": "Bearer eyJ...",
  "device_id": "uuid-here",
  "cookie": "__client=...; ..."  // Optional for v3 API
}
```

### Environment variables (alternative)
- `SUNO_AUTHORIZATION` - Bearer token (required)
- `SUNO_DEVICE_ID` - Device UUID (required)
- `SUNO_COOKIE` - Full cookie string (optional)
