"""Split a videos.csv workload into equal chunks for parallel transcript extraction."""

import argparse
import csv
import math
from pathlib import Path


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
        description="Split videos.csv into member chunks for distributed transcript extraction."
    )
    parser.add_argument("--input", required=True, help="Input videos.csv")
    parser.add_argument(
        "--processed",
        help="Optional existing videos_with_transcripts.csv; skip video_ids already present.",
    )
    parser.add_argument("--members", type=int, default=6, help="Number of team members.")
    parser.add_argument(
        "--output-dir",
        default="search_terms/batches/transcript_chunks",
        help="Directory for member transcript chunk CSV files.",
    )
    parser.add_argument(
        "--prefix",
        default="transcript_member",
        help="Filename prefix for chunk files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    columns, videos = read_csv(Path(args.input))
    if not videos:
        raise SystemExit("Input videos.csv is empty.")

    processed_ids: set[str] = set()
    processed_path = Path(args.processed) if args.processed else None
    if processed_path and processed_path.exists():
        with processed_path.open(newline="", encoding="utf-8") as file:
            processed_ids = {row["video_id"] for row in csv.DictReader(file)}

    outstanding = [video for video in videos if video["video_id"] not in processed_ids]
    if not outstanding:
        raise SystemExit("No outstanding videos to split.")

    chunk_size = math.ceil(len(outstanding) / args.members)
    output_dir = Path(args.output_dir)
    print(
        f"Outstanding videos: {len(outstanding)} "
        f"(skipping {len(processed_ids)} already processed)"
    )

    for index in range(args.members):
        start = index * chunk_size
        chunk = outstanding[start : start + chunk_size]
        if not chunk:
            continue
        member_label = f"{args.prefix}_{index + 1:02d}"
        output_path = output_dir / f"{member_label}.csv"
        write_csv(output_path, columns, chunk)
        print(f"  {member_label}: {len(chunk)} videos -> {output_path}")


if __name__ == "__main__":
    main()
