# CMU Cancer Screening Video Analytics

YouTube metadata and transcript pipeline for AHN lung + colon cancer screening education.

Needs **Python 3.10+**. Each person uses their own YouTube Data API key. Do **not** push `.env`.

```
Your new terms → collect videos → extract transcripts → push your run folder
               → merge and clean → ranking model
```

Wave 1 (120 terms, six people) is already collected. This round is **the 80 new terms only**, split across three people. Use your **002** run-id. Do not write into a `*-001` folder.

**Other docs:** [YOUTUBE_API_KEY.md](YOUTUBE_API_KEY.md) · [PIPELINE_GUIDE.md](PIPELINE_GUIDE.md) · [DATA_CONTRACT.md](DATA_CONTRACT.md)

## What each person does this round

Copy the **`--input`** and **`--run-id`** from your row. Do not invent a different run-id.

| You | Your terms | Collect / extract with |
|-----|------------|------------------------|
| haikuan | `search_terms/batches_expansion/haikuan.csv` (27: 14 lung + 13 colon) | `--run-id batch-haikuan-002` |
| yule | `search_terms/batches_expansion/yule.csv` (27: 13 lung + 14 colon) | `--run-id batch-yule-002` |
| suzie | `search_terms/batches_expansion/suzie.csv` (26: 13 lung + 13 colon) | `--run-id batch-suzie-002` |

After `git pull`, those three CSVs are already in the repo. You do not need to regenerate them unless `search_terms.csv` changes again.

Example below uses **haikuan**. Yule and Suzie only swap the two values in the table.

### 1. Pull, install, add your API key

```bash
git pull origin main
cd cmu-capstone   # if you are not already in the repo root
python3 -m pip install -r requirements.txt
cp .env.example .env   # skip if you already have .env
# Put your key in .env — steps in YOUTUBE_API_KEY.md
python3 test_youtube_api.py
```

Confirm `search_terms/batches_expansion/<your_name>.csv` exists. Row counts: haikuan 27, yule 27, suzie 26.

If that file is missing, regenerate it:

```bash
python3 assign_collection_batches.py \
  --assignments search_terms/assignments/collection_assignments_expansion_80.csv \
  --output-dir search_terms/batches_expansion
```

### 2. Collect videos (uses your API key)

Each query uses about 100 quota units (27 queries ≈ 2,700).

```bash
python3 collect_youtube_data.py \
  --input search_terms/batches_expansion/haikuan.csv \
  --top-n 10 \
  --run-id batch-haikuan-002
```

| You | Command |
|-----|---------|
| haikuan | `python3 collect_youtube_data.py --input search_terms/batches_expansion/haikuan.csv --top-n 10 --run-id batch-haikuan-002` |
| yule | `python3 collect_youtube_data.py --input search_terms/batches_expansion/yule.csv --top-n 10 --run-id batch-yule-002` |
| suzie | `python3 collect_youtube_data.py --input search_terms/batches_expansion/suzie.csv --top-n 10 --run-id batch-suzie-002` |

Creates `data/runs/batch-haikuan-002/videos.csv` (or your run-id). If that folder already exists, the script will not overwrite.

Optional check with no API calls: add `--dry-run`.

### 3. Extract public transcripts (no API key)

```bash
python3 extract_transcripts.py \
  --input data/runs/batch-haikuan-002/videos.csv \
  --resume --batch-size 50 --delay-seconds 5
```

| You | `--input` |
|-----|-----------|
| haikuan | `data/runs/batch-haikuan-002/videos.csv` |
| yule | `data/runs/batch-yule-002/videos.csv` |
| suzie | `data/runs/batch-suzie-002/videos.csv` |

Leave `--translate-to-en` off. If YouTube blocks the IP, stop and resume later. A few `transcript_unavailable` videos are normal.

### 4. Push only your finished run

Commit `data/runs/<your-run-id>/` only after it contains both `videos.csv` and `videos_with_transcripts.csv`. Do not commit `.env`, and do not commit another person's run folder.

```bash
git pull origin main
git add data/runs/batch-haikuan-002
git commit -m "Add batch-haikuan-002 videos and transcripts."
git push origin main
```

| You | Add this folder |
|-----|-----------------|
| haikuan | `data/runs/batch-haikuan-002` |
| yule | `data/runs/batch-yule-002` |
| suzie | `data/runs/batch-suzie-002` |

Each run-id is a different folder, so the three pushes do not overwrite each other.

If `search_terms/search_terms.csv` changes on GitHub: `git pull origin main`, regenerate batches (step 1), then collect with a **new** run-id.

## After the three new runs are on main

One teammate pulls `main`, merges the new run folders with the finished wave-1 runs, cleans the combined tables, and commits that cleaned dataset. Ranking reads the cleaned tables through its own entry point. Do not run ranking inside `collect_youtube_data.py` or `extract_transcripts.py`.

```bash
python3 assemble_dataset.py \
  --run-ids batch-haikuan-lung-001 batch-tanay-lung-001 batch-xinhui-lung-001 \
           batch-yiran-colon-001 batch-yule-colon-001 batch-suzie-colon-001 \
           batch-haikuan-002 batch-yule-002 batch-suzie-002 \
  --dataset-id screening-v1
```

`assemble_dataset.py` writes `data/curated/screening-v1/`. Cleaning happens on that folder. The cleaned files are the input the ranking code expects. Field names: [DATA_CONTRACT.md](DATA_CONTRACT.md).

## Wave 1 (already done)

These 001 folders are finished. Do not collect them again.

| You | Terms | Run-id |
|-----|-------|--------|
| haikuan | `search_terms/batches/haikuan.csv` (20 lung) | `batch-haikuan-lung-001` |
| tanay | `search_terms/batches/tanay.csv` (20 lung) | `batch-tanay-lung-001` |
| xinhui | `search_terms/batches/xinhui.csv` (20 lung) | `batch-xinhui-lung-001` |
| yiran | `search_terms/batches/yiran.csv` (20 colon) | `batch-yiran-colon-001` |
| yule | `search_terms/batches/yule.csv` (20 colon) | `batch-yule-colon-001` |
| suzie | `search_terms/batches/suzie.csv` (20 colon) | `batch-suzie-colon-001` |
