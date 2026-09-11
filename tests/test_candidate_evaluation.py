"""Candidate-neutral deterministic structural evaluation tests."""

from dataclasses import replace

import pytest

from cybersecgpt.tokenizer import (
    ByteBpeTrainingConfig,
    DecodeRequest,
    DecodeResult,
    EncodeRequest,
    EncodeResult,
    EvaluationDomain,
    EvaluationManifest,
    EvaluationSample,
    ExactRatio,
    FinishStatus,
    TokenizerContractError,
    Utf8ByteReferenceTokenizer,
    evaluate_candidate,
    train_byte_bpe_candidate,
)


def _manifest(*texts: str) -> EvaluationManifest:
    samples = tuple(
        EvaluationSample.from_text(
            sample_id=f"sample-{index}",
            domain=EvaluationDomain.LOGS,
            text=text,
            source_ref="generated:test",
            license_id="CC0-1.0",
        )
        for index, text in enumerate(texts)
    )
    return EvaluationManifest("candidate-evaluation", "1", samples)


def test_exact_ratio_is_reduced_and_rejects_invalid_values() -> None:
    assert ExactRatio.from_counts(6, 8) == ExactRatio(3, 4)
    assert ExactRatio.from_counts(0, 3) == ExactRatio(0, 1)
    assert ExactRatio.from_counts(0, 0) is None
    with pytest.raises(TokenizerContractError, match="reduced"):
        ExactRatio(2, 4)
    for numerator, denominator in ((-1, 1), (1, -1)):
        with pytest.raises(TokenizerContractError):
            ExactRatio.from_counts(numerator, denominator)
    with pytest.raises(TokenizerContractError, match="range"):
        ExactRatio(1, 0)


def test_reference_report_is_deterministic_exact_and_content_minimizing() -> None:
    manifest = _manifest("abc", "🔐", "")
    candidate = Utf8ByteReferenceTokenizer()

    report = evaluate_candidate(manifest, candidate)

    assert report == evaluate_candidate(manifest, candidate)
    assert report.manifest_id == manifest.manifest_id
    assert report.manifest_version == manifest.version
    assert report.algorithm_id == candidate.descriptor.algorithm_id
    assert report.tokenizer_fingerprint == candidate.descriptor.fingerprint
    assert [metric.domain for metric in report.samples] == [EvaluationDomain.LOGS] * 3
    assert [metric.tokens_per_utf8_byte for metric in report.samples] == [
        ExactRatio(1, 1),
        ExactRatio(1, 1),
        None,
    ]
    assert report.samples[1].tokens_per_unicode_scalar == ExactRatio(4, 1)
    assert all(
        metric.decode_succeeded and metric.reversible for metric in report.samples
    )
    assert all(not hasattr(metric, "text") for metric in report.samples)


def test_bpe_report_records_exact_compression_against_byte_reference() -> None:
    manifest = _manifest("abab")
    trained = train_byte_bpe_candidate(
        manifest, ByteBpeTrainingConfig(258, source_revision="test-sha")
    )

    report = evaluate_candidate(manifest, trained.candidate)
    metric = report.samples[0]

    assert metric.byte_reference_token_count == 4
    assert metric.candidate_token_count == 1
    assert metric.tokens_per_utf8_byte == ExactRatio(1, 4)
    assert metric.tokens_per_unicode_scalar == ExactRatio(1, 4)
    assert metric.compression_ratio_to_byte_reference == ExactRatio(1, 4)
    assert metric.decode_succeeded is True
    assert metric.reversible is True


def test_truncation_suppresses_ratios_and_records_decode_outcome() -> None:
    report = evaluate_candidate(
        _manifest("ab", "é"), Utf8ByteReferenceTokenizer(), max_tokens=1
    )

    ascii_metric, unicode_metric = report.samples
    assert ascii_metric.finish_status is FinishStatus.TRUNCATED
    assert ascii_metric.tokens_per_utf8_byte is None
    assert ascii_metric.tokens_per_unicode_scalar is None
    assert ascii_metric.compression_ratio_to_byte_reference is None
    assert ascii_metric.decode_succeeded is True
    assert ascii_metric.reversible is False
    assert unicode_metric.decode_succeeded is False
    assert unicode_metric.reversible is False


class _WrongEncodeFingerprint:
    descriptor = Utf8ByteReferenceTokenizer.descriptor

    @staticmethod
    def encode(request: EncodeRequest) -> EncodeResult:
        result = Utf8ByteReferenceTokenizer.encode(request)
        return replace(result, tokenizer_fingerprint="0" * 64)

    @staticmethod
    def decode(request: DecodeRequest) -> DecodeResult:
        return Utf8ByteReferenceTokenizer.decode(request)


class _WrongDecodeFingerprint(_WrongEncodeFingerprint):
    @staticmethod
    def encode(request: EncodeRequest) -> EncodeResult:
        return Utf8ByteReferenceTokenizer.encode(request)

    @staticmethod
    def decode(request: DecodeRequest) -> DecodeResult:
        result = Utf8ByteReferenceTokenizer.decode(request)
        return replace(result, tokenizer_fingerprint="0" * 64)


@pytest.mark.parametrize(
    "candidate", [_WrongEncodeFingerprint(), _WrongDecodeFingerprint()]
)
def test_report_rejects_candidate_identity_mismatch(candidate: object) -> None:
    with pytest.raises(TokenizerContractError, match="fingerprint mismatch"):
        evaluate_candidate(_manifest("abc"), candidate)  # type: ignore[arg-type]
