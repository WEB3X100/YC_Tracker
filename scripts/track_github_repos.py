#!/usr/bin/env python3
"""
GitHub AI Repo Tracker
Tracks brand-new AI repos and fastest-growing AI repos using the unauthenticated
GitHub Search API. Runs daily via GitHub Actions.

Categories produced:
  - new_7d:   top AI repos created in the last 7 days, ranked by stars
  - new_30d:  top AI repos created in the last 30 days, ranked by stars
  - growing_24h: AI repos with the biggest star gain in the last 24h
  - growing_30d: AI repos with the biggest star gain in the last 30 days

Growth is computed by diffing daily snapshots of a broad AI-repo universe
(top 100 by stars), so no per-repo API calls are needed.
"""

import requests
import json
import time
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "github-repos"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
DAILY_DIR = DATA_DIR / "daily"

# GitHub's repository search API does not support boolean OR between
# qualifiers, so each AI topic is queried separately and results are merged.
AI_TOPICS = ["ai", "llm", "machine-learning", "artificial-intelligence", "generative-ai"]

HEADERS = {"Accept": "application/vnd.github+json"}
SEARCH_URL = "https://api.github.com/search/repositories"
RATE_LIMIT_SLEEP = 6.5  # unauthenticated search API allows 10 req/min


def gh_search(query, sort="stars", per_page=30):
    try:
        r = requests.get(
            SEARCH_URL,
            headers=HEADERS,
            params={"q": query, "sort": sort, "order": "desc", "per_page": per_page},
            timeout=15,
        )
        r.raise_for_status()
        return r.json().get("items", [])
    except Exception as e:
        print(f"  [GH SEARCH ERROR] {query[:60]}: {e}")
        return []


def gh_search_topics(extra_query, per_page_each=15, sort="stars"):
    """Query each AI topic separately (qualifiers can't be OR'd) and merge by full_name."""
    seen = {}
    for topic in AI_TOPICS:
        query = f"topic:{topic} {extra_query}".strip()
        items = gh_search(query, sort=sort, per_page=per_page_each)
        for item in items:
            seen[item["full_name"]] = item
        time.sleep(RATE_LIMIT_SLEEP)
    return list(seen.values())


def repo_summary(item):
    return {
        "full_name": item.get("full_name"),
        "url": item.get("html_url"),
        "description": item.get("description") or "",
        "stars": item.get("stargazers_count", 0),
        "created_at": item.get("created_at"),
        "language": item.get("language"),
    }


def load_snapshot(day_iso):
    p = SNAPSHOT_DIR / f"{day_iso}.json"
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)


def save_snapshot(day_iso, repos):
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    with open(SNAPSHOT_DIR / f"{day_iso}.json", "w") as f:
        json.dump(repos, f, indent=2)


def closest_snapshot(target_day):
    """Find the snapshot file closest to (on or before) target_day, within 3 days."""
    for delta in range(0, 4):
        d = (target_day - timedelta(days=delta)).isoformat()
        snap = load_snapshot(d)
        if snap is not None:
            return d, snap
    return None, None


def compute_growth(today_snapshot, past_snapshot, top_n=10):
    past_by_name = {r["full_name"]: r["stars"] for r in past_snapshot}
    deltas = []
    for r in today_snapshot:
        prev_stars = past_by_name.get(r["full_name"])
        if prev_stars is None:
            continue
        gain = r["stars"] - prev_stars
        if gain <= 0:
            continue
        deltas.append({**r, "star_gain": gain})
    deltas.sort(key=lambda x: x["star_gain"], reverse=True)
    return deltas[:top_n]


def main():
    today = date.today()
    today_iso = today.isoformat()
    print(f"[GH-REPOS] {today_iso}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    cutoff_7d = (today - timedelta(days=7)).isoformat()
    cutoff_30d = (today - timedelta(days=30)).isoformat()

    new_7d_raw = gh_search_topics(f"created:>={cutoff_7d}", per_page_each=10)
    new_30d_raw = gh_search_topics(f"created:>={cutoff_30d}", per_page_each=10)
    universe_raw = gh_search_topics("", per_page_each=30)

    def top_by_stars(items, n):
        return sorted([repo_summary(r) for r in items], key=lambda x: x["stars"], reverse=True)[:n]

    new_7d = top_by_stars(new_7d_raw, 10)
    new_30d = top_by_stars(new_30d_raw, 5)
    universe = top_by_stars(universe_raw, 100)

    save_snapshot(today_iso, universe)

    snap_1d_date, snap_1d = closest_snapshot(today - timedelta(days=1))
    snap_30d_date, snap_30d = closest_snapshot(today - timedelta(days=30))

    growing_24h = compute_growth(universe, snap_1d, top_n=10) if snap_1d else []
    growing_30d = compute_growth(universe, snap_30d, top_n=10) if snap_30d else []

    result = {
        "date": today_iso,
        "generated": datetime.now().isoformat(),
        "new_7d": new_7d,
        "new_30d": new_30d,
        "growing_24h": growing_24h,
        "growing_24h_baseline": snap_1d_date,
        "growing_30d": growing_30d,
        "growing_30d_baseline": snap_30d_date,
    }

    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    with open(DAILY_DIR / f"{today_iso}.json", "w") as f:
        json.dump(result, f, indent=2)

    # prune snapshots older than 35 days to keep repo size small
    cutoff_prune = today - timedelta(days=35)
    for f in SNAPSHOT_DIR.glob("*.json"):
        try:
            d = date.fromisoformat(f.stem)
        except ValueError:
            continue
        if d < cutoff_prune:
            f.unlink()

    index = {"latest": today_iso, "last_run": datetime.now().isoformat()}
    with open(DATA_DIR / "index.json", "w") as f:
        json.dump(index, f, indent=2)

    print(f"  [OK] new_7d={len(new_7d)} new_30d={len(new_30d)} growing_24h={len(growing_24h)} growing_30d={len(growing_30d)}")


if __name__ == "__main__":
    main()
