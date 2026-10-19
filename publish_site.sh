#!/bin/bash
# Publish site/ to the gh-pages branch (GitHub Pages). Vercel deploys the same folder from main via vercel.json.
set -e
cd "$(dirname "$0")"
.venv/bin/python site/build_replay.py
W=$(mktemp -d)
git clone -q --no-checkout https://github.com/shreenathacc22/ragcap.git "$W"
cd "$W" && git checkout -q --orphan gh-pages && git rm -rfq --cached . 2>/dev/null || true
cp -R "$OLDPWD/site/." "$W/" && touch "$W/.nojekyll"
git add -A && git -c user.name="Shreenath Shetty" -c user.email="191985630+shreenathacc22@users.noreply.github.com" commit -q -m "Publish site $(date '+%Y-%m-%d %H:%M')"
git push -q --force origin gh-pages
cd "$OLDPWD" && rm -rf "$W"
echo "published: https://shreenathacc22.github.io/ragcap/"
