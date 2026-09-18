"""Merge versioned collection runs into one downstream-ready dataset without API calls."""

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        return reader.fieldnames or [], list(reader)


def write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge data/runs/<run-id> outputs into a single curated dataset."
    )
    parser.add_argument("--runs-dir", default="data/runs", help="Parent directory containing runs.")
    parser.add_argument(
        "--run-ids",
        nargs="+",
        help="Specific run IDs to merge. Defaults to every complete run directory.",
    )
    parser.add_argument(
        "--dataset-id",
        default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        help="Identifier for the output dataset directory.",
    )
    parser.add_argument(
        "--output-dir", default="data/curated", help="Parent directory for curated datasets."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    runs_dir = Path(args.runs_dir)
    if not runs_dir.exists():
        raise SystemExit(f"Runs directory does not exist: {runs_dir}")

    expected_files = {"queries.csv", "videos.csv", "video_query_matches.csv"}
    candidate_dirs = (
        [runs_dir / run_id for run_id in args.run_ids]
        if args.run_ids
        else sorted(path for path in runs_dir.iterdir() if path.is_dir())
    )
    run_dirs = [path for path in candidate_dirs if expected_files <= {file.name for file in path.iterdir()}]
    if not run_dirs:
        raise SystemExit("No complete collection runs were found.")

    output_dir = Path(args.output_dir) / args.dataset_id
    if output_dir.exists():
        raise SystemExit(f"Dataset directory already exists: {output_dir}")

    video_columns: list[str] = []
    query_columns: list[str] = []
    match_columns: list[str] = []
    error_columns: list[str] = []
    videos_by_id: dict[str, dict[str, str]] = {}
    video_runs: defaultdict[str, set[str]] = defaultdict(set)
    matches_by_key: dict[tuple[str, str], dict[str, str]] = {}
    queries_by_key: dict[tuple[str, str], dict[str, str]] = {}
    errors: list[dict[str, str]] = []

    for run_dir in run_dirs:
        current_video_columns, videos = read_csv(run_dir / "videos.csv")
        current_query_columns, queries = read_csv(run_dir / "queries.csv")
        current_match_columns, matches = read_csv(run_dir / "video_query_matches.csv")
        if not video_columns:
            video_columns = current_video_columns
            query_columns = current_query_columns
            match_columns = current_match_columns
        for video in videos:
            video_id = video["video_id"]
            video_runs[video_id].add(video["run_id"])
            existing = videos_by_id.get(video_id)
            if not existing or video["collected_at"] > existing["collected_at"]:
                videos_by_id[video_id] = video
        for match in matches:
            key = (match["video_id"], match["normalized_search_query"])
            matches_by_key.setdefault(key, match)
        for query in queries:
            key = (query["cancer_domain"], query["normalized_search_query"])
            queries_by_key.setdefault(key, query)

        error_path = run_dir / "collection_errors.csv"
        if error_path.exists():
            current_error_columns, current_errors = read_csv(error_path)
            if not error_columns:
                error_columns = current_error_columns
            errors.extend(current_errors)

    matches = list(matches_by_key.values())
    matches.sort(key=lambda row: (row["cancer_domain"], row["normalized_search_query"], int(row["search_rank"])))
    matches_by_video: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for match in matches:
        matches_by_video[match["video_id"]].append(match)

    videos = []
    for video_id, video in videos_by_id.items():
        video_matches = matches_by_video[video_id]
        video["source_run_ids"] = json.dumps(sorted(video_runs[video_id]))
        video["search_query_count"] = len(video_matches)
        if video_matches:
            video["first_seen_query"] = video_matches[0]["search_query"]
            video["first_seen_rank"] = video_matches[0]["search_rank"]
            video["search_queries"] = json.dumps(
                [
                    {
                        "query_id": match["query_id"],
                        "cancer_domain": match["cancer_domain"],
                        "search_query": match["search_query"],
                        "rank": int(match["search_rank"]),
                    }
                    for match in video_matches
                ],
                ensure_ascii=False,
            )
        videos.append(video)
    videos.sort(key=lambda row: row["video_id"])

    output_dir.mkdir(parents=True)
    write_csv(output_dir / "queries.csv", query_columns, list(queries_by_key.values()))
    write_csv(output_dir / "videos.csv", video_columns + ["source_run_ids"], videos)
    write_csv(output_dir / "video_query_matches.csv", match_columns, matches)
    write_csv(output_dir / "collection_errors.csv", error_columns, errors)
    write_json(
        output_dir / "dataset_manifest.json",
        {
            "dataset_id": args.dataset_id,
            "assembled_at": datetime.now(timezone.utc).isoformat(),
            "source_run_ids": [path.name for path in run_dirs],
            "query_count": len(queries_by_key),
            "unique_video_count": len(videos),
            "query_video_match_count": len(matches),
            "errors_carried_forward": len(errors),
        },
    )
    print(
        f"Assembled {len(run_dirs)} run(s): {len(queries_by_key)} queries, "
        f"{len(videos)} unique videos, and {len(matches)} query-video matches in {output_dir}/."
    )


if __name__ == "__main__":
    main()
