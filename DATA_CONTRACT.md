# Data contract for downstream components

Each collection command writes one immutable directory at `data/runs/<run_id>/`. Downstream
components should select a run ID explicitly rather than relying on a mutable “latest” file.

## Input

`search_terms.csv` requires `cancer_domain` and `search_query`. It may also include
`contributor`, `source`, and `scope_category`.

## Required handoff files

- `queries.csv`: one record per requested query. Join key: `query_id`.
- `videos.csv`: one record per unique `video_id`. This is the video-level input for
  preprocessing and evaluation.
- `video_query_matches.csv`: one record per retrieved query-video pair. Join keys:
  `video_id` and `query_id`. Ranking must use this file to preserve query context.
- `dataset_qa.json`: run-level completeness and duplicate statistics.
- `run_manifest.json`: immutable provenance, configuration, and input-file checksum.
- `collection_errors.csv`: retrieval failures and unavailable-video records.

## Video fields for LLM evaluation

Use `video_id`, `title`, `description`, `duration_seconds`, `default_language`,
`default_audio_language`, `transcript_text`, and `transcript_status`.

Run `extract_transcripts.py` on the curated `videos.csv` to create
`videos_with_transcripts.csv`. That file fills `transcript_text`,
`transcript_text_normalized`, transcript language, generated/translated flags, source, status,
and failure reason where YouTube exposes a public transcript. `transcript_status` distinguishes
retrieved, unavailable, and failed cases. An evaluator must not treat an empty transcript as
evidence that a video has no educational content.

## Fields for ranking and presentation

Use `video_id`, `url`, `title`, `channel_title`, `video_published_at`, `duration_seconds`, and
the query context in `video_query_matches.csv`. Engagement fields (`view_count`, `like_count`,
and `comment_count`) are descriptive only; they must not be treated as clinical-quality labels.

Use `near_duplicate_candidate` for review before final ranking. It flags identical normalized
title-and-channel combinations but does not delete any record automatically.
