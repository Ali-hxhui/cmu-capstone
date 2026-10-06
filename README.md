# CMU Cancer Screening Video Analytics

YouTube metadata and transcript pipeline for AHN lung + colon cancer screening education.

Needs **Python 3.10+**. Each person uses their own YouTube Data API key. Do **not** push `.env`.

```
Your new terms → collect videos → extract transcripts → push your run folder
               → merge and clean → ranking model
```

**Other docs:** [YOUTUBE_API_KEY.md](YOUTUBE_API_KEY.md) · [PIPELINE_GUIDE.md](PIPELINE_GUIDE.md) · [DATA_CONTRACT.md](DATA_CONTRACT.md)

## How to run this round

Wave 1 (the original 120 terms, six `*-001` folders) is **already done**. Do not collect those terms again and do not write into a `*-001` folder.

This round is **the 80 new terms only**.

| Who | Collects this round? | Term file | Run-id | Count |
|-----|----------------------|-----------|--------|-------|
| haikuan | Yes | `search_terms/batches_expansion/haikuan.csv` | `batch-haikuan-002` | 27 (14 lung + 13 colon) |
| yule | Yes | `search_terms/batches_expansion/yule.csv` | `batch-yule-002` | 27 (13 lung + 14 colon) |
| suzie | Yes | `search_terms/batches_expansion/suzie.csv` | `batch-suzie-002` | 26 (13 lung + 13 colon) |
| tanay | No | — | — | Wave 1 finished |
| xinhui | No | — | — | Wave 1 finished |
| yiran | No | — | — | Wave 1 finished |

Copy the `--input` and `--run-id` from your row. Do not invent a different run-id.

The three CSVs are already in the repo after `git pull`. You do not need to regenerate them unless `search_terms.csv` changes again.

Each query uses about 100 quota units (27 queries ≈ 2,700).

Team repo: [Suzi1i1i/ahn_cancer_screening](https://github.com/Suzi1i1i/ahn_cancer_screening). Run every command below from `data_collection/`.

First-time clone:

```bash
git clone https://github.com/Suzi1i1i/ahn_cancer_screening.git
cd ahn_cancer_screening/data_collection
```

### 1. Pull and check your API key

```bash
git pull origin main
cd data_collection   # if you already cloned and are not already here
python3 -m pip install -r requirements.txt
cp .env.example .env   # skip if you already have .env
# Put your key in .env — steps in YOUTUBE_API_KEY.md
python3 test_youtube_api.py
```

Confirm `search_terms/batches_expansion/<your_name>.csv` exists (27 rows for haikuan and yule, 26 for suzie).

If that file is missing:

```bash
python3 assign_collection_batches.py \
  --assignments search_terms/assignments/collection_assignments_expansion_80.csv \
  --output-dir search_terms/batches_expansion
```

### 2. Collect videos (uses your API key)

Use **only your own** command.

**haikuan**

```bash
python3 collect_youtube_data.py \
  --input search_terms/batches_expansion/haikuan.csv \
  --top-n 10 \
  --run-id batch-haikuan-002
```

**yule**

```bash
python3 collect_youtube_data.py \
  --input search_terms/batches_expansion/yule.csv \
  --top-n 10 \
  --run-id batch-yule-002
```

**suzie**

```bash
python3 collect_youtube_data.py \
  --input search_terms/batches_expansion/suzie.csv \
  --top-n 10 \
  --run-id batch-suzie-002
```

This writes `data/runs/<your-run-id>/videos.csv`. If that folder already exists, the script will not overwrite.

Optional check with no API calls: add `--dry-run`.

### 3. Extract public transcripts (no API key)

Leave `--translate-to-en` off. If YouTube blocks the IP, stop and resume later. A few `transcript_unavailable` videos are normal.

**haikuan**

```bash
python3 extract_transcripts.py \
  --input data/runs/batch-haikuan-002/videos.csv \
  --resume --batch-size 50 --delay-seconds 5
```

**yule**

```bash
python3 extract_transcripts.py \
  --input data/runs/batch-yule-002/videos.csv \
  --resume --batch-size 50 --delay-seconds 5
```

**suzie**

```bash
python3 extract_transcripts.py \
  --input data/runs/batch-suzie-002/videos.csv \
  --resume --batch-size 50 --delay-seconds 5
```

### 4. Push only your finished run

Commit `data/runs/<your-run-id>/` only after it contains both `videos.csv` and `videos_with_transcripts.csv`. Do not commit `.env`. Do not commit another person's run folder.

**haikuan**

```bash
git pull origin main
git add data/runs/batch-haikuan-002
git commit -m "Add batch-haikuan-002 videos and transcripts."
git push origin main
```

**yule**

```bash
git pull origin main
git add data/runs/batch-yule-002
git commit -m "Add batch-yule-002 videos and transcripts."
git push origin main
```

**suzie**

```bash
git pull origin main
git add data/runs/batch-suzie-002
git commit -m "Add batch-suzie-002 videos and transcripts."
git push origin main
```

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
