"""Fixed UTF-8 byte reference candidate for tokenizer evaluation."""

from __future__ import annotations

from hashlib import sha256
from typing import Final

from cybersecgpt.tokenizer.contracts import (
    DecodeRequest,
    DecodeResult,
    EncodeRequest,
    EncodeResult,
    FinishStatus,
    TokenizerContractError,
    TokenizerDescriptor,
)

_CANONICAL_REFERENCE_CONFIGURATION: Final = (
    b'{"algorithm_id":"utf8-byte-reference-v1",'
    b'"artifact_format_version":"reference-1",'
    b'"contract_version":"1",'
    b'"input_encoding":"utf-8-strict",'
    b'"normalization_profile":"none",'
    b'"pretokenization_profile":"utf8-bytes",'
    b'"special_tokens":[],"vocabulary_size":256}'
)
UTF8_BYTE_REFERENCE_FINGERPRINT: Final = sha256(
    _CANONICAL_REFERENCE_CONFIGURATION
).hexdigest()


class Utf8ByteReferenceTokenizer:
    """Deterministic 256-byte evaluation baseline, not Tokenizer v1 selection."""

    descriptor: Final = TokenizerDescriptor(
        tokenizer_id="utf8-byte-reference",
        contract_version="1",
        algorithm_id="utf8-byte-reference-v1",
        artifact_format_version="reference-1",
        normalization_profile="none",
        pretokenization_profile="utf8-bytes",
        vocabulary_size=256,
        fingerprint=UTF8_BYTE_REFERENCE_FINGERPRINT,
    )

    @classmethod
    def encode(cls, request: EncodeRequest) -> EncodeResult:
        """Encode canonical UTF-8 bytes, with explicit caller-bounded truncation."""

        if request.add_special_tokens:
            raise TokenizerContractError(
                "the reference candidate has no special-token allocation"
            )
        encoded = request.text.encode("utf-8")
        selected = encoded[: request.max_tokens]
        status = (
            FinishStatus.TRUNCATED
            if len(selected) < len(encoded)
            else FinishStatus.COMPLETED
        )
        return EncodeResult(tuple(selected), cls.descriptor.fingerprint, status)

    @classmethod
    def decode(cls, request: DecodeRequest) -> DecodeResult:
        """Decode byte IDs with strict UTF-8 validation and no replacement."""

        if any(
            token_id >= cls.descriptor.vocabulary_size for token_id in request.token_ids
        ):
            raise TokenizerContractError("token_ids contains a non-byte reference ID")
        try:
            text = bytes(request.token_ids).decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise TokenizerContractError(
                "token_ids is not a complete valid UTF-8 byte sequence"
            ) from error
        return DecodeResult(text, cls.descriptor.fingerprint, FinishStatus.COMPLETED)
