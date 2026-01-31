"""Authentication handling for Suno API."""

import json
import os
from pathlib import Path
from typing import Dict


class AuthError(Exception):
    """Raised when authentication configuration is invalid or missing."""
    pass


def load_auth() -> Dict[str, str]:
    """Load authentication credentials from file or environment variables.

    Returns:
        Dict with headers ready for API requests: {
            'Authorization': 'Bearer ...',
            'Cookie': '...',
            'Device-Id': '...'
        }

    Raises:
        AuthError: If credentials are not found or invalid.
    """
    # Try loading from file first
    auth_file = Path.home() / ".suno-download" / "auth.json"

    if auth_file.exists():
        try:
            with open(auth_file, 'r') as f:
                data = json.load(f)

            authorization = data.get('authorization')
            cookie = data.get('cookie')  # Optional for v3 API
            device_id = data.get('device_id')

            # Authorization and device_id are required
            if not authorization or not device_id:
                raise AuthError(
                    f"Auth file {auth_file} is missing required fields. "
                    "Required: authorization, device_id. Optional: cookie"
                )

            headers = {
                'Authorization': authorization,
                'Device-Id': device_id
            }
            # Add cookie if present (may not be needed for v3)
            if cookie:
                headers['Cookie'] = cookie

            return headers
        except json.JSONDecodeError as e:
            raise AuthError(f"Invalid JSON in auth file {auth_file}: {e}")
        except Exception as e:
            raise AuthError(f"Error reading auth file {auth_file}: {e}")

    # Fall back to environment variables
    authorization = os.getenv('SUNO_AUTHORIZATION')
    cookie = os.getenv('SUNO_COOKIE')  # Optional
    device_id = os.getenv('SUNO_DEVICE_ID')

    if not authorization or not device_id:
        raise AuthError(
            "Authentication not found. Either:\n"
            f"  1. Create {auth_file} with required keys: authorization, device_id (cookie optional)\n"
            "  2. Set environment variables: SUNO_AUTHORIZATION, SUNO_DEVICE_ID (SUNO_COOKIE optional)\n"
            "\nTo extract auth:\n"
            "  1. Open suno.com in browser and log in\n"
            "  2. Open DevTools (F12) -> Network tab\n"
            "  3. Navigate to your library to trigger API calls\n"
            "  4. Find a request to studio-api.prod.suno.com/api/feed/v3\n"
            "  5. Copy headers: authorization (Bearer token), device-id"
        )

    headers = {
        'Authorization': authorization,
        'Device-Id': device_id
    }
    if cookie:
        headers['Cookie'] = cookie

    return headers
