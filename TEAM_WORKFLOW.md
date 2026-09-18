# Team Workflow

Target: **100 lung + 100 colon search terms**, **Top 10 videos** each.

## How we collaborate

| What | Where | Who |
|------|-------|-----|
| Code and docs | **GitHub** (clone / pull only) | Xinhui maintains; others read |
| Search terms | **Local CSV** on each machine | Each member edits their own batch |
| Collection outputs | **Shared Folder** | Each member uploads their run folder |
| Final merged dataset | **Local + Shared Folder** | Xinhui runs `assemble_dataset.py` |

**Teammates do not need to push to GitHub.** Clone the repo, run locally, upload results.

Repo: https://github.com/Ali-hxhui/cmu-capstone

---

## Search term ownership

| Cancer type | Members | Target per person |
|-------------|---------|-------------------|
| **Lung** | haikuan, tanay, xinhui | ~33–34 terms |
| **Colon** | yiran, yule, suzie | ~33–34 terms |

Use your name in the `contributor` column. If you add new terms locally, send your updated CSV
to **Xinhui** so the master file on GitHub stays in sync.

---

## First-time setup (every member)

```bash
git clone https://github.com/Ali-hxhui/cmu-capstone.git
cd cmu-capstone
python3 -m pip install -r requirements.txt
cp .env.example .env
# Add YOUTUBE_API_KEY — see YOUTUBE_API_KEY.md
python3 test_youtube_api.py
```

When scripts or docs are updated on GitHub:

```bash
git pull origin main
```

---

## Step 1 — Prepare your search terms (local)

Generate your batch from the master file:

```bash
python3 scripts/assign_collection_batches.py \
  --assignments search_terms/assignments/collection_assignments_pilot50.csv
```

Output: `search_terms/batches/<your_name>.csv`

Edit that file (or a personal copy) to add terms. Set `contributor` to your name and keep
`cancer_domain` as `lung` or `colon`.

**Optional:** email or Shared-Drive your updated CSV to Xinhui for the master list.

---

## Step 2 — Collect videos (Top 10)

Use the `expected_run_id` from `search_terms/assignments/collection_assignments_pilot50.csv`.

```bash
python3 collect_youtube_data.py \
  --input search_terms/batches/tanay.csv \
  --top-n 10 \
  --run-id batch-tanay-lung-pilot
```

Use your own `--input` and `--run-id`. Each `--run-id` must be **unique** across the team.

---

## Step 3 — Upload results to Shared Folder

Upload the entire folder `data/runs/<your-run-id>/` to the team Shared Folder
(e.g. `Shared Folder/runs/tanay/`).

**Required files:**

| File | Purpose |
|------|---------|
| `queries.csv` | Search terms used in this run |
| `videos.csv` | Deduplicated video metadata |
| `video_query_matches.csv` | Query–video pairs with rank |
| `collection_errors.csv` | API errors (if any) |
| `run_manifest.json` | Run config and checksum |
| `dataset_qa.json` | Summary stats |

Do **not** upload `.env` or API keys.

If you changed search terms locally, include your batch CSV in the same Shared Folder path.

---

## Step 4 — Xinhui merges all runs

After all members finish, download run folders into `data/runs/` and merge:

```bash
python3 assemble_dataset.py \
  --run-ids batch-tanay-lung-pilot batch-xinhui-lung-pilot \
           batch-yiran-colon-pilot batch-yule-colon-pilot batch-suzie-colon-pilot \
  --dataset-id screening-v1
```

Output: `data/curated/screening-v1/`

See `search_terms/COLLECTION_PLAN.md` for transcript splitting and LLM handoff.

---

## Current progress (50 terms)

| Member | Domain | Terms now | Status |
|--------|--------|-----------|--------|
| tanay | lung | 10 | ready to collect |
| xinhui | lung | 10 | ready to collect |
| haikuan | lung | 0 | add terms first |
| yiran | colon | 10 | ready to collect |
| yule | colon | 10 | ready to collect |
| suzie | colon | 10 | ready to collect |

---

## Optional: push search terms via GitHub

Only if the team prefers git over Shared Folder for term updates:

1. Repo admin grants **Write** access
2. `git pull` → edit `search_terms/search_terms.csv` → commit → push
3. See `GITHUB_SETUP.md` for conflict-avoidance rules

This is **not required** for the default workflow above.
