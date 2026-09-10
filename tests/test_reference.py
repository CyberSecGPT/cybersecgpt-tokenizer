"""Tests for the fixed UTF-8 byte evaluation reference."""

import pytest

from cybersecgpt.tokenizer import (
    UTF8_BYTE_REFERENCE_FINGERPRINT,
    DecodeRequest,
    EncodeRequest,
    FinishStatus,
    TokenizerContractError,
    Utf8ByteReferenceTokenizer,
)


def test_reference_descriptor_and_fingerprint_are_fixed() -> None:
    descriptor = Utf8ByteReferenceTokenizer.descriptor
    assert descriptor.algorithm_id == "utf8-byte-reference-v1"
    assert descriptor.vocabulary_size == 256
    assert descriptor.special_tokens == ()
    assert descriptor.fingerprint == UTF8_BYTE_REFERENCE_FINGERPRINT
    assert UTF8_BYTE_REFERENCE_FINGERPRINT == (
        "a3d93532b1fcd00c09bff1e9b8444b567c9bd2b153aa083a4debc3f90d61334e"
    )


@pytest.mark.parametrize(
    "text", ["", "CyberSecGPT", "Khasi: jingïaroh", "e\u0301", "🔐"]
)
def test_reference_round_trip_is_deterministic(text: str) -> None:
    first = Utf8ByteReferenceTokenizer.encode(EncodeRequest(text))
    second = Utf8ByteReferenceTokenizer.encode(EncodeRequest(text))
    decoded = Utf8ByteReferenceTokenizer.decode(DecodeRequest(first.token_ids))

    assert first == second
    assert first.token_ids == tuple(text.encode("utf-8"))
    assert first.finish_status is FinishStatus.COMPLETED
    assert decoded.text == text
    assert decoded.finish_status is FinishStatus.COMPLETED
    assert decoded.tokenizer_fingerprint == first.tokenizer_fingerprint


def test_reference_truncation_is_explicit() -> None:
    result = Utf8ByteReferenceTokenizer.encode(EncodeRequest("é", max_tokens=1))
    assert result.token_ids == (0xC3,)
    assert result.finish_status is FinishStatus.TRUNCATED
    with pytest.raises(TokenizerContractError, match="valid UTF-8"):
        Utf8ByteReferenceTokenizer.decode(DecodeRequest(result.token_ids))


def test_reference_rejects_special_token_insertion_and_non_byte_ids() -> None:
    with pytest.raises(TokenizerContractError, match="no special-token"):
        Utf8ByteReferenceTokenizer.encode(
            EncodeRequest("text", add_special_tokens=True)
        )
    with pytest.raises(TokenizerContractError, match="non-byte"):
        Utf8ByteReferenceTokenizer.decode(DecodeRequest((256,)))


@pytest.mark.parametrize("token_ids", [(0x80,), (0xC0, 0x80), (0xE2, 0x82)])
def test_reference_rejects_malformed_or_incomplete_utf8(
    token_ids: tuple[int, ...],
) -> None:
    with pytest.raises(TokenizerContractError, match="valid UTF-8"):
        Utf8ByteReferenceTokenizer.decode(DecodeRequest(token_ids))
