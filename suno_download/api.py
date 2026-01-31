"""Suno API client for fetching song data."""

from typing import Dict, List
import requests
import time


class SunoAPIError(Exception):
    """Raised when Suno API requests fail."""
    pass


class SunoClient:
    """Client for interacting with Suno's API."""

    BASE_URL = "https://studio-api.prod.suno.com"

    def __init__(self, headers: Dict[str, str]):
        """Initialize client with authentication headers.

        Args:
            headers: Dict with Authorization, Cookie, and Device-Id headers
        """
        self.headers = headers.copy()
        # Add additional required headers
        self.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        self.headers['Accept'] = 'application/json'
        self.headers['Content-Type'] = 'application/json'

    def fetch_all_songs(self) -> List[Dict]:
        """Fetch all songs from user's library via paginated API calls.

        Returns:
            List of song dictionaries with all fields from API

        Raises:
            SunoAPIError: If API requests fail
        """
        all_songs = []
        cursor = None
        page_num = 0

        print("Fetching songs from Suno API...")

        while True:
            url = f"{self.BASE_URL}/api/feed/v3"

            # Build POST request payload
            payload = {
                "cursor": cursor,
                "limit": 20,
                "filters": {
                    "disliked": "False",
                    "trashed": "False",
                    "fromStudioProject": {"presence": "False"},
                    "stem": {"presence": "False"},
                    "user": {"presence": "True"}
                }
            }

            try:
                response = requests.post(url, headers=self.headers, json=payload, timeout=30)
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if response.status_code == 401:
                    raise SunoAPIError(
                        "Authentication failed (401). Your credentials may have expired.\n"
                        "Please re-extract headers from browser DevTools."
                    )
                elif response.status_code == 429:
                    raise SunoAPIError(
                        f"Rate limited after fetching {len(all_songs)} songs.\n"
                        "Wait a few minutes before trying again. Your songs fetched so far have been saved."
                    )
                raise SunoAPIError(f"HTTP error fetching page {page_num}: {e}")
            except requests.exceptions.RequestException as e:
                raise SunoAPIError(f"Network error fetching page {page_num}: {e}")

            try:
                data = response.json()
            except ValueError as e:
                raise SunoAPIError(f"Invalid JSON response on page {page_num}: {e}")

            # Extract clips from response
            clips = data.get('clips', [])

            if not clips:
                break

            all_songs.extend(clips)
            print(f"  Fetched page {page_num}: {len(clips)} songs")

            # Check for next cursor for pagination
            cursor = data.get('cursor') or data.get('next_cursor')
            if not cursor:
                break

            page_num += 1

            # Add delay to avoid rate limiting (only if there are more pages)
            if cursor:
                time.sleep(1.5)

        print(f"Total songs fetched: {len(all_songs)}")
        return all_songs
