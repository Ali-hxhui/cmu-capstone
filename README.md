# CMU Cancer Screening Video Analytics

YouTube metadata and transcript pipeline for AHN lung + colon cancer screening education.

Needs **Python 3.10+**. Each person uses their own YouTube Data API key. Do **not** push results or `.env` to GitHub.

```
Search terms → collect (API key) → extract transcripts (no API key) → upload run folder
```

**Docs:** [TEAM_WORKFLOW.md](TEAM_WORKFLOW.md) · [YOUTUBE_API_KEY.md](YOUTUBE_API_KEY.md) · [PIPELINE_GUIDE.md](PIPELINE_GUIDE.md) · [DATA_CONTRACT.md](DATA_CONTRACT.md)

## What each person does

Copy the **`--input`** and **`--run-id`** from your row. Do not invent a different run-id.

| You | Your terms | Collect / extract with |
|-----|------------|------------------------|
| haikuan | `search_terms/batches/haikuan.csv` (10 lung) | `--run-id batch-haikuan-lung-001` |
| tanay | `search_terms/batches/tanay.csv` (10 lung) | `--run-id batch-tanay-lung-001` |
| xinhui | `search_terms/batches/xinhui.csv` (10 lung) | `--run-id batch-xinhui-lung-001` |
| yiran | `search_terms/batches/yiran.csv` (10 colon) | `--run-id batch-yiran-colon-001` |
| yule | `search_terms/batches/yule.csv` (10 colon) | `--run-id batch-yule-colon-001` |
| suzie | `search_terms/batches/suzie.csv` (10 colon) | `--run-id batch-suzie-colon-001` |

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

This reads the 60-term master list and writes `search_terms/batches/` (not in git):

```bash
python3 scripts/assign_collection_batches.py \
  --assignments search_terms/assignments/collection_assignments_current.csv
```

Confirm `search_terms/batches/<your_name>.csv` exists and has 10 rows.

### 3. Collect videos (uses your API key)

```bash
python3 collect_youtube_data.py \
  --input search_terms/batches/tanay.csv \
  --top-n 10 \
  --run-id batch-tanay-lung-001
```

Creates `data/runs/batch-tanay-lung-001/videos.csv`. If that folder already exists, pick a new run-id or delete it — the script will not overwrite.

Optional check with no API calls: add `--dry-run`.

### 4. Extract public transcripts (no API key)

Only after `videos.csv` exists:

```bash
python3 extract_transcripts.py \
  --input data/runs/batch-tanay-lung-001/videos.csv \
  --resume --batch-size 50 --delay-seconds 5
```

Leave `--translate-to-en` off. If YouTube blocks the IP, stop and resume later.

### 5. Upload your run folder

Upload the whole directory `data/runs/<your-run-id>/` to the Shared Folder (including `videos_with_transcripts.csv` if step 4 finished). Do not upload `.env`.

Xinhui merges everyone’s folders later — see [TEAM_WORKFLOW.md](TEAM_WORKFLOW.md).

If `search_terms/search_terms.csv` changes on GitHub: `git pull origin main`, redo step 2, then collect with a **new** run-id.
