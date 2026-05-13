#!/usr/bin/env python3
"""Validate the lawful-learning Phase 7 research pack.

Checks the repo-local knowledge-pack artifacts added for lawful-learning:
- source registry structure and unique LL source ids
- claim registry structure, unique claim ids, and source_ref integrity
- presence of the seven-invariant pattern synthesis
- presence of the ontology and its ten invariant instances

This is intentionally lightweight. It validates structural coherence,
not the truth of the claims and not runtime execution.
"""

from __future__ import annotations

from pathlib import Path
import sys

try:
    import yaml  # type: ignore
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"ERROR: pyyaml required. Install with: pip install pyyaml ({exc})")

ROOT = Path(__file__).resolve().parents[1]

SOURCE_PATH = ROOT / "kb" / "sources" / "lawful-learning-sources.yaml"
CLAIM_PATH = ROOT / "kb" / "claims" / "lawful-learning-claims.yaml"
PATTERN_PATH = ROOT / "kb" / "patterns" / "lawful-learning-seven-invariants.md"
ONTOLOGY_PATH = ROOT / "ontology" / "lawful-learning.ttl"

ALLOWED_SOURCE_TYPES = {"primary", "secondary", "tertiary"}
ALLOWED_TAGS = {"M", "T", "S", "E", "G"}

REQUIRED_INVARIANTS = {
    "adapter_dag_acyclic",
    "black_boxing_composes",
    "replay_seal_for_composed_trace",
    "may_wigner_monitor_declared",
    "control_data_plane_separation",
    "tail_audit_allocated",
    "emergent_discretization_logged",
    "composition_superposition_declared",
    "anti_satisficing_continuation",
    "epistemic_non_collapse",
}

REQUIRED_CLAIM_FIELDS_BY_TAG = {
    "M": "mathematical_dependency",
    "T": "typological_parallel_target",
    "S": "speculative_test_artifact",
    "E": "empirical_measurement_ref",
    "G": "governance_invariant_ref",
}


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"ERROR: missing required file: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"ERROR: expected mapping in {path}")
    return data


def validate_sources() -> set[str]:
    data = _load_yaml(SOURCE_PATH)
    sources = data.get("sources", [])
    if not isinstance(sources, list) or not sources:
        raise SystemExit("ERROR: lawful-learning-sources.yaml must contain non-empty sources list")

    ids: list[str] = []
    for source in sources:
        if not isinstance(source, dict):
            raise SystemExit("ERROR: each source entry must be a mapping")
        for key in ["id", "title", "type", "url"]:
            if key not in source:
                raise SystemExit(f"ERROR: source {source.get('id')} missing required key {key}")
        source_id = source["id"]
        if not isinstance(source_id, str) or not source_id.startswith("LL-SRC-"):
            raise SystemExit(f"ERROR: lawful-learning source id must start with LL-SRC-: {source_id}")
        if source["type"] not in ALLOWED_SOURCE_TYPES:
            raise SystemExit(f"ERROR: source {source_id} has invalid type {source['type']}")
        ids.append(source_id)

    if len(ids) != len(set(ids)):
        raise SystemExit("ERROR: duplicate lawful-learning source ids detected")
    return set(ids)


def validate_claims(source_ids: set[str]) -> set[str]:
    data = _load_yaml(CLAIM_PATH)
    claims = data.get("claims", [])
    if not isinstance(claims, list) or not claims:
        raise SystemExit("ERROR: lawful-learning-claims.yaml must contain non-empty claims list")

    ids: list[str] = []
    claim_ids: list[str] = []
    for claim in claims:
        if not isinstance(claim, dict):
            raise SystemExit("ERROR: each claim entry must be a mapping")
        for key in ["id", "claim_id", "tag", "status", "summary", "source_refs"]:
            if key not in claim:
                raise SystemExit(f"ERROR: claim {claim.get('id')} missing required key {key}")

        pack_id = claim["id"]
        claim_id = claim["claim_id"]
        if not isinstance(pack_id, str) or not pack_id.startswith("LL-CLAIM-"):
            raise SystemExit(f"ERROR: claim pack id must start with LL-CLAIM-: {pack_id}")
        if not isinstance(claim_id, str) or not claim_id.startswith("claim."):
            raise SystemExit(f"ERROR: claim_id must start with claim.: {claim_id}")

        tag_tokens = set(str(claim["tag"]).split("|"))
        invalid_tags = tag_tokens - ALLOWED_TAGS
        if invalid_tags:
            raise SystemExit(f"ERROR: claim {pack_id} has invalid tags: {sorted(invalid_tags)}")
        for tag in tag_tokens:
            required_field = REQUIRED_CLAIM_FIELDS_BY_TAG[tag]
            if not str(claim.get(required_field, "")).strip():
                raise SystemExit(f"ERROR: claim {pack_id} tag {tag} requires {required_field}")
        if "|" in str(claim["tag"]) and not str(claim.get("claim_demarcation", "")).strip():
            raise SystemExit(f"ERROR: mixed-tag claim {pack_id} requires claim_demarcation")

        refs = claim.get("source_refs", [])
        if not isinstance(refs, list) or not refs:
            raise SystemExit(f"ERROR: claim {pack_id} must have non-empty source_refs")
        missing_refs = sorted(set(refs) - source_ids)
        if missing_refs:
            raise SystemExit(f"ERROR: claim {pack_id} references unknown sources: {missing_refs}")

        ids.append(pack_id)
        claim_ids.append(claim_id)

    if len(ids) != len(set(ids)):
        raise SystemExit("ERROR: duplicate lawful-learning claim ids detected")
    if len(claim_ids) != len(set(claim_ids)):
        raise SystemExit("ERROR: duplicate lawful-learning claim_id values detected")
    return set(ids)


def validate_pattern(claim_ids: set[str]) -> None:
    if not PATTERN_PATH.exists():
        raise SystemExit(f"ERROR: missing pattern file: {PATTERN_PATH}")
    text = PATTERN_PATH.read_text(encoding="utf-8")
    for invariant in REQUIRED_INVARIANTS:
        if invariant not in text:
            raise SystemExit(f"ERROR: pattern file missing invariant reference: {invariant}")
    missing_claims = [claim_id for claim_id in ["LL-CLAIM-009", "LL-CLAIM-014"] if claim_id not in claim_ids]
    if missing_claims:
        raise SystemExit(f"ERROR: pattern validation expected claim ids missing from registry: {missing_claims}")


def validate_ontology() -> None:
    if not ONTOLOGY_PATH.exists():
        raise SystemExit(f"ERROR: missing ontology file: {ONTOLOGY_PATH}")
    text = ONTOLOGY_PATH.read_text(encoding="utf-8")
    for invariant in REQUIRED_INVARIANTS:
        if f"ll:{invariant}" not in text:
            raise SystemExit(f"ERROR: ontology missing invariant instance: ll:{invariant}")
    for klass in ["ll:Source", "ll:Claim", "ll:Invariant", "ll:TrustSurface", "ll:Checker"]:
        if klass not in text:
            raise SystemExit(f"ERROR: ontology missing class/property anchor: {klass}")


def main() -> None:
    source_ids = validate_sources()
    claim_ids = validate_claims(source_ids)
    validate_pattern(claim_ids)
    validate_ontology()
    print("OK: lawful-learning Phase 7 research pack validates")


if __name__ == "__main__":
    main()
