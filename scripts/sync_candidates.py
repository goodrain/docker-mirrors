#!/usr/bin/env python3
"""Sync docker.io mirror candidates from the dongyubin/DockerHub README.

Fetches the README, extracts candidate mirror URLs, probes each /v2/ endpoint
and merges the alive ones into mirrors.json (existing entries are re-probed
too; dead ones are dropped). Designed to run in CI and open a PR for a human
to review — never push the result directly.
"""
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

README_URLS = [
    "https://raw.githubusercontent.com/dongyubin/DockerHub/main/README.md",
]
MIRRORS_FILE = Path(__file__).resolve().parent.parent / "mirrors.json"
PROBE_TIMEOUT = 8
# Hosts that show up in the README but are not registry mirrors.
HOST_BLACKLIST = {
    "github.com", "raw.githubusercontent.com", "img.shields.io",
    "www.dongyubin.com", "hub.docker.com", "docs.docker.com",
}

URL_RE = re.compile(r"https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def fetch_readme():
    last_err = None
    for url in README_URLS:
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                return resp.read().decode("utf-8", "replace")
        except Exception as exc:  # noqa: BLE001
            last_err = exc
    raise SystemExit(f"failed to fetch README from all sources: {last_err}")


def extract_candidates(text):
    seen, result = set(), []
    for raw in URL_RE.findall(text):
        host = raw.split("://", 1)[1].rstrip("/")
        if host in HOST_BLACKLIST or host in seen:
            continue
        seen.add(host)
        result.append(raw.rstrip("/"))
    return result


def probe(url):
    endpoint = url.rstrip("/") + "/v2/"
    try:
        req = urllib.request.Request(endpoint, method="GET")
        with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT) as resp:
            return url if resp.status in (200, 401) else None
    except urllib.error.HTTPError as exc:
        return url if exc.code == 401 else None
    except Exception:  # noqa: BLE001
        return None


def main():
    current = json.loads(MIRRORS_FILE.read_text())
    existing = {m["url"]: m for m in current["mirrors"]}
    candidates = list(existing) + [
        u for u in extract_candidates(fetch_readme()) if u not in existing
    ]

    with ThreadPoolExecutor(max_workers=10) as pool:
        alive = [u for u in pool.map(probe, candidates) if u]

    mirrors = [existing.get(u, {"url": u, "note": "from dongyubin/DockerHub"}) for u in alive]
    if [m["url"] for m in mirrors] == [m["url"] for m in current["mirrors"]]:
        print("no change")
        return 0

    current["mirrors"] = mirrors
    current["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    MIRRORS_FILE.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n")
    print(f"updated: {len(mirrors)} alive mirrors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
