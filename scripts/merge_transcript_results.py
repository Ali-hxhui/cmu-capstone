"""Merge distributed transcript extraction outputs into one videos_with_transcripts.csv."""

import argparse
import csv
import sys
from pathlib import Path


csv.field_size_limit(sys.maxsize)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        return reader.fieldnames or [], list(reader)


def write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge base and chunk transcript CSVs by video_id."
    )
    parser.add_argument(
        "--base",
        help="Existing partial videos_with_transcripts.csv to keep.",
    )
    parser.add_argument(
        "--chunks",
        nargs="+",
        required=True,
        help="One or more chunk videos_with_transcripts.csv files.",
    )
    parser.add_argument("--output", required=True, help="Merged output CSV path.")
    parser.add_argument(
        "--errors-output",
        help="Optional merged transcript_errors.csv path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    merged: dict[str, dict[str, str]] = {}
    columns: list[str] = []

    if args.base:
        base_columns, base_rows = read_csv(Path(args.base))
        columns = base_columns
        for row in base_rows:
            merged[row["video_id"]] = row

    for chunk_path in args.chunks:
        chunk_columns, chunk_rows = read_csv(Path(chunk_path))
        if not columns:
            columns = chunk_columns
        for row in chunk_rows:
            merged[row["video_id"]] = row

    rows = [merged[video_id] for video_id in sorted(merged)]
    write_csv(Path(args.output), columns, rows)
    print(f"Merged {len(rows)} videos -> {args.output}")

    if args.errors_output:
        error_rows: list[dict[str, str]] = []
        error_columns = ["video_id", "transcript_status", "error"]
        for chunk_path in args.chunks:
            error_path = Path(chunk_path).with_name("transcript_errors.csv")
            if not error_path.exists():
                error_path = Path(str(chunk_path).replace(".csv", "_errors.csv"))
            if error_path.exists():
                _, chunk_errors = read_csv(error_path)
                error_rows.extend(chunk_errors)
        if args.base:
            base_errors = Path(args.base).with_name("transcript_errors.csv")
            if base_errors.exists():
                _, base_error_rows = read_csv(base_errors)
                error_rows = base_error_rows + error_rows
        deduped = {row["video_id"]: row for row in error_rows}
        write_csv(Path(args.errors_output), error_columns, list(deduped.values()))
        print(f"Merged {len(deduped)} error rows -> {args.errors_output}")


if __name__ == "__main__":
    main()
