"""CLI entry point for suno-download."""

import sys
from pathlib import Path

from .auth import load_auth, AuthError
from .api import SunoClient, SunoAPIError
from .downloader import save_library_snapshot, download_song


def main():
    """Main CLI function."""
    print("Suno Download - Download public songs from your Suno.ai library")
    print("=" * 70)

    # Parse output directory from command line or prompt
    if len(sys.argv) > 1:
        output_dir = Path(sys.argv[1]).expanduser().resolve()
    else:
        default_dir = Path.home() / "Music" / "suno-download"
        response = input(f"\nOutput directory [{default_dir}]: ").strip()
        output_dir = Path(response).expanduser().resolve() if response else default_dir

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {output_dir}")

    # Load authentication
    print("\nLoading authentication...")
    try:
        auth_headers = load_auth()
        print("  ✓ Authentication loaded")
    except AuthError as e:
        print(f"\n✗ Authentication error:\n{e}")
        sys.exit(1)

    # Create API client and fetch songs
    client = SunoClient(auth_headers)

    try:
        all_songs = client.fetch_all_songs()
    except SunoAPIError as e:
        print(f"\n✗ API error:\n{e}")
        sys.exit(1)

    if not all_songs:
        print("\nNo songs found in your library.")
        sys.exit(0)

    # Save library snapshot
    print(f"\nSaving library snapshot...")
    try:
        save_library_snapshot(all_songs, output_dir)
    except Exception as e:
        print(f"  ✗ Warning: Failed to save snapshot: {e}")
        # Continue anyway

    # Filter to public songs
    public_songs = [song for song in all_songs if song.get('is_public', False)]
    print(f"\nFound {len(public_songs)} public songs (out of {len(all_songs)} total)")

    if not public_songs:
        print("\nNo public songs to download.")
        print("To make songs public, go to suno.com and change their visibility settings.")
        sys.exit(0)

    # Download public songs
    print(f"\nDownloading {len(public_songs)} public songs...")
    downloaded = 0
    skipped = 0

    for i, song in enumerate(public_songs, 1):
        if download_song(song, output_dir, i, len(public_songs)):
            downloaded += 1
        else:
            skipped += 1

    # Print summary
    print("\n" + "=" * 70)
    print("Download complete!")
    print(f"  Total songs in library: {len(all_songs)}")
    print(f"  Public songs: {len(public_songs)}")
    print(f"  Downloaded: {downloaded}")
    print(f"  Skipped (already exist): {skipped}")
    print(f"\nFiles saved to: {output_dir}")


if __name__ == "__main__":
    main()
