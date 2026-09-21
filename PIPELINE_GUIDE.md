# Pipeline Guide

How the four scripts turn search terms into a dataset for per-query LLM evaluation.

```
search_terms.csv → collect_youtube_data.py → data/runs/<member-run-id>/
                 → assemble_dataset.py     → data/curated/<dataset-id>/
                 → extract_transcripts.py  → videos_with_transcripts.csv
                 → package_handoff.py      → data/runs/<handoff-id>/
```

| Step | Script | YouTube Data API? | Output |
|------|--------|-------------------|--------|
| 1. Collect | `collect_youtube_data.py` | Yes | `data/runs/<run-id>/` |
| 2. Assemble | `assemble_dataset.py` | No | `data/curated/<dataset-id>/` |
| 3. Extract | `extract_transcripts.py` | No | `videos_with_transcripts.csv` |
| 4. Package | `package_handoff.py` | No | `data/runs/<handoff-id>/` for [AHN-youtube-videos](https://github.com/tanaymit/AHN-youtube-videos) |

Team commands live in [TEAM_WORKFLOW.md](TEAM_WORKFLOW.md). Field contract: [DATA_CONTRACT.md](DATA_CONTRACT.md).

## 1. `collect_youtube_data.py`

Input: a search-term CSV with `search_query` and `cancer_domain` (optional `contributor`, `source`, `scope_category`).

| Phase | API | Result |
|-------|-----|--------|
| A. Search | `search.list` | Top N videos per query and each video's **rank under that query** → `video_query_matches.csv` |
| B. Videos | `videos.list` (50 IDs / request) | Title, description, duration, language, engagement, `caption_available` |
| C. Channels | `channels.list` | Channel name, subscribers, country |
| D. Dedup | none | One row per `video_id` in `videos.csv`. Same normalized title + channel → `near_duplicate_candidate=True` (flag only, not deleted) |

This step does **not** download transcript text. `caption_available` is YouTube's flag, not proof we retrieved captions. Each search query costs about **100 quota units**. Use a new `--run-id` for every batch; the run directory is never overwritten.

## 2. `assemble_dataset.py`

Offline merge of `data/runs/<run-id>/` folders into `data/curated/<dataset-id>/`.

- Videos: keep latest `collected_at` per `video_id`
- Matches: unique `(video_id, normalized_search_query)`
- Queries: unique `(cancer_domain, normalized_search_query)`
- Adds `source_run_ids`, `search_query_count`, `search_queries`, and `dataset_manifest.json`

## 3. `extract_transcripts.py`

The Data API cannot download captions for videos we do not own. This script uses `youtube-transcript-api` (public captions only) and **does not use API quota**.

```
Try en / en-US / en-GB
  → public_transcript_retrieved
  → else optional --translate-to-en
  → translated_public_transcript
  → else transcript_unavailable + transcript_errors.csv
```

Leave `--translate-to-en` off for English corpora (extra request on every miss). Each row is flushed immediately; `--resume` skips written `video_id`s. Stops on IP block (`IpBlocked`, `RequestBlocked`, `PoTokenRequired`) and after 15 consecutive failures. Default timeout is 20s; `--delay-seconds` waits a random interval up to 2× that value.

`--batch-size` counts only outstanding videos. After a block, pause hours or switch networks; retrying immediately extends the ban. A past run of several hundred requests blocked the IP into the next day, then re-triggered after 27 requests at a 3s delay.

Useful fields: `transcript_text`, `transcript_text_normalized`, `transcript_status`, `transcript_is_generated`, `transcript_language`. An empty transcript is not evidence the video has no educational value. YouTube `caption_available=true` is uncommon (~23% in the pilot); actual retrieval on processed videos was ~94% because auto-captions are often public.

## 4. `package_handoff.py`

Copies the curated folder into `data/runs/<handoff-id>/` in the layout Tanay's evaluator expects (`RUN_ID=<handoff-id>`).

## Data model

```
queries.csv  ──query_id──┐
                         ├── video_query_matches.csv (one row per query–video pair + rank)
videos.csv  ──video_id───┘
```

| Job | Use |
|-----|-----|
| LLM eval | `videos_with_transcripts.csv` + matches |
| Rank per query | filter matches by `query_id`, sort `search_rank`, join transcripts |
| Metadata only | `videos.csv` + matches |

The same video may appear under several queries; rank **per query**. Engagement counts are descriptive, not quality labels.

## Current corpora (as of 2026-09-17)

| | POC | Pilot full corpus |
|---|----------------|-------------------|
| Paths | `data/curated/poc-handoff-v1/`, `data/runs/poc-handoff-001/` | `data/curated/full-corpus-v1/`, `data/runs/full-corpus-001/` |
| Queries | 10 | 50 (Top 20) |
| Unique videos | 46 | 785 |
| Matches | 50 | 1,000 |
| Transcripts | 38/46 (82.6%) complete | Paused on IP block at `2d4H8eeEG-Q`: 486/785 processed, 458 retrieved, 28 unavailable, 299 outstanding |

Collection: 10/10 and 50/50 queries succeeded, 0 API errors, ~1,000 and ~5,000 search quota units.

After the block, resume with `--batch-size 30 --delay-seconds 8`. Do not retry on the same network immediately. Final target is Top 10 on 200 terms; decide whether this Top-20 pilot stays a dev set.
