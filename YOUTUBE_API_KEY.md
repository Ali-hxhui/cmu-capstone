# How to Get a YouTube Data API Key

Each team member should create **their own** API key in Google Cloud. This spreads out the
daily quota (~10,000 units per project by default) .

---

## Step 1: Open Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with a Google account (personal Gmail or school account both work)

---

## Step 2: Create a project

1. Click the **project dropdown** at the top (next to "Google Cloud")
2. Click **New Project**
3. Enter a name, e.g. `cmu-cancer-screening-yourname`
4. Click **Create**, then select the new project from the dropdown

---

## Step 3: Enable YouTube Data API v3

1. In the left menu, go to **APIs & Services** → **Library**
   - Direct link: [API Library](https://console.cloud.google.com/apis/library)
2. Search for **YouTube Data API v3**
3. Click it, then click **Enable**

> This project only needs the **Data API** for metadata collection. Transcript extraction
> (`extract_transcripts.py`) does **not** use this key.

---

## Step 4: Create an API key

1. Go to **APIs & Services** → **Credentials**
   - Direct link: [Credentials](https://console.cloud.google.com/apis/credentials)
2. Click **+ Create Credentials** → **API key**
3. Copy the key shown in the dialog (you can paste it into `.env` now)
4. Click **Close** (or **Edit API key** to add restrictions — see Step 5)

---

## Step 5: Restrict the key (recommended)

On the key edit page:

**API restrictions**

1. Select **Restrict key**
2. Under "Select APIs", choose **YouTube Data API v3** only
3. Save

**Application restrictions** (optional for local scripts)

- For running scripts on your laptop, **None** is fine
- If you deploy to a fixed server later, restrict by IP address

---

## Step 6: Add the key to this project

```bash
cp .env.example .env
```

Edit `.env`:

```env
YOUTUBE_API_KEY=AIza...your_actual_key_here
```

**Never commit `.env` to git.** It is already listed in `.gitignore`.

---

## Step 7: Verify the key works

```bash
python3 test_youtube_api.py
```

Expected output on success:

```
API key loaded.
Test search succeeded.
Sample video title: ...
```

If you see an error:

| Error | Likely cause | Fix |
|-------|--------------|-----|
| `YOUTUBE_API_KEY is missing` | `.env` not created or wrong variable name | Copy `.env.example` → `.env` |
| `403 Forbidden` / `API key not valid` | Wrong key, or API not enabled | Re-copy key; confirm YouTube Data API v3 is enabled |
| `403 quotaExceeded` | Daily quota used up | Wait until quota resets (midnight Pacific Time) or use another team member's key/project |
| `400 badRequest` | Malformed key | Regenerate key in Cloud Console |

---

## Quota basics for this project

| Action | Approx. cost |
|--------|----------------|
| One search query (`collect_youtube_data.py`) | ~100 units |
| Default daily budget | 10,000 units |
| Rough capacity per day | ~100 search terms |

Check usage: **APIs & Services** → **Dashboard** → **YouTube Data API v3** → **Quotas**.

For the full corpus (200 search terms), split work across **6 people** and **2+ days**, or
request a quota increase in the Cloud Console (approval is not guaranteed for new projects).

---

## Security checklist

- [ ] One key per team member (separate Google Cloud projects)
- [ ] Key restricted to YouTube Data API v3 only
- [ ] `.env` stays local — never pushed to GitHub
- [ ] If a key is exposed, **delete it** in Credentials and create a new one

---

## Related commands

See [README.md](README.md) for the day-1 collect + transcript commands.
