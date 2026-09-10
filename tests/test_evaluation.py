"""Tests for deterministic evaluation manifests."""

from dataclasses import FrozenInstanceError

import pytest

from cybersecgpt.tokenizer import (
    MAX_TEXT_BYTES,
    FinishStatus,
    TokenizerContractError,
)
from cybersecgpt.tokenizer.evaluation import (
    MAX_EVALUATION_SAMPLES,
    EvaluationDomain,
    EvaluationManifest,
    EvaluationSample,
    evaluate_utf8_byte_reference,
)


def _sample(sample_id: str = "sample-1", text: str = "hello") -> EvaluationSample:
    return EvaluationSample.from_text(
        sample_id=sample_id,
        domain=EvaluationDomain.NATURAL_LANGUAGE,
        text=text,
        source_ref="generated:test",
        license_id="CC0-1.0",
    )


def test_sample_factory_is_deterministic_and_immutable() -> None:
    sample = _sample()
    assert sample.content_sha256 == _sample().content_sha256
    with pytest.raises(FrozenInstanceError):
        sample.text = "changed"  # type: ignore[misc]


@pytest.mark.parametrize("field", ["sample_id", "source_ref", "license_id"])
@pytest.mark.parametrize("value", ["", "bad value", "x" * 257])
def test_sample_rejects_invalid_metadata(field: str, value: str) -> None:
    values = {
        "sample_id": "sample",
        "domain": EvaluationDomain.CODE,
        "text": "",
        "source_ref": "generated:test",
        "license_id": "CC0-1.0",
        "content_sha256": (
            "e3b0c44298fc1c149afbf4c8996fb924" "27ae41e4649b934ca495991b7852b855"
        ),
    }
    values[field] = value
    with pytest.raises(TokenizerContractError):
        EvaluationSample(**values)  # type: ignore[arg-type]


def test_sample_rejects_oversize_content_and_digest_mismatch() -> None:
    with pytest.raises(TokenizerContractError, match="byte"):
        _sample(text="a" * (MAX_TEXT_BYTES + 1))
    with pytest.raises(TokenizerContractError, match="digest"):
        EvaluationSample(
            "sample",
            EvaluationDomain.CODE,
            "",
            "generated:test",
            "CC0-1.0",
            "0" * 64,
        )


def test_manifest_accepts_unique_bounded_samples() -> None:
    manifest = EvaluationManifest("manifest-v1", "1", (_sample(),))
    assert manifest.samples[0].sample_id == "sample-1"


@pytest.mark.parametrize("field", ["manifest_id", "version"])
@pytest.mark.parametrize("value", ["", "bad value", "x" * 129])
def test_manifest_rejects_invalid_identity(field: str, value: str) -> None:
    values = {"manifest_id": "manifest", "version": "1", "samples": (_sample(),)}
    values[field] = value
    with pytest.raises(TokenizerContractError):
        EvaluationManifest(**values)  # type: ignore[arg-type]


def test_manifest_rejects_empty_excess_duplicate_and_oversize_samples() -> None:
    with pytest.raises(TokenizerContractError, match="entries"):
        EvaluationManifest("manifest", "1", ())
    sample = _sample()
    with pytest.raises(TokenizerContractError, match="unique"):
        EvaluationManifest("manifest", "1", (sample, sample))
    many = tuple(_sample(str(index), "") for index in range(MAX_EVALUATION_SAMPLES + 1))
    with pytest.raises(TokenizerContractError, match="entries"):
        EvaluationManifest("manifest", "1", many)
    first = _sample("first", "a" * (MAX_TEXT_BYTES // 2 + 1))
    second = _sample("second", "b" * (MAX_TEXT_BYTES // 2 + 1))
    with pytest.raises(TokenizerContractError, match="manifest"):
        EvaluationManifest("manifest", "1", (first, second))


def test_reference_measurements_are_deterministic_and_content_minimizing() -> None:
    manifest = EvaluationManifest(
        "manifest-v1",
        "1",
        (_sample("ascii", "abc"), _sample("unicode", "🔐")),
    )
    first = evaluate_utf8_byte_reference(manifest)

    assert first == evaluate_utf8_byte_reference(manifest)
    assert [metric.token_count for metric in first] == [3, 4]
    assert [metric.utf8_byte_count for metric in first] == [3, 4]
    assert [metric.unicode_scalar_count for metric in first] == [3, 1]
    assert all(metric.finish_status is FinishStatus.COMPLETED for metric in first)
    assert all(metric.decode_succeeded and metric.reversible for metric in first)
    assert all(not hasattr(metric, "text") for metric in first)


def test_reference_measurements_record_valid_and_invalid_truncation() -> None:
    manifest = EvaluationManifest(
        "manifest-v1",
        "1",
        (_sample("ascii", "ab"), _sample("unicode", "é")),
    )
    metrics = evaluate_utf8_byte_reference(manifest, max_tokens=1)

    assert metrics[0].finish_status is FinishStatus.TRUNCATED
    assert metrics[0].decode_succeeded is True
    assert metrics[0].reversible is False
    assert metrics[1].finish_status is FinishStatus.TRUNCATED
    assert metrics[1].decode_succeeded is False
    assert metrics[1].reversible is False
