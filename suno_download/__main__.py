"""CLI entry point for suno-download."""

import re
import sys
from pathlib import Path

from .auth import load_auth, AuthError
from .api import SunoClient, SunoAPIError
from .downloader import save_library_snapshot, download_song, generate_tagger_json


def _extract_playlist_id(id_or_url: str) -> str:
    """Accept a full Suno playlist URL or bare ID and return the ID."""
    # e.g. https://suno.com/playlist/abc-123 or suno.com/playlist/abc-123
    match = re.search(r'/playlist/([A-Za-z0-9_-]+)', id_or_url)
    if match:
        return match.group(1)
    # Bare ID (UUID or slug)
    return id_or_url.strip()


def _load_auth_or_exit():
    print("\nLoading authentication...")
    try:
        headers = load_auth()
        print("  ✓ Authentication loaded")
        return headers
    except AuthError as e:
        print(f"\n✗ Authentication error:\n{e}")
        sys.exit(1)


def cmd_playlist(args):
    """suno-download playlist <id_or_url> [output_dir] [options]"""
    import argparse
    parser = argparse.ArgumentParser(
        prog="suno-download playlist",
        description="Download a Suno playlist and generate a bulk-id3-tagger JSON template.",
    )
    parser.add_argument("playlist", help="Suno playlist ID or URL")
    parser.add_argument("output_dir", nargs="?", default=None,
                        help="Directory to save MP3s and tags.json (default: ~/Music/<playlist-name>)")
    parser.add_argument("--album",  default="", help="Album name for tagger JSON")
    parser.add_argument("--artist", default="", help="Artist name for tagger JSON")
    parser.add_argument("--genre",  default="", help="Genre for tagger JSON")
    parser.add_argument("--year",   default="", help="Year for tagger JSON")
    parser.add_argument("--artwork", default="", help="Path to artwork file for tagger JSON")
    parsed = parser.parse_args(args)

    playlist_id = _extract_playlist_id(parsed.playlist)
    auth_headers = _load_auth_or_exit()
    client = SunoClient(auth_headers)

    print(f"\nFetching playlist '{playlist_id}'...")
    try:
        result = client.fetch_playlist(playlist_id)
    except SunoAPIError as e:
        print(f"\n✗ {e}")
        sys.exit(1)

    songs = result['clips']
    playlist_name = result['name']

    # Determine output directory
    if parsed.output_dir:
        output_dir = Path(parsed.output_dir).expanduser().resolve()
    else:
        safe_name = re.sub(r'[^\w\s-]', '', playlist_name).strip().replace(' ', '_')
        output_dir = Path.home() / "Music" / safe_name
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")

    # Download songs
    print(f"\nDownloading {len(songs)} songs...")
    downloaded = skipped = 0
    for i, song in enumerate(songs, 1):
        if download_song(song, output_dir, i, len(songs)):
            downloaded += 1
        else:
            skipped += 1

    # Generate tagger JSON
    generate_tagger_json(
        songs, output_dir,
        album=parsed.album or playlist_name,
        artist=parsed.artist,
        genre=parsed.genre,
        year=parsed.year,
        artwork=parsed.artwork,
    )

    print("\n" + "=" * 70)
    print(f"Playlist download complete!")
    print(f"  Songs in playlist: {len(songs)}")
    print(f"  Downloaded: {downloaded}")
    print(f"  Skipped (already exist): {skipped}")
    print(f"  Files + tags.json saved to: {output_dir}")
    print(f"\nNext steps:")
    print(f"  1. Edit {output_dir}/tags.json — fill in artist, genre, year, artwork")
    print(f"  2. bulk-id3-tagger tag {output_dir} {output_dir}/tags.json")


def cmd_download(args):
    """Original full-library download command."""
    if args:
        output_dir = Path(args[0]).expanduser().resolve()
    else:
        default_dir = Path.home() / "Music" / "suno-download"
        response = input(f"\nOutput directory [{default_dir}]: ").strip()
        output_dir = Path(response).expanduser().resolve() if response else default_dir

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {output_dir}")

    auth_headers = _load_auth_or_exit()
    client = SunoClient(auth_headers)

    try:
        all_songs = client.fetch_all_songs()
    except SunoAPIError as e:
        print(f"\n✗ API error:\n{e}")
        sys.exit(1)

    if not all_songs:
        print("\nNo songs found in your library.")
        sys.exit(0)

    print(f"\nSaving library snapshot...")
    try:
        save_library_snapshot(all_songs, output_dir)
    except Exception as e:
        print(f"  ✗ Warning: Failed to save snapshot: {e}")

    public_songs = [s for s in all_songs if s.get('is_public', False)]
    print(f"\nFound {len(public_songs)} public songs (out of {len(all_songs)} total)")

    if not public_songs:
        print("\nNo public songs to download.")
        sys.exit(0)

    print(f"\nDownloading {len(public_songs)} public songs...")
    downloaded = skipped = 0
    for i, song in enumerate(public_songs, 1):
        if download_song(song, output_dir, i, len(public_songs)):
            downloaded += 1
        else:
            skipped += 1

    print("\n" + "=" * 70)
    print("Download complete!")
    print(f"  Total songs in library: {len(all_songs)}")
    print(f"  Public songs: {len(public_songs)}")
    print(f"  Downloaded: {downloaded}")
    print(f"  Skipped (already exist): {skipped}")
    print(f"\nFiles saved to: {output_dir}")


def main():
    """Main CLI function — dispatches to subcommands."""
    if len(sys.argv) > 1 and sys.argv[1] == "playlist":
        print("Suno Download — Playlist Mode")
        print("=" * 70)
        cmd_playlist(sys.argv[2:])
    else:
        print("Suno Download - Download public songs from your Suno.ai library")
        print("=" * 70)
        cmd_download(sys.argv[1:])


if __name__ == "__main__":
    main()
