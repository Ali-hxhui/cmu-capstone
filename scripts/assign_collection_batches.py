"""Split search_terms/search_terms.csv into per-member batch files for parallel collection."""

import argparse
import csv
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
    parser = argparse.ArgumentParser(description="Create per-member search term batch CSV files.")
    parser.add_argument(
        "--input",
        default="search_terms/search_terms.csv",
        help="Master search term CSV.",
    )
    parser.add_argument(
        "--assignments",
        default="search_terms/assignments/collection_assignments.csv",
        help="Member assignment table with cancer_domain, start_at, and max_queries.",
    )
    parser.add_argument(
        "--output-dir",
        default="search_terms/batches",
        help="Directory for per-member batch CSV files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    assignment_path = Path(args.assignments)
    output_dir = Path(args.output_dir)

    columns, terms = read_csv(input_path)
    _, assignments = read_csv(assignment_path)
    if not terms:
        raise SystemExit(f"No search terms found in {input_path}")
    if not assignments:
        raise SystemExit(f"No assignments found in {assignment_path}")

    domain_counts: dict[str, int] = {}
    for row in terms:
        domain = row["cancer_domain"].strip().lower()
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

    print(f"Master file: {len(terms)} search terms ({domain_counts})")
    for row in assignments:
        member_id = row["member_id"]
        domain = row["cancer_domain"].strip().lower()
        start_at = int(row["start_at"])
        max_queries = int(row["max_queries"])
        domain_terms = [
            term for term in terms if term["cancer_domain"].strip().lower() == domain
        ]
        batch = domain_terms[start_at : start_at + max_queries] if max_queries else []
        if not batch:
            print(f"  {member_id} ({domain}): skipped (0 terms in slice)")
            continue
        output_path = output_dir / f"{member_id}.csv"
        write_csv(output_path, columns, batch)
        print(
            f"  {member_id} ({domain}): slice {start_at + 1}-{start_at + len(batch)} "
            f"of {len(domain_terms)} ({len(batch)} terms) -> {output_path}"
        )
        if max_queries and len(batch) < max_queries:
            print(
                f"    warning: expected {max_queries} {domain} terms but only "
                f"{len(domain_terms)} exist in master file"
            )


if __name__ == "__main__":
    main()
