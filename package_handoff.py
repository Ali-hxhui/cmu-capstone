"""Package a curated dataset into data/runs/<handoff-id>/ for downstream LLM eval (Tanay's repo)."""

import argparse
import csv
import json
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

csv.field_size_limit(sys.maxsize)

RETRIEVED_STATUSES = {"public_transcript_retrieved", "translated_public_transcript"}

HANDOFF_FILES = (
    "queries.csv",
    "videos.csv",
    "video_query_matches.csv",
    "videos_with_transcripts.csv",
    "collection_errors.csv",
    "transcript_errors.csv",
    "dataset_manifest.json",
    "dataset_qa.json",
    "search_terms.csv",
    "DATA_CONTRACT.md",
)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        return reader.fieldnames or [], list(reader)


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Copy a curated dataset into data/runs/<handoff-id>/ in the layout expected by "
            "the downstream AHN-youtube-videos evaluator (RUN_ID=<handoff-id>)."
        )
    )
    parser.add_argument(
        "--curated",
        required=True,
        help="Curated dataset directory, e.g. data/curated/screening-v1",
    )
    parser.add_argument(
        "--handoff-id",
        required=True,
        help="Output folder name under data/runs/, used as RUN_ID downstream.",
    )
    parser.add_argument(
        "--runs-dir",
        default="data/runs",
        help="Parent directory for the packaged handoff folder.",
    )
    parser.add_argument(
        "--transcripts",
        help="Path to videos_with_transcripts.csv (default: <curated>/videos_with_transcripts.csv).",
    )
    parser.add_argument(
        "--search-terms",
        default="search_terms/search_terms.csv",
        help="Search terms CSV to include in the handoff package.",
    )
    parser.add_argument(
        "--data-contract",
        default="DATA_CONTRACT.md",
        help="Data contract markdown to copy into the handoff package.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing handoff directory.",
    )
    return parser.parse_args()


def require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"Missing required {label}: {path}")


def copy_file(source: Path, destination: Path) -> None:
    shutil.copy2(source, destination)


def build_dataset_qa(
    curated_dir: Path,
    handoff_id: str,
    transcript_path: Path,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    _, matches = read_csv(curated_dir / "video_query_matches.csv")
    _, videos = read_csv(transcript_path)
    _, queries = read_csv(curated_dir / "queries.csv")

    status_counts = Counter(row.get("transcript_status") or "" for row in videos)
    retrieved = sum(1 for row in videos if row.get("transcript_status") in RETRIEVED_STATUSES)
    unavailable = sum(
        1 for row in videos if row.get("transcript_status") == "transcript_unavailable"
    )
    near_duplicate_candidates = sum(
        1 for row in videos if str(row.get("near_duplicate_candidate", "")).lower() == "true"
    )

    qa: dict[str, Any] = {
        "handoff_id": handoff_id,
        "handoff_at": datetime.now(timezone.utc).isoformat(),
        "downstream_run_id": handoff_id,
        "source_dataset": curated_dir.name,
        "source_run_ids": manifest.get("source_run_ids", []),
        "queries_requested": len(queries),
        "queries_succeeded": len(queries),
        "query_video_matches": len(matches),
        "unique_videos": len(videos),
        "exact_duplicate_matches_removed": len(matches) - len(videos),
        "near_duplicate_candidates": near_duplicate_candidates,
        "videos_with_metadata": sum(
            1 for row in videos if str(row.get("metadata_available", "")).lower() == "true"
        ),
        "videos_reporting_captions": sum(
            1 for row in videos if str(row.get("caption_available", "")).lower() == "true"
        ),
        "videos_missing_title": sum(1 for row in videos if not (row.get("title") or "").strip()),
        "videos_missing_description": sum(
            1 for row in videos if not (row.get("description") or "").strip()
        ),
        "errors_recorded": manifest.get("errors_carried_forward", 0),
        "transcripts_retrieved": retrieved,
        "transcripts_unavailable": unavailable,
        "transcript_status_counts": dict(sorted(status_counts.items())),
        "transcript_success_rate_pct": round(100 * retrieved / len(videos), 1) if videos else 0.0,
        "transcript_note": (
            "Handoff package for AHN-youtube-videos. "
            "Set RUN_ID to handoff_id and point data/runs/<handoff_id>/ at this folder."
        ),
    }
    return qa


def main() -> None:
    args = parse_args()
    curated_dir = Path(args.curated)
    if not curated_dir.is_dir():
        raise SystemExit(f"Curated directory does not exist: {curated_dir}")

    for name in ("queries.csv", "videos.csv", "video_query_matches.csv", "dataset_manifest.json"):
        require_file(curated_dir / name, name)

    transcript_path = Path(args.transcripts) if args.transcripts else curated_dir / "videos_with_transcripts.csv"
    require_file(transcript_path, "videos_with_transcripts.csv")

    output_dir = Path(args.runs_dir) / args.handoff_id
    if output_dir.exists():
        if not args.force:
            raise SystemExit(
                f"Handoff directory already exists: {output_dir}. Use --force to replace it."
            )
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    copy_file(curated_dir / "queries.csv", output_dir / "queries.csv")
    copy_file(curated_dir / "videos.csv", output_dir / "videos.csv")
    copy_file(curated_dir / "video_query_matches.csv", output_dir / "video_query_matches.csv")
    copy_file(transcript_path, output_dir / "videos_with_transcripts.csv")

    collection_errors = curated_dir / "collection_errors.csv"
    if collection_errors.exists():
        copy_file(collection_errors, output_dir / "collection_errors.csv")

    transcript_errors = transcript_path.with_name("transcript_errors.csv")
    if not transcript_errors.exists():
        transcript_errors = curated_dir / "transcript_errors.csv"
    if transcript_errors.exists():
        copy_file(transcript_errors, output_dir / "transcript_errors.csv")

    copy_file(curated_dir / "dataset_manifest.json", output_dir / "dataset_manifest.json")

    manifest = json.loads((curated_dir / "dataset_manifest.json").read_text(encoding="utf-8"))
    qa = build_dataset_qa(curated_dir, args.handoff_id, transcript_path, manifest)
    write_json(output_dir / "dataset_qa.json", qa)

    search_terms = Path(args.search_terms)
    if search_terms.exists():
        copy_file(search_terms, output_dir / "search_terms.csv")

    data_contract = Path(args.data_contract)
    if data_contract.exists():
        copy_file(data_contract, output_dir / "DATA_CONTRACT.md")

    present = [name for name in HANDOFF_FILES if (output_dir / name).exists()]
    print(f"Packaged handoff -> {output_dir}/")
    print(f"  Files: {', '.join(present)}")
    print(
        f"  Downstream: RUN_ID={args.handoff_id} python -m src.run_eval "
        f"(in AHN-youtube-videos repo)"
    )


if __name__ == "__main__":
    main()
