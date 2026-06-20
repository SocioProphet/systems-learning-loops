#!/bin/bash
# pull-state.sh — on the BIG machine: pull the OCW corpus + vector brain + code repos
# from GCS and lay them out to resume the grind. Run after cloning this repo.
set -e
B="${OCW_BUCKET:-gs://sourceos-artifacts-socioprophet/ocw-corpus}"
mkdir -p "$HOME/Downloads/MIT OCW" "$HOME/dev"
echo "# pulling captured corpus + vectors (state.tar) from $B …"
gsutil cp "$B/state.tar" - | tar xf - -C "$HOME/Downloads/MIT OCW"
echo "# pulling code repos (Noetica + hellgraph) …"
gsutil cp "$B/code.tar.gz" - | tar xzf - -C "$HOME/dev"
echo "# pulled: $(find "$HOME/Downloads/MIT OCW/_corpus" -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ') corpus dirs · $(find "$HOME/Downloads/MIT OCW/_brain" -name '*.jsonl' 2>/dev/null | wc -l | tr -d ' ') vectorized courses"
echo "# next:"
echo "#   bash ~/dev/Noetica/agent-machine/scripts/setup-new-mac.sh   # node/ollama/python + pull models + build"
echo "#   cd  ~/dev/Noetica/agent-machine"
echo "#   bash scripts/ocw-grind.sh                                    # resume CAPTURE (skips done via manifest)"
echo "#   OLLAMA_HOST=http://127.0.0.1:11434 npx tsx scripts/build-corpus.ts   # resume VECTORIZE"
