# Team Workflow

Target: **100 lung + 100 colon search terms**, **Top 10 videos** each.

## Search term ownership

| Cancer type | Members | Target per person |
|-------------|---------|-------------------|
| **Lung** | haikuan, tanay, xinhui | ~33–34 terms |
| **Colon** | yiran, yule, suzie | ~33–34 terms |

Add new rows to `search_terms/search_terms.csv` with your name in the `contributor` column.

## First-time setup

1. `python3 -m pip install -r requirements.txt`
2. Create your own YouTube Data API key — [YOUTUBE_API_KEY.md](YOUTUBE_API_KEY.md)
3. `cp .env.example .env` → add `YOUTUBE_API_KEY` → run `python3 test_youtube_api.py`

## Current progress (50 terms)

| Member | Domain | Terms now | Status |
|--------|--------|-----------|--------|
| tanay | lung | 10 | ready to collect |
| xinhui | lung | 10 | ready to collect |
| haikuan | lung | 0 | add terms first |
| yiran | colon | 10 | ready to collect |
| yule | colon | 10 | ready to collect |
| suzie | colon | 10 | ready to collect |

## Regenerate your batch file

```bash
python3 scripts/assign_collection_batches.py \
  --assignments search_terms/assignments/collection_assignments_pilot50.csv
```

Output: `search_terms/batches/<your_name>.csv`

## Collect videos (Top 10)

```bash
python3 collect_youtube_data.py \
  --input search_terms/batches/tanay.csv \
  --top-n 10 \
  --run-id batch-tanay-lung-pilot
```

Use the `expected_run_id` from `search_terms/assignments/collection_assignments_pilot50.csv`.

## After all 6 batches finish

```bash
python3 assemble_dataset.py \
  --run-ids batch-tanay-lung-pilot batch-xinhui-lung-pilot \
           batch-yiran-colon-pilot batch-yule-colon-pilot batch-suzie-colon-pilot \
  --dataset-id screening-v1
```

See `search_terms/COLLECTION_PLAN.md` for transcript splitting and handoff steps.
