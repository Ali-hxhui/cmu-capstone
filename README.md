# CMU Cancer Screening Video Analytics

YouTube metadata and transcript pipeline for AHN lung + colon cancer screening education.

Needs **Python 3.10+**. Each person uses their own YouTube Data API key.

```
Search terms → collect (API key) → extract transcripts (no API key) → upload run folder
```

**Docs:** [TEAM_WORKFLOW.md](TEAM_WORKFLOW.md) (who runs what) · [YOUTUBE_API_KEY.md](YOUTUBE_API_KEY.md) · [PIPELINE_GUIDE.md](PIPELINE_GUIDE.md) · [DATA_CONTRACT.md](DATA_CONTRACT.md)

`data/` is gitignored. After you collect, upload `data/runs/<run-id>/` to the Shared Folder.

## Day-1 run (every member)

Replace `<your_name>` and the `--run-id` with values from
`search_terms/assignments/collection_assignments_current.csv`. `--run-id` must be unique.

```bash
git clone https://github.com/Ali-hxhui/cmu-capstone.git
cd cmu-capstone
python3 -m pip install -r requirements.txt
cp .env.example .env
# Put your key in .env — see YOUTUBE_API_KEY.md
python3 test_youtube_api.py

python3 scripts/assign_collection_batches.py \
  --assignments search_terms/assignments/collection_assignments_current.csv

python3 collect_youtube_data.py \
  --input search_terms/batches/<your_name>.csv \
  --top-n 10 \
  --run-id batch-<your_name>-<lung|colon>-pilot

python3 extract_transcripts.py \
  --input data/runs/batch-<your_name>-<lung|colon>-pilot/videos.csv \
  --resume --batch-size 50 --delay-seconds 5
```

`assign_collection_batches.py` creates `search_terms/batches/` (not in git). Collection writes `videos.csv`; transcript extraction cannot run until that file exists.

Leave `--translate-to-en` off. If YouTube blocks the IP, stop and resume later — do not retry immediately.

If `search_terms/search_terms.csv` is updated on GitHub: `git pull origin main`, regenerate batches, then collect again.

No batch file / “skipped (0 terms)” means you have no rows in the current master list yet. Wait for the next term-list update.

Optional dry-run (no API calls):

```bash
python3 collect_youtube_data.py --top-n 10 --max-queries 2 --run-id test-001 --dry-run
```

Merge and downstream package: [TEAM_WORKFLOW.md](TEAM_WORKFLOW.md).

## What you need vs later

| Day 1 | Later / not required to extract |
|-------|----------------------------------|
| `collect_youtube_data.py`, `extract_transcripts.py`, `test_youtube_api.py` | `assemble_dataset.py`, `package_handoff.py` |
| `scripts/assign_collection_batches.py` | `scripts/split_transcript_workload.py`, `scripts/merge_transcript_results.py` |
| `search_terms/search_terms.csv` + `assignments/collection_assignments_current.csv` | `assignments/collection_assignments.csv` (200-term split) |
| `requirements.txt`, `.env.example` | [archive/](archive/) (old POC list and target counts) |
