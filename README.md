# CMU Cancer Screening Video Analytics

YouTube video metadata and transcript pipeline for AHN lung + colon cancer screening
education research.

**Docs:** [Team workflow](TEAM_WORKFLOW.md) · [Pipeline guide](PIPELINE_GUIDE.md) ·
[YouTube API key setup](YOUTUBE_API_KEY.md) · [Data contract](DATA_CONTRACT.md) ·
[GitHub setup](GITHUB_SETUP.md)

## Repository layout

```
collect_youtube_data.py   → search_terms/ → data/runs/<run-id>/
assemble_dataset.py       → data/curated/<dataset-id>/
extract_transcripts.py    → videos_with_transcripts.csv
package_handoff.py        → data/runs/<handoff-id>/ (downstream LLM input)
scripts/                  → batch split & merge helpers
search_terms/             → master CSV + 6-person assignments
config/                   → target counts (200 terms, Top 10)
```

Large CSV outputs live under `data/` and are **not** committed to git — share via team drive.

## Team

| Domain | Members |
|--------|---------|
| Lung | haikuan, tanay, xinhui |
| Colon | yiran, yule, suzie |

Target: **100 + 100 search terms**, **Top 10 videos** each.

## Data collection

1. Install dependencies once:

   ```bash
   python3 -m pip install -r requirements.txt
   ```

2. **Get a YouTube Data API key** — see [YOUTUBE_API_KEY.md](YOUTUBE_API_KEY.md) for the
   full Google Cloud setup steps. Each team member should use their own key.

3. Put the key in `.env`:

   ```bash
   cp .env.example .env
   ```

   ```env
   YOUTUBE_API_KEY=your_key_here
   ```

   Verify it works:

   ```bash
   python3 test_youtube_api.py
   ```

4. Add one search term per row to `search_terms/search_terms.csv`. `cancer_domain` should be
   `colon` or `lung`. The optional contributor, source, and scope-category fields are retained
   in the query-to-video relationship dataset. See `search_terms/README.md` and
   `TEAM_WORKFLOW.md` for the 6-person collection plan (200 terms × Top 10 videos).

   ```csv
   cancer_domain,search_query,contributor,source,scope_category
   colon,how to prepare for a colonoscopy,Team,American Cancer Society,Pre-screening education
   lung,low dose CT lung cancer screening,Team,American Lung Association,Pre-screening education
   ```

5. Collect a small, versioned test batch:

   ```bash
   python3 collect_youtube_data.py --top-n 10 --max-queries 2 --run-id test-001
   ```

   To validate a batch without making any API request, add `--dry-run`:

   ```bash
   python3 collect_youtube_data.py --top-n 10 --max-queries 10 --run-id batch-001 --dry-run
   ```

6. Collect a later batch without overwriting the first:

   ```bash
   python3 collect_youtube_data.py --top-n 10 --start-at 2 --max-queries 20 --run-id batch-002
   ```

7. Merge completed runs into one dataset for downstream analysis. This command is offline and
   does not call YouTube:

   ```bash
   python3 assemble_dataset.py --run-ids batch-001 batch-002 --dataset-id screening-v1
   ```

8. Extract transcripts from videos that YouTube makes publicly available. This uses a separate,
   unofficial public-transcript client and does not consume YouTube Data API quota:

   ```bash
   python3 extract_transcripts.py \
     --input data/curated/screening-v1/videos.csv \
     --translate-to-en \
     --dry-run
   ```

   Remove `--dry-run` only after reviewing the plan. The extractor requests videos serially,
   waits one second between them, prefers English captions, and records unavailable or blocked
   videos in `transcript_errors.csv`. Each row is written as soon as it is processed, so an
   interrupted run keeps its progress and `--resume` continues from the first unwritten video.

## Transcript rate limits

The public-transcript client is unofficial, and YouTube blocks an IP that requests too many
transcripts too quickly. A sustained run of several hundred requests caused a block that stayed
in effect the next day and then re-triggered after only 27 requests at a three-second delay.

Extract in small batches instead of one long pass. `--batch-size` counts only videos that still
need a transcript, so the same command can be repeated unchanged until the corpus is complete:

```bash
caffeinate -i -m -s python3 -u extract_transcripts.py \
  --input data/runs/<run-id>/videos.csv \
  --resume --batch-size 50 --delay-seconds 5
```

Each run reports corpus-level progress, so run one batch, confirm the retrieval rate looks
normal, then wait a few hours before repeating it. `--delay-seconds` sets a minimum wait that is
randomized up to twice its value, and `caffeinate` keeps the machine awake while the screen
sleeps.

Leave `--translate-to-en` off unless the corpus contains non-English videos. It spends a second
request on every video that fails, which is the opposite of what a rate-limited run needs.

When YouTube blocks the IP, the extractor stops immediately rather than recording the remaining
videos as having no transcript. Treat a block as a signal to pause for several hours; repeated
retries extend it. Switching to a different network is the fastest way to continue.

Each command creates `data/runs/<run-id>/` containing:

- `queries.csv`: input search terms with stable query IDs.
- `videos.csv`: one deduplicated row per video, including normalized duration, language,
  transcript status, and near-duplicate candidate fields.
- `video_query_matches.csv`: every query that retrieved a video, its rank, contributor,
  source, and scope category.
- `collection_errors.csv`: API, unavailable-video, and network errors.
- `dataset_qa.json`: completeness, duplicate, caption, and error statistics.
- `run_manifest.json`: input checksum, run configuration, timestamp, and quota estimate.

The `caption_available` field is YouTube's caption-availability flag. `transcript_text` is
populated only when a public transcript can be retrieved. The official API does not allow the
project to download transcripts for videos it does not administer, and the supplemental
transcript client cannot recover captions that YouTube does not expose.

The merged handoff dataset is saved under `data/curated/<dataset-id>/`. Its fields and join keys
are defined in `DATA_CONTRACT.md`.

## Quota

Each unique search query costs about 100 YouTube Data API quota units. The default daily budget is
typically 10,000 units, so do not run all 100 terms in a single batch. Collect in batches (for
example, 50–90 terms) and check the Google Cloud quota dashboard before the next batch.
