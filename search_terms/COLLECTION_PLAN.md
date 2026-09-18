# Search Terms & Collection Plan

## Target corpus

| Item | Target | Current (2026-09-17) |
|------|--------|----------------------|
| Lung search terms | 100 | 20 |
| Colon search terms | 100 | 30 |
| **Total search terms** | **200** | **50** |
| Videos per query | **Top 10** | Pilot used Top 20 |
| Max query–video matches | 2,000 | 1,000 (50 × 20 pilot) |
| Estimated unique videos | ~1,200–1,600 (after dedup) | 785 (pilot) |

## Files

| File | Purpose |
|------|---------|
| `search_terms.csv` | Master list — edit this as terms are finalized |
| `poc-handoff.csv` | 10-term POC subset |
| `assignments/collection_assignments.csv` | Six-way split for 200 terms |
| `batches/` | Generated per-member slices (gitignored output) |

## Team split by cancer type

| Domain | Members | Target each |
|--------|---------|-------------|
| Lung | haikuan, tanay, xinhui | ~34 / 33 / 33 |
| Colon | yiran, yule, suzie | ~34 / 33 / 33 |

Regenerate batch CSVs:

```bash
# Current 50 terms
python3 scripts/assign_collection_batches.py \
  --assignments search_terms/assignments/collection_assignments_pilot50.csv

# Final 200 terms
python3 scripts/assign_collection_batches.py
```

Final assignment (within each domain):

| Member | Domain | start_at | max_queries | run_id |
|--------|--------|----------|-------------|--------|
| haikuan | lung | 0 | 34 | batch-haikuan-lung-001 |
| tanay | lung | 34 | 33 | batch-tanay-lung-001 |
| xinhui | lung | 67 | 33 | batch-xinhui-lung-001 |
| yiran | colon | 0 | 34 | batch-yiran-colon-001 |
| yule | colon | 34 | 33 | batch-yule-colon-001 |
| suzie | colon | 67 | 33 | batch-suzie-colon-001 |

## Collection command (per member)

Use **Top 10** for the final corpus:

```bash
python3 collect_youtube_data.py \
  --input search_terms/batches/tanay.csv \
  --top-n 10 \
  --run-id batch-tanay-lung-pilot
```

## Quota planning

- ~100 quota units per search query
- 200 queries ≈ **20,000 units** total
- Default daily budget ≈ 10,000 → split across **2+ days** and **6 people**
- Each member’s batch (33–34 queries) ≈ **3,300–3,400 units/day**

## After collection

1. Upload each `data/runs/<run-id>/` folder to the shared drive
2. Merge locally:

```bash
python3 assemble_dataset.py \
  --run-ids batch-member_01-001 batch-member_02-001 ... \
  --dataset-id screening-v1
```

3. Split transcript workload:

```bash
python3 scripts/split_transcript_workload.py \
  --input data/curated/screening-v1/videos.csv \
  --members 6
```

4. Each member extracts transcripts on their chunk, then merge:

```bash
python3 scripts/merge_transcript_results.py \
  --base data/runs/full-corpus-001/videos_with_transcripts.csv \
  --chunks data/team_transcripts/member_*.csv \
  --output data/curated/screening-v1/videos_with_transcripts.csv
```

5. Package for downstream LLM eval (Tanay's `RUN_ID` folder):

```bash
python3 package_handoff.py \
  --curated data/curated/screening-v1 \
  --handoff-id screening-v1
```

Share `data/runs/screening-v1/` — same layout as `poc-handoff-v1`.

## Pilot data already collected

- `full-corpus-001`: 50 queries, Top 20, 785 unique videos
- Transcript progress: see `data/curated/full-corpus-v1/dataset_qa.json`
- Decide in meeting: **keep pilot as dev set** or **re-collect at Top 10** when all 200 terms are ready
