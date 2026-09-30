"""Tests for canonical P6.10 corpus admission manifests."""

from dataclasses import FrozenInstanceError, replace
from hashlib import sha256

import pytest

from cybersecgpt.tokenizer import TokenizerContractError
from cybersecgpt.tokenizer.corpus_manifest import (
    CORPUS_MANIFEST_SCHEMA_VERSION,
    MAX_CORPUS_EXCLUSION_REASONS,
    MAX_CORPUS_SAMPLES,
    CorpusAdmissionManifest,
    CorpusSampleContent,
    CorpusSampleRecord,
    CorpusSourceRecord,
    CorpusTransformation,
    RightsDecision,
    SafetyDecision,
    admit_corpus,
)
from cybersecgpt.tokenizer.evaluation import EvaluationDomain

ZERO = "0" * 64


def _source(**changes: object) -> CorpusSourceRecord:
    values: dict[str, object] = {
        "source_id": "source-1",
        "origin_ref": "urn:generated:p6-10-fixture",
        "acquisition_method": "generated-fixture",
        "acquired_at": "2026-09-30",
        "source_revision": "fixture-v1",
        "source_sha256": ZERO,
        "license_expression": "CC0-1.0",
        "obligations_sha256": ZERO,
        "reviewer_id": "owner-review",
        "reviewed_at": "2026-09-30",
        "rights_decision": RightsDecision.APPROVED,
        "sensitive_data_decision": SafetyDecision.CLEAN,
        "contamination_decision": SafetyDecision.CLEAN,
        "acquisition_allowed": True,
        "processing_allowed": True,
        "training_allowed": True,
        "derived_statistics_allowed": True,
        "artifact_distribution_allowed": True,
    }
    values.update(changes)
    return CorpusSourceRecord(**values)  # type: ignore[arg-type]


def _sample(
    sample_id: str = "sample-1",
    content: bytes = b"alpha",
    *,
    source_id: str = "source-1",
    domain: EvaluationDomain = EvaluationDomain.NATURAL_LANGUAGE,
) -> CorpusSampleRecord:
    return CorpusSampleRecord(
        sample_id,
        source_id,
        domain,
        len(content),
        sha256(content).hexdigest(),
    )


def _manifest(
    *,
    sources: tuple[CorpusSourceRecord, ...] | None = None,
    samples: tuple[CorpusSampleRecord, ...] | None = None,
    transformations: tuple[CorpusTransformation, ...] | None = None,
    exclusions: tuple[tuple[str, int], ...] = (("duplicate", 1),),
    digest: bool = True,
) -> CorpusAdmissionManifest:
    manifest = CorpusAdmissionManifest(
        corpus_id="p6-10-fixture",
        schema_version=CORPUS_MANIFEST_SCHEMA_VERSION,
        approved_purpose="Tokenizer v1 manifest verifier test only",
        artifact_distribution_terms="CC0 fixture; no production approval",
        sources=sources if sources is not None else (_source(),),
        transformations=(
            transformations
            if transformations is not None
            else (CorpusTransformation("decode", "fixture-tool-v1", ZERO),)
        ),
        samples=samples if samples is not None else (_sample(),),
        exclusion_counts=exclusions,
        manifest_sha256="",
    )
    return manifest.with_computed_digest() if digest else manifest


def test_manifest_digest_and_admission_are_deterministic_and_minimal() -> None:
    manifest = _manifest(
        samples=(
            _sample(),
            _sample("sample-2", b"{}", domain=EvaluationDomain.STRUCTURED_DATA),
        )
    )
    supplied = (
        CorpusSampleContent("sample-1", b"alpha"),
        CorpusSampleContent("sample-2", b"{}"),
    )
    result = admit_corpus(manifest, supplied, deadline_ns=2, now_ns=1)

    assert manifest == _manifest(samples=manifest.samples)
    assert manifest.with_computed_digest() is manifest
    assert result.corpus_id == "p6-10-fixture"
    assert result.manifest_sha256 == manifest.manifest_sha256
    assert result.sample_count == 2
    assert result.total_bytes == 7
    assert result.source_ids == ("source-1",)
    assert result.sample_digests == tuple(s.content_sha256 for s in manifest.samples)
    assert result.domains == (
        EvaluationDomain.NATURAL_LANGUAGE,
        EvaluationDomain.STRUCTURED_DATA,
    )
    assert not hasattr(result, "content")
    with pytest.raises(FrozenInstanceError):
        result.sample_count = 3  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_id", ""),
        ("source_id", "bad id"),
        ("source_id", "é"),
        ("origin_ref", ""),
        ("origin_ref", "a\x00b"),
        ("acquired_at", "20260930"),
        ("acquired_at", "1999-01-01"),
        ("acquired_at", "2026-13-01"),
        ("acquired_at", "2026-01-32"),
        ("source_sha256", "bad"),
        ("source_sha256", "G" * 64),
        ("obligations_sha256", "bad"),
    ],
)
def test_source_rejects_invalid_metadata(field: str, value: object) -> None:
    with pytest.raises(TokenizerContractError, match="invalid corpus"):
        _source(**{field: value})


@pytest.mark.parametrize(
    "record",
    [
        lambda: CorpusTransformation("", "tool", ZERO),
        lambda: CorpusTransformation("stage", "bad tool", ZERO),
        lambda: CorpusTransformation("stage", "tool", "bad"),
        lambda: CorpusSampleRecord("", "source", EvaluationDomain.CODE, 0, ZERO),
        lambda: CorpusSampleRecord("sample", "", EvaluationDomain.CODE, 0, ZERO),
        lambda: CorpusSampleRecord("sample", "source", EvaluationDomain.CODE, -1, ZERO),
        lambda: CorpusSampleRecord("sample", "source", EvaluationDomain.CODE, 0, "bad"),
        lambda: CorpusSampleContent("", b""),
        lambda: CorpusSampleContent("sample", bytearray()),
    ],
)
def test_records_reject_invalid_values(record: object) -> None:
    with pytest.raises(TokenizerContractError, match="invalid corpus"):
        record()  # type: ignore[operator]


def test_manifest_rejects_identity_schema_text_and_digest_changes() -> None:
    valid = _manifest()
    changes: tuple[dict[str, object], ...] = (
        {"corpus_id": ""},
        {"schema_version": "future"},
        {"approved_purpose": ""},
        {"artifact_distribution_terms": ""},
        {"manifest_sha256": "bad"},
        {"approved_purpose": "changed"},
    )
    for change in changes:
        with pytest.raises(TokenizerContractError, match="invalid corpus"):
            replace(valid, **change)


def test_manifest_rejects_missing_excess_duplicate_and_unbound_records() -> None:
    source = _source()
    sample = _sample()
    stage = CorpusTransformation("decode", "fixture-tool-v1", ZERO)
    cases = (
        {"sources": ()},
        {"samples": ()},
        {"transformations": ()},
        {"sources": (source, source)},
        {"samples": (sample, sample)},
        {
            "samples": (
                sample,
                _sample("sample-2", b"alpha"),
            )
        },
        {"transformations": (stage, stage)},
        {"samples": (_sample(source_id="missing"),)},
        {"exclusions": (("duplicate", 1), ("duplicate", 2))},
        {"exclusions": (("bad reason", 1),)},
        {"exclusions": (("bad-count", -1),)},
        {
            "exclusions": tuple(
                (f"reason-{index}", 0)
                for index in range(MAX_CORPUS_EXCLUSION_REASONS + 1)
            )
        },
    )
    for case in cases:
        with pytest.raises(TokenizerContractError, match="invalid corpus"):
            _manifest(**case)  # type: ignore[arg-type]

    with pytest.raises(TokenizerContractError, match="invalid corpus"):
        _manifest(
            samples=tuple(
                _sample(str(i), bytes((i % 251,)))
                for i in range(MAX_CORPUS_SAMPLES + 1)
            )
        )


def test_manifest_rejects_total_byte_limit_without_allocating_large_content() -> None:
    first = replace(_sample(), byte_count=9_000_000, content_sha256="1" * 64)
    second = replace(
        _sample("sample-2", b"b"), byte_count=9_000_000, content_sha256="2" * 64
    )
    with pytest.raises(TokenizerContractError, match="invalid corpus"):
        _manifest(samples=(first, second))


@pytest.mark.parametrize(
    "source_change",
    [
        {"rights_decision": RightsDecision.REJECTED},
        {"rights_decision": RightsDecision.UNKNOWN},
        {"rights_decision": RightsDecision.REVOKED},
        {"sensitive_data_decision": SafetyDecision.REJECTED},
        {"sensitive_data_decision": SafetyDecision.UNKNOWN},
        {"contamination_decision": SafetyDecision.REJECTED},
        {"acquisition_allowed": False},
        {"processing_allowed": False},
        {"training_allowed": False},
        {"derived_statistics_allowed": False},
        {"artifact_distribution_allowed": False},
    ],
)
def test_admission_fails_closed_on_rights_or_safety(
    source_change: dict[str, object],
) -> None:
    manifest = _manifest(sources=(_source(**source_change),))
    with pytest.raises(TokenizerContractError, match="invalid corpus"):
        admit_corpus(manifest, (CorpusSampleContent("sample-1", b"alpha"),))


def test_admission_rejects_unsealed_cancelled_expired_or_invalid_clock() -> None:
    unsealed = _manifest(digest=False)
    sealed = unsealed.with_computed_digest()
    content = (CorpusSampleContent("sample-1", b"alpha"),)
    calls = (
        (
            unsealed,
            {},
        ),
        (sealed, {"cancelled": True}),
        (sealed, {"deadline_ns": 1}),
        (sealed, {"now_ns": 1}),
        (sealed, {"deadline_ns": 1, "now_ns": 1}),
    )
    for manifest, options in calls:
        with pytest.raises(TokenizerContractError, match="invalid corpus"):
            admit_corpus(manifest, content, **options)  # type: ignore[arg-type]


def test_admission_rejects_missing_extra_reordered_changed_and_mismatched_content() -> (
    None
):
    manifest = _manifest(
        samples=(_sample(), _sample("sample-2", b"beta", domain=EvaluationDomain.CODE))
    )
    alpha = CorpusSampleContent("sample-1", b"alpha")
    beta = CorpusSampleContent("sample-2", b"beta")
    bad_cases = (
        (),
        (alpha,),
        (alpha, beta, beta),
        (beta, alpha),
        (CorpusSampleContent("sample-1", b"alphx"), beta),
        (CorpusSampleContent("sample-1", b"alpha!"), beta),
    )
    for supplied in bad_cases:
        with pytest.raises(TokenizerContractError, match="invalid corpus"):
            admit_corpus(manifest, supplied)
