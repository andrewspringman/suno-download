#!/usr/bin/env python3
"""Find a specific song by searching through all possible filter combinations."""

import json
import requests
import time
from suno_download.auth import load_auth

TARGET_SONG_ID = "03eba5d5-f78d-4f62-8aef-4fa10f7cb089"
BASE_URL = "https://studio-api.prod.suno.com"


def fetch_all_with_filters(headers, filters_desc, filters):
    """Fetch all songs with specific filters."""
    print(f"\n{'='*70}")
    print(f"Fetching ALL songs with: {filters_desc}")
    print(f"{'='*70}")

    all_clips = []
    cursor = None
    page = 0

    while True:
        payload = {
            "cursor": cursor,
            "limit": 50,  # Larger limit
            "filters": filters
        }

        try:
            response = requests.post(
                f"{BASE_URL}/api/feed/v3",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            clips = data.get('clips', [])

            if not clips:
                break

            all_clips.extend(clips)
            print(f"  Page {page}: {len(clips)} songs (total so far: {len(all_clips)})")

            # Check if target song is in this batch
            for clip in clips:
                if clip.get('id') == TARGET_SONG_ID:
                    print(f"\n🎉 FOUND TARGET SONG ON PAGE {page}!")
                    print(json.dumps(clip, indent=2))
                    return True, all_clips

            cursor = data.get('cursor') or data.get('next_cursor')
            if not cursor:
                break

            page += 1
            time.sleep(0.5)  # Small delay

        except Exception as e:
            print(f"✗ Error on page {page}: {e}")
            break

    print(f"\nTotal songs fetched: {len(all_clips)}")
    print(f"✗ Target song NOT found")
    return False, all_clips


def main():
    """Search for the missing song."""
    print("Searching for missing song...")
    print(f"Target ID: {TARGET_SONG_ID}")

    # Load and prepare auth headers
    try:
        headers = load_auth()
        headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json'
    except Exception as e:
        print(f"Auth error: {e}")
        return

    # Try with no filters at all
    found, _ = fetch_all_with_filters(
        headers,
        "NO FILTERS (all songs)",
        {}
    )

    if found:
        print("\n✓ Song found with NO filters - it's being excluded by current filters!")
        return

    # Try with only user filter
    found, _ = fetch_all_with_filters(
        headers,
        "Only user=True filter",
        {"user": {"presence": "True"}}
    )

    if found:
        print("\n✓ Song found with user-only filter!")
        return

    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    print("Song not found in ANY query results.")
    print("\nPossible reasons:")
    print("1. Song was created AFTER the last fetch")
    print("2. Song belongs to a different user (check if you're the owner)")
    print("3. Song might be in a special category we're not querying")
    print("\nNext step: Check on suno.com if this song is in YOUR library")
    print(f"or if it's someone else's song that you liked/favorited.")


if __name__ == "__main__":
    main()
