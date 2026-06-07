# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool that downloads all public songs (and saves metadata for all songs, public and private) from a user's Suno.ai library.

## Commands

```bash
# Setup (from repo root)
python3 -m venv venv && source venv/bin/activate
pip install -e .

# Run
python -m suno_download [OUTPUT_DIR]
# or, if installed in an active venv:
suno-download [OUTPUT_DIR]
```

There is no test suite, linter, or build step configured (no `tests/`, no lint config in `setup.py`).

## Architecture

The package (`suno_download/`) is a thin pipeline of four modules wired together in `__main__.py:main()`:

1. **`auth.py`** — `load_auth()` reads credentials from `~/.suno-download/auth.json`, falling back to `SUNO_AUTHORIZATION` / `SUNO_DEVICE_ID` / `SUNO_COOKIE` env vars. Returns a headers dict (`Authorization`, `Device-Id`, optional `Cookie`). Raises `AuthError` on missing/invalid config.
2. **`api.py`** — `SunoClient.fetch_all_songs()` pages through `POST /api/feed/v3` (cursor-based, 1.5s delay between pages to dodge rate limits) and returns the full list of clip dicts. Raises `SunoAPIError` for HTTP/network/JSON failures, with specific messages for 401 (expired auth) and 429 (rate limited).
3. **`downloader.py`** — `save_library_snapshot()` writes the full song list + timestamp to `suno_library.json`; `download_song()` sanitizes the title into a filename (`{title}_{id}.mp3`), skips files that already exist, and tries the CDN URL (`https://cdn1.suno.ai/{id}.mp3`) before falling back to the song's `audio_url`.
4. **`__main__.py`** — orchestrates: resolve output dir → load auth → fetch all songs → save snapshot → filter to `is_public == True` → download each, skipping existing files → print summary.

### Authentication model

No automated login or CAPTCHA handling — the user manually copies `Authorization` (Bearer token) and `Device-Id` headers from a browser DevTools Network capture of a request to `studio-api.prod.suno.com`. `Cookie` is optional and may not be required by the v3 API. See README.md "Setup: Extract Authentication" for the full extraction walkthrough that should stay in sync with `auth.py`'s error message.

### API details

- **Base URL:** `https://studio-api.prod.suno.com`
- **List songs:** `POST /api/feed/v3`, body `{"cursor": ..., "limit": 20, "filters": {"trashed": "False", "user": {"presence": "True"}}}`. This filter set returns *all* non-trashed songs (liked, disliked, neutral, remasters, stems, studio projects) — it does not filter by visibility. Response is `{"clips": [...], "cursor": "..."}`.
- **Download URL:** `https://cdn1.suno.ai/{SONG_ID}.mp3`, with the clip's own `audio_url` as fallback.
- Visibility is determined client-side by the `is_public` boolean on each clip — only public clips get downloaded, but metadata for everything is saved to `suno_library.json`.

### Ad-hoc debug scripts

`find_song.py` and `debug_missing_song.py` at the repo root are one-off investigation scripts (hardcoded target song IDs) used to probe why specific songs were missing from feed results under different filter combinations. They import `suno_download.auth.load_auth` directly and are not part of the package or its entry points.
