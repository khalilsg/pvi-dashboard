#!/usr/bin/env bash
# Pull the latest 2026 results from the election-tracker repo and rebuild the dashboard.
# Usage: ./scripts/update.sh          (then commit and push; GitHub Pages redeploys)
set -euo pipefail
cd "$(dirname "$0")/.."
BASE="https://raw.githubusercontent.com/Tom-Neverwinter/election-tracker/main"
tmp=$(mktemp -d)
curl -fsSL "$BASE/results-data.js" -o "$tmp/results-data.js"
curl -fsSL "$BASE/history.js" -o "$tmp/history.js"
mv "$tmp/results-data.js" "$tmp/history.js" data/raw/
python3 scripts/build_data.py
python3 scripts/build_site.py
