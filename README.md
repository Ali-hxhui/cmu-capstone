# CMU Cancer Screening Video Analytics

YouTube metadata and transcript pipeline for AHN lung + colon cancer screening education.

Needs **Python 3.10+**. Each person uses their own YouTube Data API key. Do **not** push `.env`.

```
Your 20 terms → collect videos → extract transcripts → push your run folder
             → merge and clean → ranking model
```

Six people collect. The next teammate merges those runs, cleans the tables, and hands them to the ranking model in this same repo. Collection scripts and the ranking entry point stay separate.

**Other docs:** [YOUTUBE_API_KEY.md](YOUTUBE_API_KEY.md) · [PIPELINE_GUIDE.md](PIPELINE_GUIDE.md) · [DATA_CONTRACT.md](DATA_CONTRACT.md)

## What each person does

Copy the **`--input`** and **`--run-id`** from your row. Do not invent a different run-id.

| You | Your terms | Collect / extract with |
|-----|------------|------------------------|
| haikuan | `search_terms/batches/haikuan.csv` (20 lung) | `--run-id batch-haikuan-lung-001` |
| tanay | `search_terms/batches/tanay.csv` (20 lung) | `--run-id batch-tanay-lung-001` |
| xinhui | `search_terms/batches/xinhui.csv` (20 lung) | `--run-id batch-xinhui-lung-001` |
| yiran | `search_terms/batches/yiran.csv` (20 colon) | `--run-id batch-yiran-colon-001` |
| yule | `search_terms/batches/yule.csv` (20 colon) | `--run-id batch-yule-colon-001` |
| suzie | `search_terms/batches/suzie.csv` (20 colon) | `--run-id batch-suzie-colon-001` |

Example below uses **tanay**. Swap those two values for your row.

### 1. Clone, install, add your API key

```bash
git clone https://github.com/Ali-hxhui/cmu-capstone.git
cd cmu-capstone
python3 -m pip install -r requirements.txt
cp .env.example .env
# Put your key in .env — steps in YOUTUBE_API_KEY.md
python3 test_youtube_api.py
```

### 2. Build your personal term file

```bash
python3 assign_collection_batches.py \
  --assignments search_terms/assignments/collection_assignments_current.csv
```

Confirm `search_terms/batches/<your_name>.csv` exists and has 20 rows.

### 3. Collect videos (uses your API key)

Each query uses about 100 quota units (20 queries ≈ 2,000).

```bash
python3 collect_youtube_data.py \
  --input search_terms/batches/tanay.csv \
  --top-n 10 \
  --run-id batch-tanay-lung-001
```

Creates `data/runs/batch-tanay-lung-001/videos.csv`. If that folder already exists, the script will not overwrite.

Optional check with no API calls: add `--dry-run`.

### 4. Extract public transcripts (no API key)

```bash
python3 extract_transcripts.py \
  --input data/runs/batch-tanay-lung-001/videos.csv \
  --resume --batch-size 50 --delay-seconds 5
```

Leave `--translate-to-en` off. If YouTube blocks the IP, stop and resume later. A few `transcript_unavailable` videos are normal.

### 5. Push only your finished run

Commit `data/runs/<your-run-id>/` only after it contains both `videos.csv` and `videos_with_transcripts.csv`. Do not commit `.env`, and do not commit another person's run folder.

```bash
git pull origin main
git add data/runs/batch-tanay-lung-001
git commit -m "Add batch-tanay-lung-001 videos and transcripts."
git push origin main
```

Each run-id is a different folder, so the six pushes do not overwrite each other.

If `search_terms/search_terms.csv` changes on GitHub: `git pull origin main`, redo step 2, then collect with a **new** run-id.

## After the six runs are on main

One teammate pulls `main`, merges the six run folders, cleans the combined tables, and commits that cleaned dataset. Ranking reads the cleaned tables through its own entry point. Do not run ranking inside `collect_youtube_data.py` or `extract_transcripts.py`.

```bash
python3 assemble_dataset.py \
  --run-ids batch-haikuan-lung-001 batch-tanay-lung-001 batch-xinhui-lung-001 \
           batch-yiran-colon-001 batch-yule-colon-001 batch-suzie-colon-001 \
  --dataset-id screening-v1
```

`assemble_dataset.py` writes `data/curated/screening-v1/`. Cleaning happens on that folder. The cleaned files are the input the ranking code expects. Field names: [DATA_CONTRACT.md](DATA_CONTRACT.md).
