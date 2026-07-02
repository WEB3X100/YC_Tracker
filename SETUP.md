# Setup Guide

One-time setup to get the YC Startup Intelligence Tracker running.

---

## Prerequisites

- GitHub account with Actions enabled on this repo
- Anthropic API key — get at [console.anthropic.com](https://console.anthropic.com) (web search is billed per-search on top of normal token usage; see [Cost](README.md#cost))
- Vercel account (free) for dashboard hosting

---

## Step 1: Add Repository Secrets

Go to **Settings → Secrets and Variables → Actions → New repository secret** and add:

| Secret Name | Value |
|-------------|-------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (starts with `sk-ant-`) |

That's the only secret required — the script uses Claude's built-in web search tool instead of a separate search API, so there's no Brave key to manage.

Never commit this value. GitHub Secrets are the only safe place to store it.

---

## Step 2: Configure Your Niches

Edit `config/niches.json` and add your niches:

```json
{
  "niches": [
    {
      "slug": "ai-developer-tools",
      "name": "AI Developer Tools",
      "owner": "@your-github-handle",
      "active": true
    }
  ]
}
```

**Slug rules**: lowercase, hyphens only, no spaces. This becomes the directory name under `data/`.

**Cost tip**: Start with 1–2 niches. Each active niche adds ~$1–3/month to API costs.

---

## Step 3: Create Data Directories

For each niche slug, create placeholder files:

```
data/{your-slug}/briefs/.gitkeep
data/{your-slug}/weekly/.gitkeep
data/{your-slug}/monthly/.gitkeep
```

Commit and push these.

---

## Step 4: Enable GitHub Actions

1. Go to the **Actions** tab in this repo
2. If prompted, click **I understand my workflows, go ahead and enable them**
3. To trigger a manual first run: **Actions → Daily Brief → Run workflow**

The first run takes ~2 minutes. Check the run log if it fails.

---

## Step 5: Deploy the Dashboard

1. Go to [vercel.com](https://vercel.com) → **Add New Project**
2. Import this GitHub repository
3. Set **Root Directory** to `site`
4. Leave all other settings as defaults
5. Click **Deploy**

Vercel auto-deploys on every push to `main` — so every morning brief auto-refreshes your dashboard.

---

## Step 6: Verify Everything Works

After the first successful GitHub Actions run:

1. Check `data/index.json` was committed with a `latest_brief` value
2. Check `data/{slug}/briefs/YYYY-MM-DD.json` exists with content
3. Open your Vercel URL — the niche dropdown should populate, Today tab should show the brief

---

## Updating for a New YC Batch

Update `"current_batch"` in `config/niches.json` each new YC cohort:
```json
"current_batch": "S26"
```

Current batch cadence: W = Winter (Jan), S = Summer (Jun).
