#!/usr/bin/env python3
"""Minimal validator for sources.yaml structure.

This is intentionally lightweight. It checks:
- required keys
- unique ids
- allowed type values
"""

import sys, yaml
from pathlib import Path

ALLOWED_TYPES = {"primary", "secondary", "tertiary"}

def main():
    p = Path(__file__).resolve().parents[1] / "kb" / "sources" / "sources.yaml"
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    sources = data.get("sources", [])
    ids = [s.get("id") for s in sources]
    if any(i is None for i in ids):
        raise SystemExit("ERROR: some sources missing 'id'")
    if len(ids) != len(set(ids)):
        raise SystemExit("ERROR: duplicate source ids detected")
    for s in sources:
        for k in ["id", "title", "type", "url"]:
            if k not in s:
                raise SystemExit(f"ERROR: source {s.get('id')} missing required key '{k}'")
        if s["type"] not in ALLOWED_TYPES:
            raise SystemExit(f"ERROR: source {s['id']} has invalid type {s['type']}")
    print("OK: sources.yaml passes minimal validation")

if __name__ == "__main__":
    try:
        import yaml  # noqa
    except Exception:
        raise SystemExit("ERROR: pyyaml required. Install with: pip install pyyaml")
    main()
