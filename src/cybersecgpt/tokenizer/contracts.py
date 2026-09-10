"""Immutable, bounded public contracts for CyberSecGPT tokenizers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

MAX_TEXT_BYTES: Final = 16 * 1024 * 1024
MAX_TOKEN_COUNT: Final = 4 * 1024 * 1024
MAX_VOCABULARY_SIZE: Final = 1_048_576
MAX_IDENTIFIER_LENGTH: Final = 128
SHA256_HEX_LENGTH: Final = 64


class TokenizerContractError(ValueError):
    """Raised when a tokenizer contract fails validation."""


class FinishStatus(StrEnum):
    """Stable encode/decode completion states."""

    COMPLETED = "completed"
    TRUNCATED = "truncated"


def _require_identifier(value: str, field_name: str) -> None:
    if not value or len(value) > MAX_IDENTIFIER_LENGTH:
        raise TokenizerContractError(
            f"{field_name} must contain 1..{MAX_IDENTIFIER_LENGTH} characters"
        )
    if not value.isascii() or any(character.isspace() for character in value):
        raise TokenizerContractError(
            f"{field_name} must be ASCII and contain no whitespace"
        )


def _require_sha256(value: str, field_name: str) -> None:
    if len(value) != SHA256_HEX_LENGTH or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise TokenizerContractError(
            f"{field_name} must be a lowercase SHA-256 hexadecimal digest"
        )


@dataclass(frozen=True, slots=True)
class SpecialToken:
    """A named, non-authorizing special-token allocation."""

    role: str
    token_id: int

    def __post_init__(self) -> None:
        _require_identifier(self.role, "role")
        if self.token_id < 0 or self.token_id >= MAX_VOCABULARY_SIZE:
            raise TokenizerContractError("token_id is outside the supported range")


@dataclass(frozen=True, slots=True)
class TokenizerDescriptor:
    """Behavior-defining identity for one immutable tokenizer artifact."""

    tokenizer_id: str
    contract_version: str
    algorithm_id: str
    artifact_format_version: str
    normalization_profile: str
    pretokenization_profile: str
    vocabulary_size: int
    fingerprint: str
    special_tokens: tuple[SpecialToken, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "tokenizer_id",
            "contract_version",
            "algorithm_id",
            "artifact_format_version",
            "normalization_profile",
            "pretokenization_profile",
        ):
            _require_identifier(getattr(self, field_name), field_name)
        if not 1 <= self.vocabulary_size <= MAX_VOCABULARY_SIZE:
            raise TokenizerContractError(
                "vocabulary_size is outside the supported range"
            )
        _require_sha256(self.fingerprint, "fingerprint")
        token_ids = tuple(token.token_id for token in self.special_tokens)
        roles = tuple(token.role for token in self.special_tokens)
        if len(token_ids) != len(set(token_ids)):
            raise TokenizerContractError("special token IDs must be unique")
        if len(roles) != len(set(roles)):
            raise TokenizerContractError("special token roles must be unique")
        if any(token_id >= self.vocabulary_size for token_id in token_ids):
            raise TokenizerContractError(
                "special token ID must be smaller than vocabulary_size"
            )


@dataclass(frozen=True, slots=True)
class EncodeRequest:
    """Bounded text encoding request; content never conveys authorization."""

    text: str
    max_tokens: int = MAX_TOKEN_COUNT
    add_special_tokens: bool = False

    def __post_init__(self) -> None:
        if len(self.text.encode("utf-8")) > MAX_TEXT_BYTES:
            raise TokenizerContractError("text exceeds the encoded byte limit")
        if not 0 <= self.max_tokens <= MAX_TOKEN_COUNT:
            raise TokenizerContractError("max_tokens is outside the supported range")


@dataclass(frozen=True, slots=True)
class EncodeResult:
    """Deterministic token IDs and explicit completion metadata."""

    token_ids: tuple[int, ...]
    tokenizer_fingerprint: str
    finish_status: FinishStatus

    def __post_init__(self) -> None:
        _require_sha256(self.tokenizer_fingerprint, "tokenizer_fingerprint")
        if len(self.token_ids) > MAX_TOKEN_COUNT:
            raise TokenizerContractError("token_ids exceeds the token-count limit")
        if any(
            token_id < 0 or token_id >= MAX_VOCABULARY_SIZE
            for token_id in self.token_ids
        ):
            raise TokenizerContractError("token_ids contains an unsupported ID")


@dataclass(frozen=True, slots=True)
class DecodeRequest:
    """Bounded token decoding request."""

    token_ids: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.token_ids) > MAX_TOKEN_COUNT:
            raise TokenizerContractError("token_ids exceeds the token-count limit")
        if any(
            token_id < 0 or token_id >= MAX_VOCABULARY_SIZE
            for token_id in self.token_ids
        ):
            raise TokenizerContractError("token_ids contains an unsupported ID")


@dataclass(frozen=True, slots=True)
class DecodeResult:
    """Decoded text bound to the exact tokenizer fingerprint."""

    text: str
    tokenizer_fingerprint: str
    finish_status: FinishStatus

    def __post_init__(self) -> None:
        if len(self.text.encode("utf-8")) > MAX_TEXT_BYTES:
            raise TokenizerContractError("text exceeds the encoded byte limit")
        _require_sha256(self.tokenizer_fingerprint, "tokenizer_fingerprint")
