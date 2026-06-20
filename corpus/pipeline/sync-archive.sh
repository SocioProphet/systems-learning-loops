#!/bin/bash
# sync-archive — the ONE place that writes to LaCie. Run it alone (never alongside the
# capture/vectorize grind) so a single writer can't saturate and wedge the USB disk.
# Mirrors the local brain to LaCie and drains any staging zips. Idempotent + resumable
# (rsync). If LaCie isn't mounted, it exits cleanly — never blocks.
set -u
ARCHIVE="${OCW_ARCHIVE:-/Volumes/LaCie}"
BRAIN="${OCW_BRAIN:-$HOME/Downloads/MIT OCW/_brain}"
STAGING="${OCW_STAGING:-$HOME/Downloads/ocw-staging}"

if [ ! -d "$ARCHIVE" ] || ! touch "$ARCHIVE/.w" 2>/dev/null; then
  echo "✗ archive not mounted/writable at $ARCHIVE — nothing synced (safe)."; exit 0
fi
rm -f "$ARCHIVE/.w"

echo "# sync-archive → $ARCHIVE  ($(date '+%H:%M:%S'))"

# 1) mirror local brain → LaCie/ocw-brain (per-course files; --partial survives a yank)
if [ -d "$BRAIN" ]; then
  mkdir -p "$ARCHIVE/ocw-brain"
  echo "  brain: $(find "$BRAIN" -name '*.jsonl' | wc -l | tr -d ' ') course files → LaCie/ocw-brain"
  rsync -a --partial --exclude='*.tmp' "$BRAIN/" "$ARCHIVE/ocw-brain/" 2>&1 | tail -2
fi

# 2) drain staging zips → LaCie/ocw-zips (raw archive)
if [ -d "$STAGING" ] && ls "$STAGING"/*.zip >/dev/null 2>&1; then
  mkdir -p "$ARCHIVE/ocw-zips"
  n=0
  for z in "$STAGING"/*.zip; do
    mv "$z" "$ARCHIVE/ocw-zips/" 2>/dev/null && n=$((n+1))
  done
  echo "  drained $n staging zips → LaCie/ocw-zips"
fi

echo "# done. brain on LaCie: $(find "$ARCHIVE/ocw-brain" -name '*.jsonl' 2>/dev/null | wc -l | tr -d ' ') files · zips: $(ls "$ARCHIVE/ocw-zips"/*.zip 2>/dev/null | wc -l | tr -d ' ')"
