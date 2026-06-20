#!/bin/bash
# ocw-grind — capture the full OCW catalog while PRESERVING the full course zips
# (video and all) for future use, WITHOUT letting the flaky LaCie wedge the box.
#
# Design: capture writes only LOCALLY — it keeps each full zip in staging and extracts
# substance to the corpus, never touching LaCie inline. When local disk runs low the
# capture self-pauses (exits). This supervisor then BATCH-DRAINS the staged zips to
# LaCie in one controlled, timeout-guarded pass (single writer; if LaCie hangs the
# drain aborts cleanly and we keep the zips staged), then resumes capture. Loop until
# the whole 2577-course catalog is done.
set -u
cd "$(dirname "$0")/.." || exit 1
STAGING="${OCW_STAGING:-$HOME/Downloads/ocw-staging}"
ARCHIVE="${OCW_ARCHIVE:-/Volumes/LaCie}/ocw-zips"
MANIFEST="$HOME/Downloads/MIT OCW/_corpus/_manifest.jsonl"
CATALOG=2577
mkdir -p "$STAGING"

count() { grep -cE '"status":"(ok|empty)"' "$MANIFEST" 2>/dev/null || echo 0; }
staged_zips() { ls "$STAGING"/*.zip 2>/dev/null | wc -l | tr -d ' '; }

drain() {
  local archroot="${OCW_ARCHIVE:-/Volumes/LaCie}"
  if [ ! -d "$archroot" ] || ! timeout 8 bash -c "touch '$archroot/.w' && rm -f '$archroot/.w'" 2>/dev/null; then
    echo "# drain: LaCie not mounted/writable — keeping $(staged_zips) zips staged for next pass"
    return 1
  fi
  local n; n=$(staged_zips)
  [ "$n" -eq 0 ] && return 0
  echo "# drain: moving $n full zips → LaCie/ocw-zips ($(du -sh "$STAGING" 2>/dev/null | cut -f1)) …"
  mkdir -p "$ARCHIVE"
  # rsync --remove-source-files: deletes each source only after it fully transfers;
  # --timeout aborts on a LaCie stall, leaving un-transferred zips safely staged.
  rsync -a --remove-source-files --timeout=180 --exclude='*.tmp' "$STAGING"/*.zip "$ARCHIVE"/ 2>>/tmp/ocw-drain.log \
    && echo "# drain: done — $(ls "$ARCHIVE"/*.zip 2>/dev/null | wc -l | tr -d ' ') zips on LaCie" \
    || echo "# drain: LaCie stalled mid-batch — $(staged_zips) zips kept staged, will retry next pass"
}

echo "# ocw-grind started $(date '+%H:%M:%S') — keep-zips, batch-drain to LaCie on low disk"
while true; do
  before=$(count)
  # capture: keep full zips locally, no inline LaCie, self-pause when local free < 15GB
  OCW_KEEP_ZIPS=1 OCW_ARCHIVE='' OCW_MIN_FREE_GB=15 OCW_DELAY_MS=3000 npx tsx scripts/ocw-capture.ts
  after=$(count)
  drain
  if [ "$after" -ge "$CATALOG" ]; then echo "# GRIND COMPLETE — $after/$CATALOG captured"; break; fi
  if [ "$after" -le "$before" ] && [ "$(staged_zips)" -eq 0 ]; then
    echo "# grind idle at $after/$CATALOG (no progress, nothing staged) — stopping"; break
  fi
  sleep 5
done
