#!/bin/bash
# push-state.sh — from the ACTIVE machine: re-bundle the corpus + brain to GCS (full
# snapshot). Run to publish progress so another machine can pull-state and continue.
set -e
B="${OCW_BUCKET:-gs://sourceos-artifacts-socioprophet/ocw-corpus}"
cd "$HOME/Downloads/MIT OCW"
echo "# streaming state.tar → $B ($(find _brain -name '*.jsonl'|wc -l|tr -d ' ') vectorized courses)…"
tar cf - _brain _corpus | gsutil cp - "$B/state.tar"
echo "# done."
