#!/bin/bash
# Full site build. Order matters:
#   1. guides + tools generate their pages (with empty chrome markers)
#   2. the localizer templates the 13 homepages from index.html
#   3. chrome.py fills the shared header/footer into every page — LAST, so the
#      localizer never copies English chrome into a locale page
#   4. sitemap.py derives sitemap.xml from what is now on disk
set -euo pipefail
cd "$(dirname "$0")/.."
node translate/build.js
node tools/build.js | head -1
python3 _build/build_locales.py | tail -1
python3 _build/chrome.py --strict
python3 _build/sitemap.py
python3 _build/audit.py --problems | tail -3
