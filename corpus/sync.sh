#!/bin/bash
# sync.sh — snapshot the local vector brain + capture manifest into this repo and push.
# Run anytime (or on a schedule) to keep the repo current with the grind. LFS-aware.
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
BRAIN="${OCW_BRAIN:-$HOME/Downloads/MIT OCW/_brain}"
MAN="$HOME/Downloads/MIT OCW/_corpus/_manifest.jsonl"
rsync -a --exclude='*.tmp' "$BRAIN/" "$REPO/corpus/vectors/"
[ -f "$MAN" ] && cp "$MAN" "$REPO/corpus/catalog/capture_manifest.jsonl"
cd "$REPO"
git add corpus/vectors corpus/catalog/capture_manifest.jsonl
n=$(find corpus/vectors -name '*.jsonl' | wc -l | tr -d ' ')
git diff --cached --quiet && { echo "sync: nothing new ($n courses)"; exit 0; }
git commit -q -m "corpus: sync vectors — $n courses vectorized"
git push origin main && echo "sync: pushed — $n courses on the remote"
