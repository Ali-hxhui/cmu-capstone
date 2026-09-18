# GitHub Upload and Team Sharing Guide

This repository holds **code and configuration only**. Large CSV outputs (collection runs,
transcripts) should be shared via Shared Folder or Google Drive.

---

## 1. What goes on GitHub vs what stays local

### Tracked in GitHub (English only)

```
cmu-capstone/
├── collect_youtube_data.py      # Step 1: YouTube metadata collection
├── extract_transcripts.py       # Step 2: transcript extraction
├── assemble_dataset.py          # Step 3: merge runs into handoff package
├── test_youtube_api.py          # API key connectivity test
├── scripts/                     # batch split and merge helpers
├── search_terms/                # master CSV + team assignments
├── config/collection_targets.json
├── DATA_CONTRACT.md
├── README.md
├── TEAM_WORKFLOW.md
├── PIPELINE_GUIDE.md
├── GITHUB_SETUP.md
├── YOUTUBE_API_KEY.md
├── requirements.txt
├── .env.example
└── .gitignore
```

### Not tracked (see `.gitignore`)

| Path | Reason |
|------|--------|
| `.env` | YouTube API key — each member creates locally |
| `data/` | Large generated CSVs — use Shared Folder |
| `search_terms/batches/*.csv` | Regenerate with `scripts/assign_collection_batches.py` |
| `.venv/`, `__pycache__/` | Local Python environment |
| `local/` | Personal bilingual / Chinese notes (not for teammates) |
| `*.pdf`, `*.xlsx`, `*.docx` | Project admin files |
| `Backup-codes*.txt` | Security credentials |

---

## 2. First upload (repo admin)

```bash
cd /path/to/cmu-capstone
git init
git branch -M main
git status    # confirm .env, data/, and local/ are NOT listed
git add .
git commit -m "$(cat <<'EOF'
Initial commit: YouTube screening video data pipeline.

Includes collection, transcript extraction, assembly scripts,
search term assignments, and team workflow docs.
EOF
)"
```

### Create the remote repository

**Option A — GitHub CLI (recommended if `gh` is installed):**

```bash
gh repo create cmu-capstone --private --source=. --remote=origin --push
```

**Option B — GitHub website:**

1. Open https://github.com/new
2. Repository name: `cmu-capstone` or `ahn-cancer-screening-pipeline`
3. Choose **Private**
4. Do **not** add a README (you already have one locally)
5. After creation:

```bash
git remote add origin https://github.com/<your-username>/cmu-capstone.git
git push -u origin main
```

---

## 3. Invite teammates

1. Open the repository on GitHub
2. **Settings** → **Collaborators** (or **Manage access**)
3. Click **Add people**
4. Enter each teammate's GitHub username
5. They accept the email invitation, then can clone

Suggested permissions (default workflow — local run + CSV handoff):

| Role | Access |
|------|--------|
| Repo admin (Xinhui) | Admin |
| Other 5 members | **Read** (clone and pull only) |

Grant **Write** only if teammates will push search term updates directly to GitHub (optional).
See `TEAM_WORKFLOW.md`.

---

## 4. Teammate setup after clone

```bash
git clone https://github.com/<username>/cmu-capstone.git
cd cmu-capstone
python3 -m pip install -r requirements.txt
```

**Get a YouTube API key:** follow [YOUTUBE_API_KEY.md](YOUTUBE_API_KEY.md) (Google Cloud
Console → enable YouTube Data API v3 → create key → restrict to that API).

```bash
cp .env.example .env
# Edit .env and add YOUTUBE_API_KEY
python3 test_youtube_api.py
```

Generate a personal batch file:

```bash
python3 scripts/assign_collection_batches.py \
  --assignments search_terms/assignments/collection_assignments_pilot50.csv
```

Collect videos (example for tanay):

```bash
python3 collect_youtube_data.py \
  --input search_terms/batches/tanay.csv \
  --top-n 10 \
  --run-id batch-tanay-lung-pilot
```

See `TEAM_WORKFLOW.md` for the full 6-person workflow.

> Use one API key per person to avoid shared quota conflicts.

---

## 5. Day-to-day workflow (default)

**Teammates:**

```bash
git pull origin main    # when Xinhui updates scripts or docs
# run collection locally — see TEAM_WORKFLOW.md
# upload data/runs/<run-id>/ to Shared Folder
```

**Repo admin (Xinhui):**

- Merge uploaded run folders with `assemble_dataset.py`
- Update `search_terms/search_terms.csv` from member CSVs when needed
- Push code and doc changes to GitHub

**Optional — teammates push search terms:** `git pull` → edit CSV → commit → push. Requires
Write access. Not needed for the default handoff workflow.

---

## 6. Where things live

| Content | Location |
|---------|----------|
| Scripts, search terms, English docs | **GitHub** |
| Collection CSVs, transcripts | **Shared Folder / Google Drive** |
| API keys | Local `.env` per machine |
| Bilingual personal notes | Local `local/` folder (gitignored) |

---

## 7. FAQ

**Q: Git asks for a password when pushing?**  
A: Use a GitHub Personal Access Token as the password, or run `gh auth login`.

**Q: `.env` was pushed by mistake?**  
A: Rotate the API key in Google Cloud immediately and remove the file from git history.

**Q: Teammate has no GitHub account?**  
A: Sign up free at https://github.com/signup

**Q: Repository name with spaces or non-ASCII paths?**  
A: Git handles local paths fine; use an English repo name on GitHub, e.g. `ahn-cancer-screening`.
