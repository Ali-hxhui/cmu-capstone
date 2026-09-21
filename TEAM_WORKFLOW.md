# Team Workflow

Target: **100 lung + 100 colon** search terms, **Top 10** videos each. Current master file: **50 terms** (20 lung, 30 colon).

Repo: https://github.com/Ali-hxhui/cmu-capstone

## Where things live

| What | Where | Who |
|------|--------|-----|
| Code and English docs | **GitHub** | Xinhui maintains; others clone / pull |
| Search terms | `search_terms/search_terms.csv` | Edit locally; send updates to Xinhui |
| Collection / transcript CSVs | **Shared Folder** (`data/` is gitignored) | Each member uploads their run folder |
| API keys | Local `.env` | One key per person |
| Personal notes | `local/` (gitignored) | Keep off GitHub |

Teammates do **not** need to push. Clone, run locally, upload results.

### GitHub vs Shared Folder

Tracked: Python scripts, `search_terms/` master + assignments, English docs, `requirements.txt`, `.env.example`.

Not tracked: `.env`, `data/`, generated `search_terms/batches/*.csv`, `.venv/`, `local/`, PDFs / Office files.

Suggested access: Xinhui **Admin**, others **Read**. Grant **Write** only if the team will edit `search_terms.csv` on GitHub. Then `git pull` before editing, and only one person should change the master file at a time.

## Ownership

| Domain | Members | Target each (200-term plan) | Current 50-term status |
|--------|---------|-----------------------------|------------------------|
| Lung | haikuan, tanay, xinhui | ~33–34 | tanay 10, xinhui 10 ready; haikuan 0 (add terms first) |
| Colon | yiran, yule, suzie | ~33–34 | 10 each, ready to collect |

Use your name in `contributor`. New terms: copy a row from `search_terms/search_terms.template.csv`, set `cancer_domain` to `lung` or `colon`, keep lung rows together then colon rows.

Assignment tables:

| File | When |
|------|------|
| `search_terms/assignments/collection_assignments_pilot50.csv` | Current 50 terms |
| `search_terms/assignments/collection_assignments.csv` | Final 200-term split |

`search_terms/poc-handoff.csv` is the older 10-term POC list, not the working master.

## First-time setup

```bash
git clone https://github.com/Ali-hxhui/cmu-capstone.git
cd cmu-capstone
python3 -m pip install -r requirements.txt
cp .env.example .env
# Add YOUTUBE_API_KEY — see YOUTUBE_API_KEY.md
python3 test_youtube_api.py
```

Later: `git pull origin main` when scripts or docs change.

## Collect (every member)

```bash
python3 scripts/assign_collection_batches.py \
  --assignments search_terms/assignments/collection_assignments_pilot50.csv
```

That writes `search_terms/batches/<your_name>.csv`. Then collect with a **unique** `--run-id` (use `expected_run_id` from the assignments file):

```bash
python3 collect_youtube_data.py \
  --input search_terms/batches/tanay.csv \
  --top-n 10 \
  --run-id batch-tanay-lung-pilot
```

When the 200-term list is ready, regenerate batches without `--assignments` (defaults to `collection_assignments.csv`) and use `--top-n 10`.

**Quota:** each query ≈ 100 units. 200 queries ≈ 20,000 units. Default daily budget ≈ 10,000, so split across people and days. A 33–34 query batch ≈ 3,300–3,400 units.

Upload the whole folder `data/runs/<your-run-id>/` to the Shared Folder. Include your batch CSV if you changed terms. Do **not** upload `.env`.

Required run files: `queries.csv`, `videos.csv`, `video_query_matches.csv`, `collection_errors.csv`, `run_manifest.json`, `dataset_qa.json`.

## Merge, transcripts, handoff (Xinhui)

```bash
python3 assemble_dataset.py \
  --run-ids batch-tanay-lung-pilot batch-xinhui-lung-pilot \
           batch-yiran-colon-pilot batch-yule-colon-pilot batch-suzie-colon-pilot \
  --dataset-id screening-v1
```

Transcripts (does not use Data API quota). Prefer small batches; leave `--translate-to-en` off for English corpora:

```bash
caffeinate -i -m -s python3 -u extract_transcripts.py \
  --input data/curated/screening-v1/videos.csv \
  --output data/curated/screening-v1/videos_with_transcripts.csv \
  --error-output data/curated/screening-v1/transcript_errors.csv \
  --resume --batch-size 50 --delay-seconds 5
```

Optional 6-way split if the team extracts in parallel:

```bash
python3 scripts/split_transcript_workload.py \
  --input data/curated/screening-v1/videos.csv \
  --members 6

python3 scripts/merge_transcript_results.py \
  --base data/curated/screening-v1/videos_with_transcripts.csv \
  --chunks data/team_transcripts/member_*.csv \
  --output data/curated/screening-v1/videos_with_transcripts.csv
```

Package for [AHN-youtube-videos](https://github.com/tanaymit/AHN-youtube-videos):

```bash
python3 package_handoff.py \
  --curated data/curated/screening-v1 \
  --handoff-id screening-v1
```

Tanay: `RUN_ID=screening-v1 python -m src.run_eval`.

Pilot already collected: `full-corpus-001` (50 queries, Top 20, 785 unique videos). Decide whether to keep it as a dev set or re-collect at Top 10 when all 200 terms are ready. Script behavior and corpus stats: [PIPELINE_GUIDE.md](PIPELINE_GUIDE.md).

## Git FAQ

**Git asks for a password when pushing?** Use a GitHub Personal Access Token, or `gh auth login`.

**`.env` was pushed by mistake?** Rotate the API key in Google Cloud and remove it from git history.

**No GitHub account?** https://github.com/signup
