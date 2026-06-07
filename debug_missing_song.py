#!/usr/bin/env python3
"""Debug script to find missing songs and test different filter combinations."""

import json
import requests
from pathlib import Path
from suno_download.auth import load_auth

# Song we're looking for
TARGET_SONG_ID = "03eba5d5-f78d-4f62-8aef-4fa10f7cb089"
TARGET_SONG_TITLE = "There is Grace (Remastered)"

BASE_URL = "https://studio-api.prod.suno.com"


def test_filters(headers, filter_config, description):
    """Test a specific filter configuration."""
    print(f"\n{'='*70}")
    print(f"Testing: {description}")
    print(f"Filters: {json.dumps(filter_config, indent=2)}")
    print(f"{'='*70}")

    payload = {
        "cursor": None,
        "limit": 20,
        "filters": filter_config
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

        print(f"✓ Fetched {len(clips)} songs")

        # Look for our target song
        found = False
        for clip in clips:
            if clip.get('id') == TARGET_SONG_ID:
                print(f"\n🎉 FOUND TARGET SONG!")
                print(f"Title: {clip.get('title')}")
                print(f"ID: {clip.get('id')}")
                print(f"is_public: {clip.get('is_public')}")
                print(f"is_liked: {clip.get('is_liked')}")
                print(f"is_trashed: {clip.get('is_trashed')}")
                print(f"Full clip data:")
                print(json.dumps(clip, indent=2))
                found = True
                break

        if not found:
            print(f"✗ Target song NOT found in this result set")

            # Show some sample songs for comparison
            if clips:
                print(f"\nSample songs returned:")
                for i, clip in enumerate(clips[:3]):
                    print(f"  {i+1}. {clip.get('title')} (ID: {clip.get('id')})")
                    print(f"     is_public: {clip.get('is_public')}, is_liked: {clip.get('is_liked')}")

        return found

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run debug tests."""
    print("="*70)
    print("Debug Script: Finding Missing Songs")
    print("="*70)
    print(f"Looking for song: {TARGET_SONG_TITLE}")
    print(f"Song ID: {TARGET_SONG_ID}")

    # Load auth
    try:
        auth_headers = load_auth()
        # Add required headers
        auth_headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        auth_headers['Accept'] = 'application/json'
        auth_headers['Content-Type'] = 'application/json'
    except Exception as e:
        print(f"Error loading auth: {e}")
        return

    # Test different filter combinations
    test_configs = [
        # Current filters (what we're using now)
        {
            "config": {
                "disliked": "False",
                "trashed": "False",
                "fromStudioProject": {"presence": "False"},
                "stem": {"presence": "False"},
                "user": {"presence": "True"}
            },
            "description": "Current filters (disliked=False, trashed=False)"
        },

        # Remove disliked filter
        {
            "config": {
                "trashed": "False",
                "fromStudioProject": {"presence": "False"},
                "stem": {"presence": "False"},
                "user": {"presence": "True"}
            },
            "description": "Without 'disliked' filter"
        },

        # Minimal filters - just user songs, not trashed
        {
            "config": {
                "trashed": "False",
                "user": {"presence": "True"}
            },
            "description": "Minimal filters (only trashed=False, user=True)"
        },

        # Just user songs
        {
            "config": {
                "user": {"presence": "True"}
            },
            "description": "Only user filter"
        },

        # Empty filters
        {
            "config": {},
            "description": "No filters (might return all public songs)"
        },
    ]

    found_in = []
    for test in test_configs:
        if test_filters(auth_headers, test["config"], test["description"]):
            found_in.append(test["description"])

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    if found_in:
        print(f"✓ Target song FOUND in {len(found_in)} configuration(s):")
        for desc in found_in:
            print(f"  - {desc}")
        print(f"\nRecommendation: Update the app to use one of the filters above")
    else:
        print(f"✗ Target song NOT FOUND in any configuration")
        print(f"\nPossible reasons:")
        print(f"  1. Song might not be in the first 20 results (try increasing limit)")
        print(f"  2. Song might require different filter logic")
        print(f"  3. Song might need specific userId in filter")
        print(f"\nNext steps: Check the full library snapshot to see if it appears later")


if __name__ == "__main__":
    main()
