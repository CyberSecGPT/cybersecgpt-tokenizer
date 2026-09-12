"""Tests for the deterministic experimental byte-frequency Unigram candidate."""

from dataclasses import FrozenInstanceError

import pytest

import cybersecgpt.tokenizer.unigram as unigram
from cybersecgpt.tokenizer import (
    ByteUnigramCandidate,
    ByteUnigramTrainingConfig,
    DecodeRequest,
    EncodeRequest,
    EvaluationDomain,
    EvaluationManifest,
    EvaluationSample,
    FinishStatus,
    TokenizerContractError,
    UnigramTrainingFinishStatus,
    evaluate_candidate,
    train_byte_unigram_candidate,
)


def _manifest(*texts: str) -> EvaluationManifest:
    samples = tuple(
        EvaluationSample.from_text(
            sample_id=f"sample-{index}",
            domain=EvaluationDomain.SECURITY_PROSE,
            text=text,
            source_ref="generated:test",
            license_id="CC0-1.0",
        )
        for index, text in enumerate(texts)
    )
    return EvaluationManifest("unigram-fixture", "1", samples)


def _candidate(text: str = "abab") -> ByteUnigramCandidate:
    return train_byte_unigram_candidate(
        _manifest(text),
        ByteUnigramTrainingConfig(258, source_revision="test-sha"),
    ).candidate


def test_training_is_deterministic_provenance_bound_and_content_minimizing() -> None:
    manifest = _manifest("abab", "ab")
    config = ByteUnigramTrainingConfig(257, source_revision="test-sha")

    first = train_byte_unigram_candidate(manifest, config)
    second = train_byte_unigram_candidate(manifest, config)

    assert first == second
    assert (
        first.candidate.descriptor.fingerprint
        == second.candidate.descriptor.fingerprint
    )
    assert first.manifest_id == "unigram-fixture"
    assert first.manifest_version == "1"
    assert first.sample_digests == tuple(
        sample.content_sha256 for sample in manifest.samples
    )
    assert first.requested_vocabulary_limit == 257
    assert first.max_training_bytes == 1024 * 1024
    assert first.source_revision == "test-sha"
    assert first.implementation_version == "experimental-byte-frequency-unigram-v1"
    assert first.finish_status is UnigramTrainingFinishStatus.VOCABULARY_LIMIT
    assert not hasattr(first, "text")
    with pytest.raises(FrozenInstanceError):
        first.source_revision = "changed"  # type: ignore[misc]


def test_discovery_uses_frequency_then_unsigned_byte_order() -> None:
    frequent = train_byte_unigram_candidate(
        _manifest("ababa"), ByteUnigramTrainingConfig(257)
    ).candidate
    tied = train_byte_unigram_candidate(
        _manifest("ababacac"), ByteUnigramTrainingConfig(257)
    ).candidate

    assert frequent.tokens[256] == b"ab"
    assert tied.tokens[256] == b"ab"


def test_costs_use_pseudocount_and_exact_integer_ceiling() -> None:
    candidate = train_byte_unigram_candidate(
        _manifest("aaa"), ByteUnigramTrainingConfig(257)
    ).candidate

    assert candidate.tokens[256] == b"aa"
    effective = (4, *(1 for _ in range(255)), 3)
    total = sum(effective)
    assert candidate.costs[ord("a")] == (total * unigram.UNIGRAM_COST_SCALE + 3) // 4
    assert candidate.costs[0] == total * unigram.UNIGRAM_COST_SCALE
    assert candidate.costs[256] == (total * unigram.UNIGRAM_COST_SCALE + 2) // 3


def test_candidate_round_trips_unicode_and_reports_structural_compression() -> None:
    candidate = _candidate(" jingïaroh jingïaroh ")
    request = EncodeRequest(" jingïaroh ")

    encoded = candidate.encode(request)
    decoded = candidate.decode(DecodeRequest(encoded.token_ids))
    report = evaluate_candidate(_manifest(request.text), candidate)

    assert encoded.finish_status is FinishStatus.COMPLETED
    assert len(encoded.token_ids) < len(request.text.encode("utf-8"))
    assert decoded.text == request.text
    assert decoded.tokenizer_fingerprint == candidate.descriptor.fingerprint
    assert candidate.descriptor.algorithm_id == "experimental-byte-frequency-unigram-v1"
    assert candidate.descriptor.special_tokens == ()
    assert report.samples[0].reversible is True


def test_segmentation_prefers_cost_then_count_then_token_id() -> None:
    alphabet = tuple(bytes((value,)) for value in range(256))
    base_costs = (10,) * 256

    lower_cost = ByteUnigramCandidate(alphabet + (b"ab",), base_costs + (15,))
    assert lower_cost.encode(EncodeRequest("ab")).token_ids == (256,)

    fewer = ByteUnigramCandidate(alphabet + (b"ab",), base_costs + (20,))
    assert fewer.encode(EncodeRequest("ab")).token_ids == (256,)

    token_order = ByteUnigramCandidate(alphabet + (b"ab", b"bc"), base_costs + (10, 10))
    assert token_order.encode(EncodeRequest("abc")).token_ids == (97, 257)


def test_encode_is_reproducible_and_truncation_is_explicit() -> None:
    candidate = _candidate()
    first = candidate.encode(EncodeRequest("abab"))
    assert first == candidate.encode(EncodeRequest("abab"))
    truncated = candidate.encode(EncodeRequest("ababc", max_tokens=1))
    assert truncated.finish_status is FinishStatus.TRUNCATED
    assert len(truncated.token_ids) == 1
    empty = candidate.encode(EncodeRequest("", max_tokens=0))
    assert empty.finish_status is FinishStatus.COMPLETED
    assert empty.token_ids == ()


def test_candidate_rejects_special_tokens_invalid_ids_and_malformed_utf8() -> None:
    candidate = _candidate()
    with pytest.raises(TokenizerContractError, match="no special-token"):
        candidate.encode(EncodeRequest("ab", add_special_tokens=True))
    with pytest.raises(TokenizerContractError, match="invalid Unigram"):
        candidate.decode(DecodeRequest((len(candidate.tokens),)))
    with pytest.raises(TokenizerContractError, match="valid UTF-8"):
        candidate.decode(DecodeRequest((0xC3,)))


def test_candidate_rejects_amplified_decode_before_join(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = _candidate()
    monkeypatch.setattr(unigram, "MAX_TEXT_BYTES", 1)
    with pytest.raises(TokenizerContractError, match="output limit"):
        candidate.decode(DecodeRequest((256,)))


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"vocabulary_limit": 255}, "vocabulary_limit"),
        ({"vocabulary_limit": 8193}, "vocabulary_limit"),
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
        ByteUnigramTrainingConfig(**changes)  # type: ignore[arg-type]


def test_training_enforces_content_and_distinct_substring_limits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(TokenizerContractError, match="max_training_bytes"):
        train_byte_unigram_candidate(
            _manifest("ab"), ByteUnigramTrainingConfig(257, max_training_bytes=1)
        )
    monkeypatch.setattr(unigram, "MAX_UNIGRAM_DISTINCT_SUBSTRINGS", 1)
    with pytest.raises(TokenizerContractError, match="resource_limit"):
        train_byte_unigram_candidate(_manifest("abcd"), ByteUnigramTrainingConfig(257))


def test_training_reports_candidate_exhaustion() -> None:
    result = train_byte_unigram_candidate(_manifest(""), ByteUnigramTrainingConfig(257))
    assert result.finish_status is UnigramTrainingFinishStatus.CANDIDATE_EXHAUSTED
    assert len(result.candidate.tokens) == 256


def test_candidate_validation_rejects_malformed_in_memory_data() -> None:
    alphabet = tuple(bytes((value,)) for value in range(256))
    costs = (1,) * 256
    with pytest.raises(TokenizerContractError, match="vocabulary size"):
        ByteUnigramCandidate(alphabet[:-1], costs[:-1])
    with pytest.raises(TokenizerContractError, match="fallback"):
        ByteUnigramCandidate((b"x",) + alphabet[1:], costs)
    with pytest.raises(TokenizerContractError, match="counts differ"):
        ByteUnigramCandidate(alphabet, costs[:-1])
    with pytest.raises(TokenizerContractError, match="unique"):
        ByteUnigramCandidate(alphabet + (b"a",), costs + (1,))
    with pytest.raises(TokenizerContractError, match="length"):
        ByteUnigramCandidate(alphabet + (b"",), costs + (1,))
    with pytest.raises(TokenizerContractError, match="length"):
        ByteUnigramCandidate(alphabet + (b"x" * 17,), costs + (1,))
    with pytest.raises(TokenizerContractError, match="cost"):
        ByteUnigramCandidate(alphabet, (0,) + costs[1:])
    with pytest.raises(TokenizerContractError, match="cost"):
        ByteUnigramCandidate(alphabet, (unigram._MAX_COST + 1,) + costs[1:])
