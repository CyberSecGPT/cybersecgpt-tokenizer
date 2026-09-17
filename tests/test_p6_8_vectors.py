"""Reviewable known-output and negative conformance evidence for P6.8."""

import json
from pathlib import Path

import pytest
from scripts.verify_p6_8_vectors import (
    VECTOR_PATH,
    ConformanceError,
    verify_negative_boundaries,
    verify_vectors,
)


def test_pinned_vectors_replay_and_negative_boundaries() -> None:
    count, digest = verify_vectors()
    assert count == 20
    assert digest == "481d0c11c6a51a9b7cd63133c34b51194fa69e87744e91ca87c619d64d2ade74"
    verify_negative_boundaries()


@pytest.mark.parametrize(
    ("path", "value", "reason"),
    [
        (("bpe_fingerprint",), "0" * 64, "BPE identity mismatch"),
        (("artifact_sha256",), "0" * 64, "artifact SHA mismatch"),
        (("artifact_digest",), "0" * 64, "artifact digest mismatch"),
        (("construction_sample_digests", 0), "0" * 64, "construction sample mismatch"),
        (("vectors", 0, "input_sha256"), "0" * 64, "input digest mismatch"),
        (("vectors", 1, "bpe_ids"), [1], "BPE oracle mismatch"),
        (("vectors", 1, "reference_ids"), [1], "reference oracle mismatch"),
        (("vectors", 1, "license_id"), "unknown", "invalid fixture provenance"),
        (("vectors", 1, "finish_status"), "truncated", "completion status mismatch"),
        (("vectors", 1, "text"), "different", "input digest mismatch"),
        (("schema_version",), "unknown", "schema version mismatch"),
        (("source_revision",), "unknown", "source revision mismatch"),
    ],
)
def test_modified_vector_fails_closed(
    tmp_path: Path, path: tuple[str | int, ...], value: object, reason: str
) -> None:
    fixture = json.loads(VECTOR_PATH.read_text(encoding="utf-8"))
    parent = fixture
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = value
    modified = tmp_path / "modified.json"
    modified.write_text(
        json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with pytest.raises(ConformanceError, match=reason):
        verify_vectors(modified)


def test_unbounded_or_unknown_fixture_is_rejected(tmp_path: Path) -> None:
    oversize = tmp_path / "oversize.json"
    oversize.write_bytes(b" " * 65_537)
    with pytest.raises(ConformanceError, match="fixture exceeds byte limit"):
        verify_vectors(oversize)
    fixture = json.loads(VECTOR_PATH.read_text(encoding="utf-8"))
    fixture["unknown_field"] = "untrusted"
    changed = tmp_path / "unknown.json"
    changed.write_text(
        json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with pytest.raises(ConformanceError, match="invalid vector schema"):
        verify_vectors(changed)


def test_duplicate_or_noncanonical_json_is_rejected(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    original = VECTOR_PATH.read_text(encoding="utf-8")
    duplicate.write_text(
        original.replace(
            '"schema_version":', '"schema_version": "wrong", "schema_version":', 1
        ),
        encoding="utf-8",
    )
    with pytest.raises(ConformanceError, match="invalid fixture JSON"):
        verify_vectors(duplicate)
    noncanonical = tmp_path / "noncanonical.json"
    noncanonical.write_text(json.dumps(json.loads(original)), encoding="utf-8")
    with pytest.raises(ConformanceError, match="non-canonical fixture JSON"):
        verify_vectors(noncanonical)
