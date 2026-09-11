"""Tests for the deterministic experimental byte-BPE candidate."""

from dataclasses import FrozenInstanceError

import pytest

import cybersecgpt.tokenizer.byte_bpe as byte_bpe
from cybersecgpt.tokenizer import (
    MAX_VOCABULARY_SIZE,
    BpeMerge,
    BpeTrainingFinishStatus,
    ByteBpeCandidate,
    ByteBpeTrainingConfig,
    DecodeRequest,
    EncodeRequest,
    EvaluationDomain,
    EvaluationManifest,
    EvaluationSample,
    FinishStatus,
    TokenizerContractError,
    train_byte_bpe_candidate,
)


def _manifest(*texts: str) -> EvaluationManifest:
    samples = tuple(
        EvaluationSample.from_text(
            sample_id=f"sample-{index}",
            domain=EvaluationDomain.CODE,
            text=text,
            source_ref="generated:test",
            license_id="CC0-1.0",
        )
        for index, text in enumerate(texts)
    )
    return EvaluationManifest("fixture", "1", samples)


def _candidate(text: str = "abab") -> ByteBpeCandidate:
    return train_byte_bpe_candidate(
        _manifest(text), ByteBpeTrainingConfig(258, source_revision="test-sha")
    ).candidate


def test_training_is_deterministic_and_records_provenance_without_text() -> None:
    config = ByteBpeTrainingConfig(258, source_revision="test-sha")
    first = train_byte_bpe_candidate(_manifest("abab", "ab"), config)
    second = train_byte_bpe_candidate(_manifest("abab", "ab"), config)

    assert first == second
    assert (
        first.candidate.descriptor.fingerprint
        == second.candidate.descriptor.fingerprint
    )
    different = train_byte_bpe_candidate(_manifest("cdcd"), config)
    assert (
        first.candidate.descriptor.fingerprint
        != different.candidate.descriptor.fingerprint
    )
    assert first.finish_status is BpeTrainingFinishStatus.VOCABULARY_LIMIT
    assert first.manifest_id == "fixture"
    assert first.max_training_bytes == 1024 * 1024
    assert first.implementation_version == "experimental-byte-bpe-v1"
    assert first.sample_digests == tuple(
        sample.content_sha256 for sample in _manifest("abab", "ab").samples
    )
    assert not hasattr(first, "text")
    with pytest.raises(FrozenInstanceError):
        first.source_revision = "changed"  # type: ignore[misc]


def test_training_frequency_and_unsigned_byte_tie_breaking() -> None:
    frequent = train_byte_bpe_candidate(
        _manifest("ababa"), ByteBpeTrainingConfig(257)
    ).candidate
    tied = train_byte_bpe_candidate(
        _manifest("abac"), ByteBpeTrainingConfig(257)
    ).candidate

    assert frequent.tokens[256] == b"ab"
    assert tied.tokens[256] == b"ab"


def test_candidate_round_trips_unicode_and_compresses_learned_text() -> None:
    candidate = _candidate(" jingïaroh jingïaroh ")
    request = EncodeRequest(" jingïaroh ")
    encoded = candidate.encode(request)
    decoded = candidate.decode(DecodeRequest(encoded.token_ids))

    assert encoded.finish_status is FinishStatus.COMPLETED
    assert len(encoded.token_ids) < len(request.text.encode("utf-8"))
    assert decoded.text == request.text
    assert decoded.tokenizer_fingerprint == candidate.descriptor.fingerprint
    assert candidate.descriptor.algorithm_id == "experimental-byte-bpe-v1"
    assert candidate.descriptor.special_tokens == ()


def test_encode_is_reproducible_and_truncation_is_explicit() -> None:
    candidate = _candidate()
    first = candidate.encode(EncodeRequest("abab"))
    assert first == candidate.encode(EncodeRequest("abab"))
    truncated = candidate.encode(EncodeRequest("ababc", max_tokens=1))
    assert truncated.finish_status is FinishStatus.TRUNCATED
    assert len(truncated.token_ids) == 1


def test_candidate_rejects_special_tokens_invalid_ids_and_malformed_utf8() -> None:
    candidate = _candidate()
    with pytest.raises(TokenizerContractError, match="no special-token"):
        candidate.encode(EncodeRequest("ab", add_special_tokens=True))
    with pytest.raises(TokenizerContractError, match="invalid BPE"):
        candidate.decode(DecodeRequest((len(candidate.tokens),)))
    with pytest.raises(TokenizerContractError, match="valid UTF-8"):
        candidate.decode(DecodeRequest((0xC3,)))


def test_candidate_rejects_amplified_decode_before_join(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = _candidate()
    monkeypatch.setattr(byte_bpe, "MAX_TEXT_BYTES", 1)
    with pytest.raises(TokenizerContractError, match="output limit"):
        candidate.decode(DecodeRequest((256,)))


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"vocabulary_limit": 255}, "vocabulary_limit"),
        ({"vocabulary_limit": MAX_VOCABULARY_SIZE + 1}, "vocabulary_limit"),
        ({"vocabulary_limit": 256, "merge_budget": -1}, "merge_budget"),
        ({"vocabulary_limit": 256, "merge_budget": 257}, "merge_budget"),
        ({"vocabulary_limit": 256, "max_training_bytes": -1}, "max_training_bytes"),
        (
            {"vocabulary_limit": 256, "max_training_bytes": 1024 * 1024 + 1},
            "max_training_bytes",
        ),
        (
            {"vocabulary_limit": 256, "source_revision": "bad revision"},
            "source_revision",
        ),
        ({"vocabulary_limit": 256, "source_revision": ""}, "source_revision"),
        ({"vocabulary_limit": 256, "source_revision": "é"}, "source_revision"),
        ({"vocabulary_limit": 256, "source_revision": "x" * 129}, "source_revision"),
    ],
)
def test_training_config_rejects_invalid_values(
    changes: dict[str, object], message: str
) -> None:
    with pytest.raises(TokenizerContractError, match=message):
        ByteBpeTrainingConfig(**changes)  # type: ignore[arg-type]


def test_training_enforces_content_limit_and_reports_bounded_stops() -> None:
    with pytest.raises(TokenizerContractError, match="max_training_bytes"):
        train_byte_bpe_candidate(
            _manifest("ab"), ByteBpeTrainingConfig(257, max_training_bytes=1)
        )
    no_pair = train_byte_bpe_candidate(_manifest(""), ByteBpeTrainingConfig(257))
    assert no_pair.finish_status is BpeTrainingFinishStatus.NO_ELIGIBLE_PAIR
    budget = train_byte_bpe_candidate(
        _manifest("abab"), ByteBpeTrainingConfig(300, merge_budget=1)
    )
    assert budget.finish_status is BpeTrainingFinishStatus.MERGE_BUDGET


def test_candidate_validation_rejects_malformed_in_memory_data() -> None:
    alphabet = tuple(bytes((value,)) for value in range(256))
    with pytest.raises(TokenizerContractError, match="vocabulary size"):
        ByteBpeCandidate(alphabet[:-1], ())
    with pytest.raises(TokenizerContractError, match="fallback"):
        ByteBpeCandidate((b"x",) + alphabet[1:], ())
    with pytest.raises(TokenizerContractError, match="counts"):
        ByteBpeCandidate(alphabet + (b"ab",), ())
    with pytest.raises(TokenizerContractError, match="consecutive"):
        ByteBpeCandidate(alphabet + (b"ab",), (BpeMerge(97, 98, 257),))
    with pytest.raises(TokenizerContractError, match="invalid ID"):
        ByteBpeCandidate(alphabet + (b"ab",), (BpeMerge(-1, 98, 256),))
    with pytest.raises(TokenizerContractError, match="invalid ID"):
        ByteBpeCandidate(alphabet + (b"ab",), (BpeMerge(97, 256, 256),))
    with pytest.raises(TokenizerContractError, match="inconsistent"):
        ByteBpeCandidate(alphabet + (b"ac",), (BpeMerge(97, 98, 256),))
