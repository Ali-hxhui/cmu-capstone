"""Verify access to the YouTube Data API without exposing the API key."""

import json
import os
import ssl
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import certifi


def load_env_file() -> None:
    """Load simple KEY=VALUE entries from a local .env file."""
    env_path = Path(__file__).with_name(".env")
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def main() -> None:
    load_env_file()
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        raise SystemExit("YOUTUBE_API_KEY is missing from .env.")

    params = urlencode(
        {
            "part": "snippet",
            "q": "mammogram explained",
            "type": "video",
            "maxResults": 3,
            "key": api_key,
        }
    )
    url = f"https://www.googleapis.com/youtube/v3/search?{params}"
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    try:
        with urlopen(url, timeout=30, context=ssl_context) as response:
            data = json.load(response)
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"API request failed ({error.code}): {details}") from error
    except URLError as error:
        raise SystemExit(f"Network request failed: {error.reason}") from error

    items = data.get("items", [])
    if not items:
        raise SystemExit("The API responded successfully but returned no videos.")

    print("YouTube Data API access confirmed.\n")
    for index, item in enumerate(items, start=1):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        print(f"{index}. {title}\n   https://www.youtube.com/watch?v={video_id}")


if __name__ == "__main__":
    main()
