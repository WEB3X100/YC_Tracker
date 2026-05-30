# Contributing

---

## Adding a Niche

1. Open a GitHub Issue using the **Niche Request** template
2. Once approved, add your entry to `config/niches.json`:

```json
{
  "slug": "your-niche",
  "name": "Your Niche Name",
  "owner": "@your-github-handle",
  "active": true,
  "extra_focus_areas": ["specific area 1", "specific area 2"],
  "extra_noise_filters": ["term to exclude"]
}
```

3. Create placeholder data directories:

```
data/your-niche/briefs/.gitkeep
data/your-niche/weekly/.gitkeep
data/your-niche/monthly/.gitkeep
```

4. Open a PR with both changes.

---

## Reporting Signal Quality

After receiving a brief, use the **Brief Feedback** issue template to rate:

- Signal quality (1–5)
- What was useful
- What was noise
- What was missed

Feedback improves the search queries in `scripts/generate_brief.py` over time.

---

## Nominating a Gem

If you spot a startup that hits 3+ gem criteria, use the **Gem Nomination** issue template:

- Company name + batch
- Which of the 7 criteria it meets
- Source URLs

Gem nominations are reviewed in the weekly synthesis.

---

## Tuning Noise Filters

If you see recurring noise in your niche, add terms to `extra_noise_filters` in `config/niches.json`:

```json
"extra_noise_filters": ["blog post", "hiring", "job board"]
```

Format: lowercase strings. A result is filtered if its title or snippet contains any filter term.

---

## Updating YC Partners

The `yc_partners` list in `config/niches.json` drives partner pulse searches. Add new partners as they join YC:

```json
{"name": "Partner Name", "x_handle": "@handle", "active": true}
```

---

## Code Changes

The main script is `scripts/generate_brief.py`. Key functions:

- `search_brave(query, count, freshness)` — Brave API wrapper
- `search_hn(query, hours_back)` — HN Algolia API (free)
- `call_claude(prompt, search_data)` — Claude synthesis
- `run_daily(niche, global_cfg)` — daily brief logic
- `run_weekly(niche, global_cfg)` — weekly synthesis
- `run_monthly(niche, global_cfg)` — monthly deep dive

PR checklist:
- [ ] Tested with `python scripts/generate_brief.py daily` locally
- [ ] No API keys committed
- [ ] `data/index.json` schema unchanged (backward compatible)
