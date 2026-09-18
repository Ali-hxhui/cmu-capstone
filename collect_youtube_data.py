"""Collect reproducible YouTube video metadata for screening search terms."""

import argparse
import csv
import hashlib
import json
import os
import re
import ssl
import sys
import time
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import certifi


API_BASE_URL = "https://www.googleapis.com/youtube/v3"
VIDEO_COLUMNS = [
    "run_id",
    "collected_at",
    "video_id",
    "url",
    "title",
    "description",
    "channel_id",
    "channel_title",
    "channel_description",
    "channel_published_at",
    "channel_country",
    "channel_view_count",
    "channel_subscriber_count",
    "channel_hidden_subscriber_count",
    "video_published_at",
    "duration_iso8601",
    "duration_seconds",
    "default_language",
    "default_audio_language",
    "caption_available",
    "transcript_status",
    "transcript_text",
    "transcript_source",
    "transcript_retrieval_error",
    "privacy_status",
    "made_for_kids",
    "view_count",
    "like_count",
    "comment_count",
    "favorite_count",
    "metadata_available",
    "search_query_count",
    "first_seen_query",
    "first_seen_rank",
    "normalized_title",
    "near_duplicate_key",
    "near_duplicate_candidate",
    "search_queries",
]
MATCH_COLUMNS = [
    "run_id",
    "collected_at",
    "video_id",
    "query_id",
    "cancer_domain",
    "search_query",
    "normalized_search_query",
    "search_rank",
    "contributor",
    "source",
    "scope_category",
]
QUERY_COLUMNS = [
    "run_id",
    "query_id",
    "input_row",
    "cancer_domain",
    "search_query",
    "normalized_search_query",
    "contributor",
    "source",
    "scope_category",
]
ERROR_COLUMNS = [
    "run_id",
    "collected_at",
    "stage",
    "cancer_domain",
    "search_query",
    "video_id",
    "error",
]


class YouTubeApiError(RuntimeError):
    """A YouTube API request failed."""


def load_env_file() -> None:
    """Load simple KEY=VALUE entries from the project .env file."""
    env_path = Path(__file__).with_name(".env")
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def api_get(resource: str, params: dict[str, str], max_retries: int) -> dict[str, Any]:
    """Call a read-only YouTube Data API resource."""
    api_key = os.environ["YOUTUBE_API_KEY"]
    query = urlencode({**params, "key": api_key})
    url = f"{API_BASE_URL}/{resource}?{query}"
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    for attempt in range(max_retries + 1):
        try:
            with urlopen(url, timeout=30, context=ssl_context) as response:
                return json.load(response)
        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            if error.code not in {429, 500, 502, 503, 504} or attempt == max_retries:
                raise YouTubeApiError(f"HTTP {error.code}: {body}") from error
            failure = f"HTTP {error.code}"
        except URLError as error:
            if attempt == max_retries:
                raise YouTubeApiError(f"Network error: {error.reason}") from error
            failure = f"Network error: {error.reason}"
        delay_seconds = 2**attempt
        print(
            f"{failure}; retrying in {delay_seconds} second(s) "
            f"({attempt + 1}/{max_retries}).",
            file=sys.stderr,
        )
        time.sleep(delay_seconds)
    raise AssertionError("Unreachable retry state.")


def normalize_text(value: str) -> str:
    """Collapse whitespace for reliable comparisons and downstream text processing."""
    return " ".join(value.split())


def duration_to_seconds(value: str) -> int | str:
    """Convert YouTube's ISO 8601 duration to seconds when present."""
    match = re.fullmatch(r"P(?:\d+D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", value)
    if not match:
        return ""
    hours, minutes, seconds = (int(part or 0) for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def read_search_terms(path: Path) -> list[dict[str, str]]:
    """Read required search_query and optional cancer_domain columns."""
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or "search_query" not in reader.fieldnames:
            raise ValueError("The input CSV must have a 'search_query' column.")
        terms = []
        for input_row, row in enumerate(reader, start=2):
            query = (row.get("search_query") or "").strip()
            if query:
                terms.append(
                    {
                        "input_row": str(input_row),
                        "query_id": f"query_{len(terms) + 1:03d}",
                        "search_query": query,
                        "normalized_search_query": normalize_text(query).casefold(),
                        "cancer_domain": (row.get("cancer_domain") or "").strip(),
                        "contributor": (row.get("contributor") or "").strip(),
                        "source": (row.get("source") or "").strip(),
                        "scope_category": (row.get("scope_category") or "").strip(),
                    }
                )
    if not terms:
        raise ValueError("The input CSV contains no search terms.")
    return terms


def retrieve_search_results(
    query: str,
    top_n: int,
    region_code: str | None,
    relevance_language: str | None,
    max_retries: int,
) -> list[dict[str, Any]]:
    """Return up to top_n video search results with their query-specific ranks."""
    results: list[dict[str, Any]] = []
    page_token: str | None = None

    while len(results) < top_n:
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": str(min(50, top_n - len(results))),
        }
        if region_code:
            params["regionCode"] = region_code
        if relevance_language:
            params["relevanceLanguage"] = relevance_language
        if page_token:
            params["pageToken"] = page_token

        response = api_get("search", params, max_retries)
        for item in response.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            if video_id:
                results.append({"video_id": video_id, "snippet": item.get("snippet", {})})
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return results[:top_n]


def chunks(values: list[str], size: int) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def retrieve_video_details(
    video_ids: list[str], max_retries: int
) -> dict[str, dict[str, Any]]:
    """Fetch detailed metadata for up to 50 video IDs per API request."""
    videos: dict[str, dict[str, Any]] = {}
    for batch in chunks(video_ids, 50):
        response = api_get(
            "videos",
            {
                "part": "snippet,contentDetails,statistics,status",
                "id": ",".join(batch),
                "maxResults": "50",
            },
            max_retries,
        )
        for item in response.get("items", []):
            videos[item["id"]] = item
    return videos


def retrieve_channel_details(
    channel_ids: list[str], max_retries: int
) -> dict[str, dict[str, Any]]:
    """Fetch channel metadata for channels represented in the dataset."""
    channels: dict[str, dict[str, Any]] = {}
    for batch in chunks(channel_ids, 50):
        response = api_get(
            "channels",
            {"part": "snippet,statistics", "id": ",".join(batch), "maxResults": "50"},
            max_retries,
        )
        for item in response.get("items", []):
            channels[item["id"]] = item
    return channels


def write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect YouTube video and channel metadata for screening search terms."
    )
    parser.add_argument(
        "--input",
        default="search_terms/search_terms.csv",
        help="CSV with search_query column.",
    )
    parser.add_argument(
        "--output-dir", default="data/runs", help="Parent directory for versioned collection runs."
    )
    parser.add_argument(
        "--run-id", help="Unique run identifier. Defaults to the current UTC timestamp."
    )
    parser.add_argument("--top-n", type=int, default=20, help="Videos retrieved per query (default: 20).")
    parser.add_argument("--start-at", type=int, default=0, help="Zero-based input row for a batch.")
    parser.add_argument("--max-queries", type=int, help="Maximum number of queries in this batch.")
    parser.add_argument("--region-code", default="US", help="Two-letter search region; use '' for none.")
    parser.add_argument(
        "--relevance-language", default="en", help="Preferred result language; use '' for none."
    )
    parser.add_argument(
        "--max-retries", type=int, default=2, help="Retries for transient API errors (default: 2)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the selected search-term batch and estimate quota without calling YouTube.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not 1 <= args.top_n <= 500:
        raise SystemExit("--top-n must be between 1 and 500.")
    if args.max_retries < 0:
        raise SystemExit("--max-retries must be zero or greater.")

    try:
        terms = read_search_terms(Path(args.input))
    except (OSError, ValueError) as error:
        raise SystemExit(f"Cannot read search terms: {error}") from error

    selected_terms = terms[args.start_at :]
    if args.max_queries is not None:
        selected_terms = selected_terms[: args.max_queries]
    if not selected_terms:
        raise SystemExit("No search terms were selected for this batch.")

    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path(args.output_dir) / run_id
    if output_dir.exists():
        raise SystemExit(f"Run directory already exists: {output_dir}. Choose a new --run-id.")

    estimated_search_units = len(selected_terms) * 100
    if args.dry_run:
        print(f"Dry run passed: {len(selected_terms)} search terms selected.")
        print(f"Run directory: {output_dir}")
        print(f"Estimated search quota: {estimated_search_units} units.")
        print("No YouTube API request was made.")
        return

    load_env_file()
    if not os.environ.get("YOUTUBE_API_KEY"):
        raise SystemExit("YOUTUBE_API_KEY is missing from .env.")

    print(
        f"Collecting {len(selected_terms)} queries × Top {args.top_n}. "
        f"Search requests alone use about {estimated_search_units} quota units."
    )

    collected_at = datetime.now(timezone.utc).isoformat()
    matches: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    search_snippets: OrderedDict[str, dict[str, Any]] = OrderedDict()

    for number, term in enumerate(selected_terms, start=args.start_at + 1):
        query = term["search_query"]
        print(f"[{number}/{len(terms)}] Searching: {query}")
        try:
            results = retrieve_search_results(
                query,
                args.top_n,
                args.region_code or None,
                args.relevance_language or None,
                args.max_retries,
            )
        except YouTubeApiError as error:
            errors.append(
                {
                    "run_id": run_id,
                    "collected_at": collected_at,
                    "stage": "search",
                    "cancer_domain": term["cancer_domain"],
                    "search_query": query,
                    "video_id": "",
                    "error": str(error),
                }
            )
            print(f"  Error: {error}", file=sys.stderr)
            continue

        for rank, result in enumerate(results, start=1):
            video_id = result["video_id"]
            search_snippets.setdefault(video_id, result["snippet"])
            matches.append(
                {
                    "run_id": run_id,
                    "collected_at": collected_at,
                    "video_id": video_id,
                    "query_id": term["query_id"],
                    "cancer_domain": term["cancer_domain"],
                    "search_query": query,
                    "normalized_search_query": term["normalized_search_query"],
                    "search_rank": rank,
                    "contributor": term["contributor"],
                    "source": term["source"],
                    "scope_category": term["scope_category"],
                }
            )

    video_ids = list(search_snippets)
    try:
        video_details = retrieve_video_details(video_ids, args.max_retries) if video_ids else {}
    except YouTubeApiError as error:
        video_details = {}
        errors.append(
            {
                "run_id": run_id,
                "collected_at": collected_at,
                "stage": "video_details",
                "cancer_domain": "",
                "search_query": "",
                "video_id": "",
                "error": str(error),
            }
        )

    channel_ids = list(
        {
            detail.get("snippet", {}).get("channelId")
            for detail in video_details.values()
            if detail.get("snippet", {}).get("channelId")
        }
    )
    try:
        channel_details = (
            retrieve_channel_details(channel_ids, args.max_retries) if channel_ids else {}
        )
    except YouTubeApiError as error:
        channel_details = {}
        errors.append(
            {
                "run_id": run_id,
                "collected_at": collected_at,
                "stage": "channel_details",
                "cancer_domain": "",
                "search_query": "",
                "video_id": "",
                "error": str(error),
            }
        )

    matches_by_video: dict[str, list[dict[str, Any]]] = {}
    for match in matches:
        matches_by_video.setdefault(match["video_id"], []).append(match)

    near_duplicate_keys: dict[str, int] = {}
    for video_id in video_ids:
        detail = video_details.get(video_id, {})
        snippet = detail.get("snippet", search_snippets[video_id])
        duplicate_key = (
            f"{normalize_text(str(snippet.get('title', ''))).casefold()}|"
            f"{snippet.get('channelId', '')}"
        )
        near_duplicate_keys[duplicate_key] = near_duplicate_keys.get(duplicate_key, 0) + 1

    videos: list[dict[str, Any]] = []
    for video_id in video_ids:
        detail = video_details.get(video_id, {})
        snippet = detail.get("snippet", search_snippets[video_id])
        content = detail.get("contentDetails", {})
        statistics = detail.get("statistics", {})
        status = detail.get("status", {})
        channel_id = snippet.get("channelId", "")
        channel = channel_details.get(channel_id, {})
        channel_snippet = channel.get("snippet", {})
        channel_statistics = channel.get("statistics", {})
        video_matches = matches_by_video[video_id]
        title = str(snippet.get("title", ""))
        description = str(snippet.get("description", ""))
        caption_available = content.get("caption", "")
        normalized_title = normalize_text(title).casefold()
        near_duplicate_key = f"{normalized_title}|{channel_id}"
        transcript_status = (
            "captions_reported_available"
            if caption_available == "true"
            else "no_captions_reported"
            if detail
            else "video_metadata_unavailable"
        )

        if not detail:
            errors.append(
                {
                    "run_id": run_id,
                    "collected_at": collected_at,
                    "stage": "video_details",
                    "cancer_domain": "",
                    "search_query": "",
                    "video_id": video_id,
                    "error": "Video was returned by search but unavailable from videos.list.",
                }
            )

        videos.append(
            {
                "run_id": run_id,
                "collected_at": collected_at,
                "video_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "title": title,
                "description": description,
                "channel_id": channel_id,
                "channel_title": channel_snippet.get("title", snippet.get("channelTitle", "")),
                "channel_description": channel_snippet.get("description", ""),
                "channel_published_at": channel_snippet.get("publishedAt", ""),
                "channel_country": channel_snippet.get("country", ""),
                "channel_view_count": channel_statistics.get("viewCount", ""),
                "channel_subscriber_count": channel_statistics.get("subscriberCount", ""),
                "channel_hidden_subscriber_count": channel_statistics.get(
                    "hiddenSubscriberCount", ""
                ),
                "video_published_at": snippet.get("publishedAt", ""),
                "duration_iso8601": content.get("duration", ""),
                "duration_seconds": duration_to_seconds(content.get("duration", "")),
                "default_language": snippet.get("defaultLanguage", ""),
                "default_audio_language": snippet.get("defaultAudioLanguage", ""),
                "caption_available": caption_available,
                "transcript_status": transcript_status,
                "transcript_text": "",
                "transcript_source": "",
                "transcript_retrieval_error": "",
                "privacy_status": status.get("privacyStatus", ""),
                "made_for_kids": status.get("madeForKids", ""),
                "view_count": statistics.get("viewCount", ""),
                "like_count": statistics.get("likeCount", ""),
                "comment_count": statistics.get("commentCount", ""),
                "favorite_count": statistics.get("favoriteCount", ""),
                "metadata_available": bool(detail),
                "search_query_count": len(video_matches),
                "first_seen_query": video_matches[0]["search_query"],
                "first_seen_rank": video_matches[0]["search_rank"],
                "normalized_title": normalized_title,
                "near_duplicate_key": near_duplicate_key,
                "near_duplicate_candidate": near_duplicate_keys[near_duplicate_key] > 1,
                "search_queries": json.dumps(
                    [
                        {
                            "cancer_domain": match["cancer_domain"],
                            "search_query": match["search_query"],
                            "rank": match["search_rank"],
                            "contributor": match["contributor"],
                            "source": match["source"],
                            "scope_category": match["scope_category"],
                        }
                        for match in video_matches
                    ],
                    ensure_ascii=False,
                ),
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    query_rows = [
        {
            "run_id": run_id,
            "query_id": term["query_id"],
            "input_row": term["input_row"],
            "cancer_domain": term["cancer_domain"],
            "search_query": term["search_query"],
            "normalized_search_query": term["normalized_search_query"],
            "contributor": term["contributor"],
            "source": term["source"],
            "scope_category": term["scope_category"],
        }
        for term in selected_terms
    ]
    successful_queries = len(selected_terms) - sum(
        error["stage"] == "search" for error in errors
    )
    qa = {
        "run_id": run_id,
        "collected_at": collected_at,
        "queries_requested": len(selected_terms),
        "queries_succeeded": successful_queries,
        "query_video_matches": len(matches),
        "unique_videos": len(videos),
        "exact_duplicate_matches_removed": len(matches) - len(videos),
        "near_duplicate_candidates": sum(
            row["near_duplicate_candidate"] for row in videos
        ),
        "videos_with_metadata": sum(row["metadata_available"] for row in videos),
        "videos_reporting_captions": sum(
            row["caption_available"] == "true" for row in videos
        ),
        "videos_missing_title": sum(not row["title"] for row in videos),
        "videos_missing_description": sum(not row["description"] for row in videos),
        "errors_recorded": len(errors),
    }
    manifest = {
        "run_id": run_id,
        "collected_at": collected_at,
        "input_file": str(Path(args.input)),
        "input_sha256": hashlib.sha256(Path(args.input).read_bytes()).hexdigest(),
        "configuration": {
            "top_n": args.top_n,
            "start_at": args.start_at,
            "max_queries": args.max_queries,
            "region_code": args.region_code or None,
            "relevance_language": args.relevance_language or None,
            "max_retries": args.max_retries,
        },
        "estimated_search_quota_units": estimated_search_units,
        "outputs": [
            "queries.csv",
            "videos.csv",
            "video_query_matches.csv",
            "collection_errors.csv",
            "dataset_qa.json",
            "run_manifest.json",
        ],
    }
    write_csv(output_dir / "queries.csv", QUERY_COLUMNS, query_rows)
    write_csv(output_dir / "videos.csv", VIDEO_COLUMNS, videos)
    write_csv(output_dir / "video_query_matches.csv", MATCH_COLUMNS, matches)
    write_csv(output_dir / "collection_errors.csv", ERROR_COLUMNS, errors)
    write_json(output_dir / "dataset_qa.json", qa)
    write_json(output_dir / "run_manifest.json", manifest)
    print(
        f"Saved {len(videos)} unique videos, {len(matches)} query-video matches, "
        f"and {len(errors)} errors to {output_dir}/."
    )


if __name__ == "__main__":
    main()
