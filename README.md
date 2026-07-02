# YC Startup Intelligence Tracker

> Daily automated intelligence on Y Combinator startups, OpenAI token signals, partner pulse, dead startup lessons, and gem detection. Self-updating. Zero manual prompts.

---

## What This Does

Every weekday morning, a GitHub Action runs a Python script that:

1. **Searches the web (via headless Claude Code's WebSearch tool) + HN** for YC startup activity across your configured niches
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
            ├── HN Algolia API        (free)
            └── headless Claude Code  (WebSearch + synthesis, via subscription OAuth token)
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
| Claude subscription (Pro/Max, already owned) | $0 extra — usage counts against your plan, not metered API billing |
| GitHub Actions | Free (2,000 min/month) |
| Vercel | Free tier |
| **Total** | **$0 extra** (subject to your subscription's usage limits — see [SETUP.md](SETUP.md)) |

---

## Setup

See [SETUP.md](SETUP.md) for one-time configuration.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add niches, report signal quality, and nominate gems.
