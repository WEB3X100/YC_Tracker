# YC Startup Intelligence Tracker

> Daily automated intelligence on Y Combinator startups, OpenAI token signals, partner pulse, dead startup lessons, and gem detection. Self-updating. Zero manual prompts.

---

## What This Does

Every weekday morning, a GitHub Action runs a Python script that:

1. **Searches Brave + HN** for YC startup activity across your configured niches
2. **Finds OpenAI token grant signals** — which startups Sam Altman's team is co-endorsing
3. **Tracks YC partner posts** on X/LinkedIn — what the smartest operators are publicly excited about
4. **Analyzes dead YC startup failure patterns** (YC Graveyard lessons)
5. **Mines G2 review gaps** — competitor complaints that signal open market opportunities
6. **Detects gem candidates** — startups at the convergence of multiple approval signals
7. **Commits structured JSON briefs** to this repo

A static HTML dashboard (Vercel-hosted) reads the JSON files and renders your daily intelligence feed.

---

## Signal Hierarchy

```
OpenAI token grant confirmed       → HIGHEST SIGNAL
YC partner post (X/LinkedIn)       → Very strong
YC HN Show launch                  → Strong
Acquire.com listing (niche)        → Market validation
G2 review gap (top complaint)      → Opportunity signal
YC Graveyard failure pattern       → Avoid/pivot signal
General YC news                    → Context only
```

---

## Gem Detection

A startup becomes a **gem candidate** when it hits 3+ of these criteria:

- OpenAI token grant confirmed or rumored
- YC partner publicly mentioned / endorsed
- HN Show HN post in last 30 days
- G2 competitor has this exact complaint
- Acquire.com validates this niche has buyers
- Dead startup in same space (timing may be right now)
- Multiple YC batches have attempted this (persistent demand)

---

## Architecture

```
GitHub Actions (cron: weekdays 7am ET)
    └── scripts/generate_brief.py
            ├── Brave Search API      ($3/month)
            ├── HN Algolia API        (free)
            └── Claude API            (synthesis)
                    └── commits JSON to data/{niche}/briefs/
                            └── Vercel serves site/index.html
                                    └── reads via raw.githubusercontent.com
```

**Three schedules:**
- Daily brief: `0 12 * * 1-5` (7am Toronto, weekdays)
- Weekly synthesis: `0 13 * * 0` (Sundays)
- Monthly deep dive: `0 14 1 * *` (1st of month)

---

## Niches

Configured in `config/niches.json`. Each niche runs independently.

Data layout:
```
data/
  index.json                          ← master index
  {niche-slug}/
    briefs/YYYY-MM-DD.json
    weekly/YYYY-WXX.json
    monthly/YYYY-MM.json
```

---

## Cost

| Service | Cost |
|---------|------|
| Brave Search API | ~$3/month |
| Anthropic Claude API | ~$5–15/month |
| GitHub Actions | Free (2,000 min/month) |
| Vercel | Free tier |
| **Total** | **~$8–18/month** |

---

---

## GitHub AI Repo Tracker

A separate daily job (`scripts/track_github_repos.py`) tracks brand-new and fast-growing AI repos across all of GitHub, independent of the YC niche briefs above.

- **New 7d / New 30d** — top AI repos by stars, created in the last 7 / 30 days
- **Growing 24h / Growing 30d** — existing AI repos with the biggest star gains, computed by diffing daily snapshots of the top 100 AI repos by stars

"AI repo" = matches one of the topics: `ai`, `llm`, `machine-learning`, `artificial-intelligence`, `generative-ai`. GitHub's search API can't OR topic qualifiers in one query, so each topic is queried separately and merged.

Runs unauthenticated (60 req/hr core, 10 req/min search) — no `GITHUB_TOKEN` secret required. Snapshots older than 35 days are pruned automatically.

Data layout:
```
data/github-repos/
  index.json                ← latest pointer
  daily/YYYY-MM-DD.json     ← rendered output (new_7d, new_30d, growing_24h, growing_30d)
  snapshots/YYYY-MM-DD.json ← raw star-count snapshots used for growth diffing
```

Workflow: `.github/workflows/github-repo-tracker.yml`, runs daily at 7am Toronto. Rendered in the dashboard's **GitHub Repos** tab.

---

## Setup

See [SETUP.md](SETUP.md) for one-time configuration.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add niches, report signal quality, and nominate gems.
