# Setup Guide

One-time setup to get the YC Startup Intelligence Tracker running.

---

## Prerequisites

- GitHub account with Actions enabled on this repo
- A Claude subscription (Pro or Max) with Claude Code access — no separate Anthropic API billing needed
- Vercel account (free) for dashboard hosting

---

## Step 1: Generate a Claude Code OAuth Token

The workflows run headless Claude Code, authenticated against your Claude subscription instead of a metered API key — generation usage draws from your monthly plan, not pay-per-token billing.

On your own machine, with the [Claude Code CLI](https://claude.com/product/claude-code) installed and logged into your subscription, run:

```
claude setup-token
```

This prints a long-lived token. Copy it.

---

## Step 2: Add Repository Secrets

Go to **Settings → Secrets and Variables → Actions → New repository secret** and add:

| Secret Name | Value |
|-------------|-------|
| `CLAUDE_CODE_OAUTH_TOKEN` | The token printed by `claude setup-token` |

That's the only secret required — no `ANTHROPIC_API_KEY`, no Brave key.

Never commit this value. GitHub Secrets are the only safe place to store it.

**Note:** subscription plans have usage limits designed for interactive coding sessions, not scheduled bulk automation. If runs start failing with rate-limit errors, that's why — keep the niche count small (see Step 3) or fall back to a metered `ANTHROPIC_API_KEY` if you need higher throughput.

---

## Step 3: Configure Your Niches

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

**Cost tip**: Start with 1–2 niches — each active niche adds more generation calls per run, which counts against your subscription's usage limits.

---

## Step 4: Create Data Directories

For each niche slug, create placeholder files:

```
data/{your-slug}/briefs/.gitkeep
data/{your-slug}/weekly/.gitkeep
data/{your-slug}/monthly/.gitkeep
```

Commit and push these.

---

## Step 5: Enable GitHub Actions

1. Go to the **Actions** tab in this repo
2. If prompted, click **I understand my workflows, go ahead and enable them**
3. To trigger a manual first run: **Actions → Daily Brief → Run workflow**

The first run takes ~2 minutes. Check the run log if it fails.

---

## Step 6: Deploy the Dashboard

1. Go to [vercel.com](https://vercel.com) → **Add New Project**
2. Import this GitHub repository
3. Set **Root Directory** to `site`
4. Leave all other settings as defaults
5. Click **Deploy**

Vercel auto-deploys on every push to `main` — so every morning brief auto-refreshes your dashboard.

---

## Step 7: Verify Everything Works

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
