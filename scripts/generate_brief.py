#!/usr/bin/env python3
"""
YC Builder Intelligence - Multi-Niche Brief Generator
Runs via GitHub Actions for daily / weekly / monthly briefs across all active niches.
Usage: python generate_brief.py [daily|weekly|monthly]
"""

import requests
import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"

MODE = sys.argv[1] if len(sys.argv) > 1 else "daily"


# ── CONFIG ────────────────────────────────────────────────────────────────────

def load_config():
    with open(CONFIG_DIR / "niches.json") as f:
        return json.load(f)

def active_niches(config):
    return [n for n in config.get("niches", []) if n.get("active", True)]

def niche_paths(slug):
    base = DATA_DIR / slug
    return {
        "base":    base,
        "briefs":  base / "briefs",
        "weekly":  base / "weekly",
        "monthly": base / "monthly",
        "index":   base / "index.json",
    }

def load_niche_index(slug):
    p = niche_paths(slug)["index"]
    if not p.exists():
        return {"briefs": [], "gems": [], "latest_brief": None, "latest_weekly": None, "latest_monthly": None}
    with open(p) as f:
        return json.load(f)

def save_niche_index(slug, idx):
    p = niche_paths(slug)["index"]
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(idx, f, indent=2)

def load_brief(slug, date_str):
    p = niche_paths(slug)["briefs"] / f"{date_str}.json"
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)

def load_master_index():
    p = DATA_DIR / "index.json"
    if not p.exists():
        return {"niches": {}, "last_updated": None}
    with open(p) as f:
        return json.load(f)

def save_master_index(master):
    DATA_DIR.mkdir(exist_ok=True)
    with open(DATA_DIR / "index.json", "w") as f:
        json.dump(master, f, indent=2)


# ── SEARCH ────────────────────────────────────────────────────────────────────

def search_hn(query, hours_back=24):
    cutoff = int((datetime.now() - timedelta(hours=hours_back)).timestamp())
    try:
        r = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={"query": query, "tags": "story", "numericFilters": f"created_at_i>{cutoff}", "hitsPerPage": 6},
            timeout=10,
        )
        r.raise_for_status()
        return [{"title": h.get("title",""), "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}", "points": h.get("points",0)} for h in r.json().get("hits",[])]
    except Exception as e:
        print(f"  [HN] {e}")
        return []


# ── CLAUDE ────────────────────────────────────────────────────────────────────
# Runs headless Claude Code (authenticated via CLAUDE_CODE_OAUTH_TOKEN, drawn
# from a Claude subscription) instead of metered ANTHROPIC_API_KEY billing.

def call_claude(prompt, hn_data=None, max_searches=12):
    content = prompt
    if hn_data:
        content += "\n\n## Hacker News Data (Algolia, last 24h)\n\n" + json.dumps(hn_data, indent=2)
    content += f"\n\nUse WebSearch (up to {max_searches} searches) to research the topics above before answering. Output valid JSON only as your final message. No markdown fences, no commentary."

    proc = subprocess.run(
        ["claude", "-p", content, "--output-format", "json", "--allowedTools", "WebSearch", "--max-turns", "20"],
        capture_output=True, text=True, timeout=600,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI exited {proc.returncode}: {proc.stderr[:2000]}")
    payload = json.loads(proc.stdout)
    if payload.get("is_error"):
        raise RuntimeError(f"claude CLI reported error: {payload.get('result', '')[:2000]}")
    return payload["result"]

def parse_json(text):
    t = text.strip()
    if t.startswith("```"):
        lines = t.split("\n")
        t = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(t)


# ── DAILY ─────────────────────────────────────────────────────────────────────

def run_daily(niche, global_cfg):
    today = date.today().isoformat()
    name = niche["name"]
    slug = niche["slug"]
    batch = global_cfg.get("current_batch", "W26")
    noise = global_cfg.get("global_noise_filters", []) + niche.get("extra_noise_filters", [])

    print(f"  [DAILY] {slug} | {today}")
    paths = niche_paths(slug)
    paths["briefs"].mkdir(parents=True, exist_ok=True)

    hn_data = {
        "hn_yc":   search_hn(f"YC {name}"),
        "hn_show": search_hn(f"Show HN {name}"),
    }

    prompt = f"""You are a builder intelligence agent. Generate a daily brief for a startup builder in the {name} space.

Today: {today} | Niche: {name} | YC Batch: {batch}

Noise filters (exclude anything matching these):
{json.dumps(noise)}

Signal hierarchy: OpenAI token grants > YC partner posts > YC company launches > Graveyard lessons > G2 gaps > Acquire validation > a16z signals.

Research each of the following before answering:
- OpenAI token grant news tied to YC startups (query something like: OpenAI token grant YC startup 2026)
- Recent posts from YC partners (garrytan, gustaf, daltonc, mwseibel) on X about {name}
- Y Combinator {name} startup launches (2025-2026)
- YC {name} funding/seed rounds (last 1-2 weeks)
- A dead/shutdown YC startup in {name} and why it actually failed (not the PR reason) — for graveyard_lesson
- G2 reviews for a real {name} product with verified complaints — for g2_gap
- Acquire.com listings validating demand in {name}
- a16z portfolio companies in {name}

For gem_signals: flag only if 2+ criteria confirmed.

Output EXACTLY this JSON (no markdown fences):
{{
  "date": "{today}", "niche": "{name}", "niche_slug": "{slug}", "batch": "{batch}",
  "generated": "{datetime.now().isoformat()}",
  "one_signal": "Most important development today. 2-3 sentences.",
  "openai_token_watch": "Token grant signal or 'No new token grant signal today.'",
  "partner_pulse": [{{"partner": "", "platform": "X", "signal": "", "url": ""}}],
  "company_moves": [{{"company": "", "batch": "", "what_happened": "", "relevance": "", "url": ""}}],
  "graveyard_lesson": {{"company": "", "batch": "", "what_they_built": "", "why_failed": "", "lesson": "", "source_url": ""}},
  "g2_gap": {{"product_reviewed": "", "top_complaint": "", "opportunity": ""}},
  "gem_signals": [{{"company": "", "criteria_met": [], "signal": ""}}],
  "acquire_validation": "",
  "what_to_do": [],
  "reading_list": [{{"title": "", "url": "", "why": ""}}]
}}"""

    raw = call_claude(prompt, hn_data, max_searches=14)
    try:
        result = parse_json(raw)
    except Exception as e:
        print(f"    [PARSE ERROR] {e}")
        result = {"date": today, "niche": name, "niche_slug": slug, "parse_error": True, "raw": raw[:2000]}

    out = paths["briefs"] / f"{today}.json"
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"    [OK] {out}")
    return result


# ── WEEKLY ───────────────────────────────────────────────────────────────────

def run_weekly(niche, global_cfg):
    today = date.today().isoformat()
    name = niche["name"]
    slug = niche["slug"]
    print(f"  [WEEKLY] {slug} | {today}")
    paths = niche_paths(slug)
    paths["weekly"].mkdir(parents=True, exist_ok=True)

    past_briefs = []
    for i in range(7):
        d = (date.today() - timedelta(days=i)).isoformat()
        b = load_brief(slug, d)
        if b and not b.get("parse_error"):
            past_briefs.append({k: v for k, v in b.items() if k in ["date", "one_signal", "gem_signals", "graveyard_lesson", "g2_gap"]})

    prompt = f"""Weekly synthesis for {name}. Week ending {today}.

Past 7 daily briefs:
{json.dumps(past_briefs, indent=2)}

Research this week's news before answering:
- YC {name} startup news (past week)
- G2 reviews for {name} products (past week)
- Acquire.com listings for {name} startups sold/revenue
- YC {name} startup failures/shutdowns (2022-2025) and why
- Y Combinator batch trends/themes in {name} (2025-2026)

Synthesize category patterns, gem updates, failure patterns, G2 gap, acquire validation.

Output EXACTLY this JSON (no markdown fences):
{{
  "week_ending": "{today}", "niche": "{name}", "niche_slug": "{slug}",
  "generated": "{datetime.now().isoformat()}",
  "week_in_one_paragraph": "",
  "top_category_patterns": [{{"category": "", "appearances": 0, "trend": "Rising|Stable|Fading", "action": "Watch|Deep dive|Remove"}}],
  "gem_updates": {{"newly_flagged": [], "still_active": [], "dropped": []}},
  "graveyard_pattern": "",
  "g2_gap_summary": "",
  "acquire_validation": "",
  "openai_token_summary": "",
  "context_update_proposals": {{"add_noise_filters": [], "source_priority_changes": [], "new_focus_areas": [], "deprioritize": []}},
  "reading_list": [{{"title": "", "url": "", "why": ""}}]
}}"""

    raw = call_claude(prompt, max_searches=8)
    try:
        result = parse_json(raw)
    except Exception as e:
        result = {"week_ending": today, "niche": name, "niche_slug": slug, "parse_error": True}

    week_num = date.today().isocalendar()[1]
    out = paths["weekly"] / f"{date.today().year}-W{week_num:02d}.json"
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"    [OK] {out}")
    return result


# ── MONTHLY ───────────────────────────────────────────────────────────────────

def run_monthly(niche, global_cfg):
    today = date.today().isoformat()
    month = date.today().strftime("%Y-%m")
    name = niche["name"]
    slug = niche["slug"]
    print(f"  [MONTHLY] {slug} | {month}")
    paths = niche_paths(slug)
    paths["monthly"].mkdir(parents=True, exist_ok=True)

    past_weeklies = []
    for wf in sorted(paths["weekly"].glob("*.json"))[-5:]:
        with open(wf) as f:
            d = json.load(f)
            past_weeklies.append({k: v for k, v in d.items() if k in ["week_ending", "week_in_one_paragraph", "graveyard_pattern"]})

    prompt = f"""Monthly deep dive for {name}. Month: {month}.

Past weekly syntheses:
{json.dumps(past_weeklies, indent=2)}

Research this month's landscape before answering:
- Y Combinator {name} news/funding this month
- YC {name} startup post-mortems/failures (2022-2025)
- a16z portfolio companies in {name}
- Acquire.com {name} businesses sold/revenue
- {name} AI startup market direction/trend for 2026

Extract lasting failure patterns, gem status, market direction, accelerator landscape, recursive improvement.

Output EXACTLY this JSON (no markdown fences):
{{
  "month": "{month}", "niche": "{name}", "niche_slug": "{slug}",
  "generated": "{datetime.now().isoformat()}",
  "month_verdict": "",
  "failure_patterns": [{{"pattern": "", "examples": [], "root_cause": "", "how_to_avoid": ""}}],
  "gem_final_status": [{{"company": "", "status": "Promoted|Maintained|Dropped", "reason": "", "criteria_met": 0}}],
  "market_direction": "",
  "accelerator_landscape": {{"yc": "", "a16z": "", "gap": ""}},
  "acquire_market_health": "",
  "recursive_loop_updates": {{"research_context_changes": [], "noise_filters_final": [], "new_sources_proven": [], "sources_to_drop": []}},
  "next_month_thesis": "",
  "reading_list": [{{"title": "", "url": "", "why": ""}}]
}}"""

    raw = call_claude(prompt, max_searches=10)
    try:
        result = parse_json(raw)
    except Exception as e:
        result = {"month": month, "niche": name, "niche_slug": slug, "parse_error": True}

    out = paths["monthly"] / f"{month}.json"
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"    [OK] {out}")
    return result


# ── INDEX UPDATE ───────────────────────────────────────────────────────────────

def update_indexes(mode, niche, result):
    slug = niche["slug"]
    name = niche["name"]
    today = date.today().isoformat()

    # Per-niche index
    idx = load_niche_index(slug)

    if mode == "daily":
        idx["latest_brief"] = today
        if today not in idx.get("briefs", []):
            idx.setdefault("briefs", []).insert(0, today)
        idx["briefs"] = idx["briefs"][:120]
        for gem in result.get("gem_signals", []):
            company = gem.get("company", "")
            if not company:
                continue
            existing = next((g for g in idx.get("gems", []) if g["company"] == company), None)
            if existing:
                existing["signals_count"] = existing.get("signals_count", 0) + 1
                existing["last_seen"] = today
                for c in gem.get("criteria_met", []):
                    if c not in existing.get("criteria_met", []):
                        existing.setdefault("criteria_met", []).append(c)
            else:
                idx.setdefault("gems", []).append({"company": company, "first_seen": today, "last_seen": today, "signals_count": 1, "criteria_met": gem.get("criteria_met", [])})
    elif mode == "weekly":
        week_num = date.today().isocalendar()[1]
        idx["latest_weekly"] = f"{date.today().year}-W{week_num:02d}"
    elif mode == "monthly":
        idx["latest_monthly"] = date.today().strftime("%Y-%m")

    idx["last_run"] = datetime.now().isoformat()
    save_niche_index(slug, idx)

    # Master index (all niches in one file for the dashboard)
    master = load_master_index()
    master.setdefault("niches", {})[slug] = {
        "name": name,
        "slug": slug,
        "latest_brief":   idx.get("latest_brief"),
        "latest_weekly":  idx.get("latest_weekly"),
        "latest_monthly": idx.get("latest_monthly"),
        "briefs_count":   len(idx.get("briefs", [])),
        "gems_count":     len(idx.get("gems", [])),
        "last_run":       idx.get("last_run"),
    }
    master["last_updated"] = datetime.now().isoformat()
    save_master_index(master)


# ── MAIN ─────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)
    cfg = load_config()
    niches = active_niches(cfg)

    if not niches:
        print("No active niches in config/niches.json")
        sys.exit(1)

    print(f"Mode: {MODE} | Active niches: {[n['slug'] for n in niches]}")

    for niche in niches:
        if MODE == "daily":
            result = run_daily(niche, cfg)
        elif MODE == "weekly":
            result = run_weekly(niche, cfg)
        elif MODE == "monthly":
            result = run_monthly(niche, cfg)
        else:
            print(f"Unknown mode: {MODE}")
            sys.exit(1)
        update_indexes(MODE, niche, result)

    print("Done.")
