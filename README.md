# CMU Cancer Screening Video Analytics

YouTube metadata and transcript pipeline for AHN lung + colon cancer screening education.

Needs **Python 3.10+**. Each person uses their own YouTube Data API key. Do **not** push results or `.env` to GitHub.

```
Your 20 terms → collect videos → extract transcripts → upload the finished run folder
```

Everyone finishes **both videos and transcripts locally**, then uploads. Do not upload a collection-only folder.

**Other docs:** [YOUTUBE_API_KEY.md](YOUTUBE_API_KEY.md) · [PIPELINE_GUIDE.md](PIPELINE_GUIDE.md) · [DATA_CONTRACT.md](DATA_CONTRACT.md)

Code lives on GitHub. Large CSVs go to the Shared Folder (`data/` is gitignored).

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
python3 scripts/assign_collection_batches.py \
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

### 5. Upload only when both steps are done

The folder must contain `videos.csv` and `videos_with_transcripts.csv`. Upload the whole `data/runs/<your-run-id>/` directory to the Shared Folder. Do not upload `.env`.

If `search_terms/search_terms.csv` changes on GitHub: `git pull origin main`, redo step 2, then collect with a **new** run-id.

To add terms later: copy `search_terms/search_terms.template.csv`, set `contributor` to your name, send the rows to Xinhui so the master file stays in sync.

## After everyone uploads (Xinhui)

```bash
python3 assemble_dataset.py \
  --run-ids batch-haikuan-lung-001 batch-tanay-lung-001 batch-xinhui-lung-001 \
           batch-yiran-colon-001 batch-yule-colon-001 batch-suzie-colon-001 \
  --dataset-id screening-v1

python3 package_handoff.py \
  --curated data/curated/screening-v1 \
  --handoff-id screening-v1
```

Tanay: `RUN_ID=screening-v1 python -m src.run_eval` in [AHN-youtube-videos](https://github.com/tanaymit/AHN-youtube-videos).
