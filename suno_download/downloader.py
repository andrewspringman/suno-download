"""Download songs and save library snapshots."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import requests


def save_library_snapshot(songs: List[Dict], output_dir: Path) -> None:
    """Save complete song data to JSON file for change tracking.

    Args:
        songs: List of all song dictionaries from API
        output_dir: Directory to save the snapshot file
    """
    snapshot = {
        'timestamp': datetime.now().isoformat(),
        'total_songs': len(songs),
        'songs': songs
    }

    snapshot_file = output_dir / 'suno_library.json'

    with open(snapshot_file, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    print(f"Saved library snapshot: {snapshot_file}")


def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove invalid characters for cross-platform compatibility
    # Keep: letters, digits, spaces, hyphens, underscores, periods
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace multiple spaces with single space
    sanitized = re.sub(r'\s+', ' ', sanitized)
    # Trim whitespace
    sanitized = sanitized.strip()
    # Limit length to avoid filesystem issues
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    return sanitized


def download_song(song: Dict, output_dir: Path, current: int, total: int) -> bool:
    """Download a single song MP3 file.

    Args:
        song: Song dictionary from API
        output_dir: Directory to save the MP3
        current: Current song number (for progress display)
        total: Total number of songs to download

    Returns:
        True if downloaded, False if skipped (already exists or error)
    """
    song_id = song.get('id')
    title = song.get('title', 'Untitled')

    if not song_id:
        print(f"  [{current}/{total}] Skipping song with no ID: {title}")
        return False

    # Construct filename
    safe_title = sanitize_filename(title)
    filename = f"{safe_title}_{song_id}.mp3"
    filepath = output_dir / filename

    # Skip if already exists
    if filepath.exists():
        print(f"  [{current}/{total}] Already exists: {filename}")
        return False

    # Try CDN URL first
    download_url = f"https://cdn1.suno.ai/{song_id}.mp3"

    # If CDN URL doesn't work, try audio_url from song data
    audio_url_fallback = song.get('audio_url')

    print(f"  [{current}/{total}] Downloading: {filename}")

    # Try CDN URL
    try:
        response = requests.get(download_url, timeout=60, stream=True)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"      ✓ Downloaded successfully")
        return True

    except requests.exceptions.RequestException as e:
        # Try fallback URL if available
        if audio_url_fallback:
            try:
                print(f"      CDN failed, trying audio_url...")
                response = requests.get(audio_url_fallback, timeout=60, stream=True)
                response.raise_for_status()

                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                print(f"      ✓ Downloaded successfully (fallback)")
                return True

            except requests.exceptions.RequestException as e2:
                print(f"      ✗ Failed to download (both URLs): {e2}")
                return False
        else:
            print(f"      ✗ Failed to download: {e}")
            return False
