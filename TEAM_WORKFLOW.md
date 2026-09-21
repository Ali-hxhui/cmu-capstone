# Team Workflow

Target: **100 lung + 100 colon** search terms, **Top 10** videos each.

Repo: https://github.com/Ali-hxhui/cmu-capstone

The working master list is `search_terms/search_terms.csv` (**60 terms**: 30 lung + 30 colon). After a GitHub update: `git pull`, then regenerate your batch before collecting.

## Where things live

| What | Where | Who |
|------|--------|-----|
| Code and English docs | **GitHub** | Xinhui maintains; others clone / pull |
| Search terms | `search_terms/search_terms.csv` | Edit locally; send updates to Xinhui |
| Collection / transcript CSVs | **Shared Folder** (`data/` is gitignored) | Each member uploads their run folder |
| API keys | Local `.env` | One key per person |

Teammates do **not** need to push. Clone, run locally, upload results.

Tracked: scripts, master search terms, assignments, English docs, `requirements.txt`, `.env.example`.

Not tracked: `.env`, `data/`, generated `search_terms/batches/*.csv`, `.venv/`, `local/`.

Suggested access: Xinhui **Admin**, others **Read**.

## Ownership

| Domain | Members | Target each (200-term plan) | Current 60-term status |
|--------|---------|-----------------------------|------------------------|
| Lung | haikuan, tanay, xinhui | ~33–34 | 10 each, ready to collect |
| Colon | yiran, yule, suzie | ~33–34 | 10 each, ready to collect |

Use your name in `contributor`. New terms: copy `search_terms/search_terms.template.csv`, set `cancer_domain` to `lung` or `colon`, keep lung rows together then colon rows.

| File | When |
|------|------|
| `search_terms/assignments/collection_assignments_current.csv` | Current 60-term list |
| `search_terms/assignments/collection_assignments.csv` | After the 200-term master file is on GitHub |

## 1. Setup

Python **3.10+**.

```bash
git clone https://github.com/Ali-hxhui/cmu-capstone.git
cd cmu-capstone
python3 -m pip install -r requirements.txt
cp .env.example .env
# Add YOUTUBE_API_KEY — see YOUTUBE_API_KEY.md
python3 test_youtube_api.py
```

After a term-list or script update: `git pull origin main`.

## 2. Collect (every member)

```bash
python3 scripts/assign_collection_batches.py \
  --assignments search_terms/assignments/collection_assignments_current.csv
```

That writes `search_terms/batches/<your_name>.csv`. Use the `expected_run_id` from the assignments file. `--run-id` must be unique across the team.

```bash
python3 collect_youtube_data.py \
  --input search_terms/batches/tanay.csv \
  --top-n 10 \
  --run-id batch-tanay-lung-001
```

If your name is skipped with 0 terms, you have nothing to collect yet.

**Quota:** each query ≈ 100 units. Default daily budget ≈ 10,000. A 33–34 query batch ≈ 3,300–3,400 units.

## 3. Extract transcripts (every member, on your own run)

Does **not** use the Data API key or quota. Run only after `videos.csv` exists.

```bash
python3 extract_transcripts.py \
  --input data/runs/batch-tanay-lung-001/videos.csv \
  --resume --batch-size 50 --delay-seconds 5
```

Leave `--translate-to-en` off. Stop if the IP is blocked; resume later or switch networks.

## 4. Upload

Upload the whole folder `data/runs/<your-run-id>/` (now including `videos_with_transcripts.csv` and `transcript_errors.csv` if extraction ran). Do **not** upload `.env`.

If you edited terms locally, include your batch CSV in the same Shared Folder path.

## 5. Merge and package (Xinhui)

After all members finish:

```bash
python3 assemble_dataset.py \
  --run-ids batch-haikuan-lung-001 batch-tanay-lung-001 batch-xinhui-lung-001 \
           batch-yiran-colon-001 batch-yule-colon-001 batch-suzie-colon-001 \
  --dataset-id screening-v1
```

If some people could not extract, finish leftover videos on the merged `videos.csv`, or split the remainder:

```bash
python3 scripts/split_transcript_workload.py \
  --input data/curated/screening-v1/videos.csv \
  --processed data/curated/screening-v1/videos_with_transcripts.csv \
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

## Git FAQ

**Git asks for a password when pushing?** Use a GitHub Personal Access Token, or `gh auth login`.

**`.env` was pushed by mistake?** Rotate the key in Google Cloud and remove it from git history.

**No GitHub account?** https://github.com/signup
