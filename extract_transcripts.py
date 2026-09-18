"""Enrich a collected YouTube dataset with available public transcripts.

This module uses youtube-transcript-api, an unofficial public-transcript client.
It does not use YouTube Data API quota and must not be used to bypass access controls.
"""

import argparse
import csv
import random
import sys
import time
from pathlib import Path
from typing import Any

import requests
from youtube_transcript_api import YouTubeTranscriptApi

# Transcript text can exceed the default CSV field limit when resuming a large run.
csv.field_size_limit(sys.maxsize)


class TimeoutSession(requests.Session):
    """A session that applies a default timeout so one video cannot stall the run."""

    def __init__(self, timeout: float) -> None:
        super().__init__()
        self.timeout = timeout

    def request(self, *args: Any, **kwargs: Any) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        return super().request(*args, **kwargs)


TRANSCRIPT_COLUMNS = [
    "transcript_text",
    "transcript_text_normalized",
    "transcript_segment_count",
    "transcript_language",
    "transcript_is_generated",
    "transcript_is_translated",
    "transcript_source",
    "transcript_status",
    "transcript_retrieval_error",
]
ERROR_COLUMNS = ["video_id", "transcript_status", "error"]
RETRIEVED_STATUSES = ("public_transcript_retrieved", "translated_public_transcript")
# A block applies to the whole IP, so every later video would be recorded as a false
# "no transcript" result rather than a retrieval failure.
BLOCKING_ERRORS = (
    "IpBlocked",
    "RequestBlocked",
    "YouTubeRequestFailed",
    "PoTokenRequired",
)


def normalize_text(value: str) -> str:
    return " ".join(value.split())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Retrieve publicly available YouTube transcripts for a collected video CSV."
    )
    parser.add_argument("--input", required=True, help="Input videos.csv from a collection run.")
    parser.add_argument(
        "--output",
        help="Output enriched CSV. Defaults to videos_with_transcripts.csv beside the input.",
    )
    parser.add_argument(
        "--error-output",
        help="Output failure CSV. Defaults to transcript_errors.csv beside the input.",
    )
    parser.add_argument(
        "--languages",
        default="en,en-US,en-GB",
        help="Comma-separated transcript language preference order.",
    )
    parser.add_argument(
        "--translate-to-en",
        action="store_true",
        help=(
            "Translate an available non-English transcript to English when no preferred "
            "transcript exists. This spends a second request on every video that fails, so "
            "leave it off for corpora that are already English."
        ),
    )
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=1.0,
        help=(
            "Minimum delay between videos. The actual wait is randomized up to twice this "
            "value, because evenly spaced requests are easier to identify as automated "
            "(default: 1.0)."
        ),
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=1,
        help="Retries per video for transient failures (default: 1).",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=20.0,
        help="Per-request network timeout (default: 20.0).",
    )
    parser.add_argument(
        "--max-consecutive-failures",
        type=int,
        default=15,
        help=(
            "Stop after this many videos fail in a row. Most videos in a healthy run return "
            "a transcript, so a long streak usually means YouTube started refusing requests "
            "without reporting a block (default: 15)."
        ),
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Keep rows already written to the output file and process only the remaining videos.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Discard an existing output file instead of resuming it.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        help=(
            "How many outstanding videos to process in this run. Videos already written to "
            "the output file do not count towards it."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate input and print the extraction plan without requesting transcripts.",
    )
    return parser.parse_args()


def read_videos(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or "video_id" not in reader.fieldnames:
            raise ValueError("Input CSV must contain a video_id column.")
        return reader.fieldnames, list(reader)


def is_blocking_error(error: Exception) -> bool:
    """Report whether YouTube refused the request because the IP itself is blocked."""
    return type(error).__name__ in BLOCKING_ERRORS


def is_transient_error(error: Exception) -> bool:
    """Report whether a retry can plausibly succeed.

    A missing, disabled, or untranslatable transcript is a property of the video, so
    retrying only spends another request against the rate limit.
    """
    return isinstance(error, requests.exceptions.RequestException)


def read_processed_rows(path: Path, columns: list[str]) -> tuple[set[str], int]:
    """Return the video IDs already written and how many of them carry a transcript.

    A row left partial by a hard stop is discarded first.

    Rows are flushed individually, so an interrupted run can leave the final row cut off
    mid-write. Appending after it would merge two videos into one malformed record.
    """
    if not path.exists() or path.stat().st_size == 0:
        return set(), 0

    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        try:
            header = next(reader)
        except StopIteration:
            return set(), 0
        if header != columns:
            raise SystemExit(
                f"{path} uses a different column layout, so appended rows would not line up "
                "with it. Choose a new --output path or delete the existing file."
            )
        rows: list[list[str]] = []
        complete = True
        try:
            for row in reader:
                if len(row) == len(columns):
                    rows.append(row)
                else:
                    complete = False
        except csv.Error:
            complete = False

    if not complete:
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            writer.writerows(rows)
        print(f"Repaired {path}: dropped a row left incomplete by an interrupted run.")

    video_id_index = columns.index("video_id")
    status_index = columns.index("transcript_status")
    processed = {row[video_id_index] for row in rows if row[video_id_index]}
    retrieved = sum(1 for row in rows if row[status_index] in RETRIEVED_STATUSES)
    return processed, retrieved


def transcript_to_fields(
    transcript: Any, *, translated: bool, source_language: str | None = None
) -> dict[str, Any]:
    segments = transcript.to_raw_data()
    text = " ".join(str(segment.get("text", "")) for segment in segments)
    return {
        "transcript_text": text,
        "transcript_text_normalized": normalize_text(text),
        "transcript_segment_count": len(segments),
        "transcript_language": transcript.language_code,
        "transcript_is_generated": transcript.is_generated,
        "transcript_is_translated": translated,
        "transcript_source": "youtube_transcript_api",
        "transcript_status": (
            "translated_public_transcript"
            if translated
            else "public_transcript_retrieved"
        ),
        "transcript_retrieval_error": "",
        "transcript_original_language": source_language or transcript.language_code,
    }


def fetch_transcript(
    api: YouTubeTranscriptApi, video_id: str, languages: list[str], translate_to_en: bool
) -> dict[str, Any]:
    """Fetch a preferred-language transcript, optionally using YouTube translation."""
    try:
        return transcript_to_fields(api.fetch(video_id, languages=languages), translated=False)
    except Exception as preferred_error:
        if not translate_to_en or is_blocking_error(preferred_error):
            raise preferred_error

        try:
            transcript_list = api.list(video_id)
            for transcript in transcript_list:
                if transcript.is_translatable:
                    translated = transcript.translate("en").fetch()
                    return transcript_to_fields(
                        translated,
                        translated=True,
                        source_language=transcript.language_code,
                    )
        except Exception:
            # A failed fallback must not hide why the preferred request failed.
            raise preferred_error from None
        raise preferred_error


def main() -> None:
    args = parse_args()
    if args.delay_seconds < 0 or args.max_retries < 0:
        raise SystemExit("--delay-seconds and --max-retries must be zero or greater.")
    if args.batch_size is not None and args.batch_size < 1:
        raise SystemExit("--batch-size must be at least 1.")

    input_path = Path(args.input)
    try:
        columns, videos = read_videos(input_path)
    except (OSError, ValueError) as error:
        raise SystemExit(f"Cannot read input dataset: {error}") from error

    if not videos:
        raise SystemExit("The input dataset contains no videos.")

    languages = [language.strip() for language in args.languages.split(",") if language.strip()]
    if not languages:
        raise SystemExit("Provide at least one language code with --languages.")

    output_path = Path(args.output) if args.output else input_path.with_name("videos_with_transcripts.csv")
    error_path = (
        Path(args.error_output) if args.error_output else input_path.with_name("transcript_errors.csv")
    )
    output_columns = columns + [
        field
        for field in TRANSCRIPT_COLUMNS + ["transcript_original_language"]
        if field not in columns
    ]
    if (
        output_path.exists()
        and output_path.stat().st_size > 0
        and not (args.resume or args.overwrite)
    ):
        raise SystemExit(
            f"{output_path} already holds results. Pass --resume to continue that run, or "
            "--overwrite to discard it and start over."
        )

    processed_ids, previously_retrieved = (
        read_processed_rows(output_path, output_columns) if args.resume else (set(), 0)
    )
    outstanding = [video for video in videos if video["video_id"] not in processed_ids]
    pending = outstanding[: args.batch_size] if args.batch_size else outstanding

    print(
        f"Corpus: {len(videos)} videos; preferred languages: {', '.join(languages)}. "
        "This process does not call the YouTube Data API."
    )
    if processed_ids:
        print(
            f"Already written: {len(processed_ids)} videos, {previously_retrieved} with a "
            "transcript."
        )
    if not pending:
        print(f"Every video in {input_path} already has a row in {output_path}.")
        return
    print(
        f"This batch covers {len(pending)} of {len(outstanding)} outstanding videos."
    )
    if args.dry_run:
        print("Dry run passed. No transcript request was made.")
        return

    api = YouTubeTranscriptApi(http_client=TimeoutSession(args.timeout_seconds))
    append_output = bool(processed_ids)
    append_errors = append_output and error_path.exists()
    written = 0
    failures = 0
    consecutive_failures = 0

    with (
        output_path.open("a" if append_output else "w", newline="", encoding="utf-8") as output_file,
        error_path.open("a" if append_errors else "w", newline="", encoding="utf-8") as error_file,
    ):
        output_writer = csv.DictWriter(output_file, fieldnames=output_columns, extrasaction="ignore")
        error_writer = csv.DictWriter(error_file, fieldnames=ERROR_COLUMNS, extrasaction="ignore")
        if not append_output:
            output_writer.writeheader()
        if not append_errors:
            error_writer.writeheader()

        for index, video in enumerate(pending, start=1):
            video_id = video["video_id"]
            print(f"[{index}/{len(pending)}] Transcript: {video_id}", flush=True)
            fields: dict[str, Any] | None = None
            error_message = ""
            blocked = False
            for attempt in range(args.max_retries + 1):
                try:
                    fields = fetch_transcript(api, video_id, languages, args.translate_to_en)
                    break
                except Exception as error:  # Library error types are version-specific.
                    error_message = f"{type(error).__name__}: {error}"
                    blocked = is_blocking_error(error)
                    if blocked or not is_transient_error(error):
                        break
                    if attempt < args.max_retries:
                        time.sleep(2**attempt)

            if blocked:
                raise SystemExit(
                    f"Stopped at {video_id}: YouTube is blocking this IP. "
                    f"Corpus progress: {len(processed_ids) + written}/{len(videos)} videos "
                    "processed. Rerun with --resume once access returns.\n"
                    f"{error_message}"
                )

            if fields is None:
                fields = {
                    "transcript_text": "",
                    "transcript_text_normalized": "",
                    "transcript_segment_count": 0,
                    "transcript_language": "",
                    "transcript_is_generated": "",
                    "transcript_is_translated": "",
                    "transcript_source": "",
                    "transcript_status": "transcript_unavailable",
                    "transcript_retrieval_error": error_message,
                    "transcript_original_language": "",
                }
                error_writer.writerow(
                    {
                        "video_id": video_id,
                        "transcript_status": fields["transcript_status"],
                        "error": error_message,
                    }
                )
                error_file.flush()
                failures += 1
                consecutive_failures += 1
            else:
                consecutive_failures = 0

            output_writer.writerow({**video, **fields})
            output_file.flush()
            written += 1

            if consecutive_failures >= args.max_consecutive_failures:
                raise SystemExit(
                    f"Stopped at {video_id} after {consecutive_failures} consecutive failures. "
                    f"Corpus progress: {len(processed_ids) + written}/{len(videos)} videos "
                    f"processed. Review {error_path} before rerunning with --resume, because a "
                    "streak this long is rarely caused by the videos themselves."
                )

            if index < len(pending) and args.delay_seconds:
                time.sleep(random.uniform(args.delay_seconds, args.delay_seconds * 2))

    total_processed = len(processed_ids) + written
    total_retrieved = previously_retrieved + (written - failures)
    print(
        f"Finished this batch: {written - failures} of {written} videos returned a transcript.\n"
        f"Corpus progress: {total_processed}/{len(videos)} videos processed, "
        f"{total_retrieved} with a transcript, {len(videos) - total_processed} outstanding.\n"
        f"Transcript output: {output_path}"
    )


if __name__ == "__main__":
    main()
