# CMU Cancer Screening Video Analytics

YouTube metadata and transcript pipeline for AHN lung + colon cancer screening education.

```
Search terms → collect → assemble → extract transcripts → package → LLM eval
```

**Docs**

| Doc | Use it for |
|-----|------------|
| [TEAM_WORKFLOW.md](TEAM_WORKFLOW.md) | Setup, who collects what, commands, GitHub vs Shared Folder |
| [PIPELINE_GUIDE.md](PIPELINE_GUIDE.md) | How the scripts work, data model, current corpus status |
| [YOUTUBE_API_KEY.md](YOUTUBE_API_KEY.md) | Google Cloud API key |
| [DATA_CONTRACT.md](DATA_CONTRACT.md) | Downstream file and field contract |

## Layout

```
collect_youtube_data.py   search terms → data/runs/<run-id>/
assemble_dataset.py       merge runs → data/curated/<dataset-id>/
extract_transcripts.py    videos.csv → videos_with_transcripts.csv
package_handoff.py        curated set → data/runs/<handoff-id>/ for LLM eval
scripts/                  split / merge helpers
search_terms/             master CSV + assignments
config/                   target counts
```

Large CSVs under `data/` are gitignored. Share them on the team drive.

## Quick start

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env          # add YOUTUBE_API_KEY — see YOUTUBE_API_KEY.md
python3 test_youtube_api.py
python3 collect_youtube_data.py --top-n 10 --max-queries 2 --run-id test-001 --dry-run
```

Team collection, merge, and handoff: [TEAM_WORKFLOW.md](TEAM_WORKFLOW.md).
