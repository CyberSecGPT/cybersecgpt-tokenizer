"""Tests for bounded tokenizer contracts."""

from dataclasses import FrozenInstanceError

import pytest

from cybersecgpt.tokenizer import (
    MAX_IDENTIFIER_LENGTH,
    MAX_TEXT_BYTES,
    MAX_TOKEN_COUNT,
    MAX_VOCABULARY_SIZE,
    DecodeRequest,
    DecodeResult,
    EncodeRequest,
    EncodeResult,
    FinishStatus,
    SpecialToken,
    TokenizerContractError,
    TokenizerDescriptor,
)

FINGERPRINT = "a" * 64


def test_public_contracts_are_immutable_and_accept_valid_values() -> None:
    special = SpecialToken("document_boundary", 7)
    descriptor = TokenizerDescriptor(
        tokenizer_id="cybersecgpt-tokenizer-v1",
        contract_version="1",
        algorithm_id="decision-pending",
        artifact_format_version="1",
        normalization_profile="decision-pending",
        pretokenization_profile="decision-pending",
        vocabulary_size=256,
        fingerprint=FINGERPRINT,
        special_tokens=(special,),
    )
    encode_request = EncodeRequest("Hello", max_tokens=4, add_special_tokens=True)
    encode_result = EncodeResult((1, 2), FINGERPRINT, FinishStatus.COMPLETED)
    decode_request = DecodeRequest((1, 2))
    decode_result = DecodeResult("Hello", FINGERPRINT, FinishStatus.TRUNCATED)

    assert descriptor.special_tokens == (special,)
    assert encode_request.add_special_tokens is True
    assert encode_result.token_ids == decode_request.token_ids
    assert decode_result.text == "Hello"
    with pytest.raises(FrozenInstanceError):
        special.token_id = 8  # type: ignore[misc]


@pytest.mark.parametrize(
    "value", ["", "x" * (MAX_IDENTIFIER_LENGTH + 1), "bad id", "é"]
)
def test_identifier_validation_rejects_invalid_values(value: str) -> None:
    with pytest.raises(TokenizerContractError):
        SpecialToken(value, 0)


@pytest.mark.parametrize("token_id", [-1, MAX_VOCABULARY_SIZE])
def test_special_token_rejects_out_of_range_ids(token_id: int) -> None:
    with pytest.raises(TokenizerContractError):
        SpecialToken("role", token_id)


def _descriptor(**changes: object) -> TokenizerDescriptor:
    values: dict[str, object] = {
        "tokenizer_id": "id",
        "contract_version": "1",
        "algorithm_id": "pending",
        "artifact_format_version": "1",
        "normalization_profile": "pending",
        "pretokenization_profile": "pending",
        "vocabulary_size": 8,
        "fingerprint": FINGERPRINT,
        "special_tokens": (),
    }
    values.update(changes)
    return TokenizerDescriptor(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("size", [0, MAX_VOCABULARY_SIZE + 1])
def test_descriptor_rejects_invalid_vocabulary_size(size: int) -> None:
    with pytest.raises(TokenizerContractError):
        _descriptor(vocabulary_size=size)


@pytest.mark.parametrize("fingerprint", ["A" * 64, "a" * 63, "g" * 64])
def test_descriptor_rejects_invalid_fingerprint(fingerprint: str) -> None:
    with pytest.raises(TokenizerContractError):
        _descriptor(fingerprint=fingerprint)


def test_descriptor_rejects_duplicate_or_out_of_vocabulary_special_tokens() -> None:
    with pytest.raises(TokenizerContractError, match="IDs"):
        _descriptor(special_tokens=(SpecialToken("one", 1), SpecialToken("two", 1)))
    with pytest.raises(TokenizerContractError, match="roles"):
        _descriptor(special_tokens=(SpecialToken("one", 1), SpecialToken("one", 2)))
    with pytest.raises(TokenizerContractError, match="smaller"):
        _descriptor(special_tokens=(SpecialToken("one", 8),))


def test_encode_request_enforces_byte_and_token_limits() -> None:
    assert EncodeRequest("").max_tokens == MAX_TOKEN_COUNT
    with pytest.raises(TokenizerContractError, match="byte"):
        EncodeRequest("a" * (MAX_TEXT_BYTES + 1))
    for value in (-1, MAX_TOKEN_COUNT + 1):
        with pytest.raises(TokenizerContractError, match="max_tokens"):
            EncodeRequest("", max_tokens=value)


@pytest.mark.parametrize("request_type", [DecodeRequest])
def test_token_sequences_enforce_count_and_id_limits(request_type: object) -> None:
    constructor = request_type
    with pytest.raises(TokenizerContractError, match="count"):
        constructor((0,) * (MAX_TOKEN_COUNT + 1))  # type: ignore[operator]
    for token_id in (-1, MAX_VOCABULARY_SIZE):
        with pytest.raises(TokenizerContractError, match="unsupported"):
            constructor((token_id,))  # type: ignore[operator]


def test_encode_result_enforces_fingerprint_count_and_id_limits() -> None:
    with pytest.raises(TokenizerContractError, match="SHA-256"):
        EncodeResult((), "invalid", FinishStatus.COMPLETED)
    with pytest.raises(TokenizerContractError, match="count"):
        EncodeResult((0,) * (MAX_TOKEN_COUNT + 1), FINGERPRINT, FinishStatus.COMPLETED)
    for token_id in (-1, MAX_VOCABULARY_SIZE):
        with pytest.raises(TokenizerContractError, match="unsupported"):
            EncodeResult((token_id,), FINGERPRINT, FinishStatus.COMPLETED)


def test_decode_result_enforces_text_and_fingerprint_limits() -> None:
    with pytest.raises(TokenizerContractError, match="byte"):
        DecodeResult("a" * (MAX_TEXT_BYTES + 1), FINGERPRINT, FinishStatus.COMPLETED)
    with pytest.raises(TokenizerContractError, match="SHA-256"):
        DecodeResult("", "invalid", FinishStatus.COMPLETED)
