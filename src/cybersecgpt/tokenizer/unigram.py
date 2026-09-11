"""Deterministic, evaluation-only byte-frequency Unigram candidate."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from typing import Final, cast

from cybersecgpt.tokenizer.contracts import (
    MAX_TEXT_BYTES,
    DecodeRequest,
    DecodeResult,
    EncodeRequest,
    EncodeResult,
    FinishStatus,
    TokenizerContractError,
    TokenizerDescriptor,
)
from cybersecgpt.tokenizer.evaluation import EvaluationManifest

BYTE_ALPHABET_SIZE: Final = 256
MAX_UNIGRAM_PIECE_BYTES: Final = 16
MAX_UNIGRAM_DISTINCT_SUBSTRINGS: Final = 262_144
MAX_UNIGRAM_SEED_PIECES: Final = 8_192
MAX_UNIGRAM_VOCABULARY_SIZE: Final = 8_192
MAX_UNIGRAM_TRAINING_BYTES: Final = 1024 * 1024
UNIGRAM_COST_SCALE: Final = 1 << 20
_ALGORITHM_ID: Final = "experimental-byte-frequency-unigram-v1"
_MAX_COST: Final = (
    MAX_UNIGRAM_TRAINING_BYTES * MAX_UNIGRAM_PIECE_BYTES + MAX_UNIGRAM_VOCABULARY_SIZE
) * UNIGRAM_COST_SCALE


class UnigramTrainingFinishStatus(StrEnum):
    """Explicit reasons for successful bounded candidate construction."""

    VOCABULARY_LIMIT = "vocabulary_limit"
    CANDIDATE_EXHAUSTED = "candidate_exhausted"


@dataclass(frozen=True, slots=True)
class ByteUnigramTrainingConfig:
    """Bounded deterministic construction settings."""

    vocabulary_limit: int
    max_training_bytes: int = MAX_UNIGRAM_TRAINING_BYTES
    source_revision: str = "unspecified"

    def __post_init__(self) -> None:
        if (
            not BYTE_ALPHABET_SIZE
            <= self.vocabulary_limit
            <= (MAX_UNIGRAM_VOCABULARY_SIZE)
        ):
            raise TokenizerContractError(
                "vocabulary_limit is outside the Unigram candidate range"
            )
        if not 0 <= self.max_training_bytes <= MAX_UNIGRAM_TRAINING_BYTES:
            raise TokenizerContractError(
                "max_training_bytes is outside the Unigram candidate range"
            )
        if (
            not self.source_revision
            or len(self.source_revision) > 128
            or not self.source_revision.isascii()
            or any(character.isspace() for character in self.source_revision)
        ):
            raise TokenizerContractError(
                "source_revision must contain 1..128 non-whitespace ASCII characters"
            )


def _candidate_fingerprint(tokens: tuple[bytes, ...], costs: tuple[int, ...]) -> str:
    digest = sha256(b"cybersecgpt-experimental-byte-frequency-unigram-v1\x00")
    for token_id, (piece, cost) in enumerate(zip(tokens, costs, strict=True)):
        digest.update(f"{token_id}:{cost}:{piece.hex()}\n".encode())
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class ByteUnigramCandidate:
    """Immutable in-memory byte-frequency Unigram evaluation candidate."""

    tokens: tuple[bytes, ...]
    costs: tuple[int, ...]

    def __post_init__(self) -> None:
        if not BYTE_ALPHABET_SIZE <= len(self.tokens) <= (MAX_UNIGRAM_VOCABULARY_SIZE):
            raise TokenizerContractError("Unigram candidate vocabulary size is invalid")
        if self.tokens[:BYTE_ALPHABET_SIZE] != tuple(
            bytes((value,)) for value in range(BYTE_ALPHABET_SIZE)
        ):
            raise TokenizerContractError("Unigram candidate byte fallback is invalid")
        if len(self.costs) != len(self.tokens):
            raise TokenizerContractError(
                "Unigram candidate token and cost counts differ"
            )
        if len(self.tokens) != len(set(self.tokens)):
            raise TokenizerContractError("Unigram candidate pieces must be unique")
        if any(
            not 2 <= len(piece) <= MAX_UNIGRAM_PIECE_BYTES
            for piece in self.tokens[BYTE_ALPHABET_SIZE:]
        ):
            raise TokenizerContractError("Unigram learned piece length is invalid")
        if any(not 1 <= cost <= _MAX_COST for cost in self.costs):
            raise TokenizerContractError("Unigram candidate cost is invalid")

    @property
    def descriptor(self) -> TokenizerDescriptor:
        """Return identity bound to every ordered piece and integer cost."""

        return TokenizerDescriptor(
            tokenizer_id="experimental-byte-frequency-unigram",
            contract_version="1",
            algorithm_id=_ALGORITHM_ID,
            artifact_format_version="in-memory-1",
            normalization_profile="none",
            pretokenization_profile="utf8-bytes",
            vocabulary_size=len(self.tokens),
            fingerprint=_candidate_fingerprint(self.tokens, self.costs),
        )

    def encode(self, request: EncodeRequest) -> EncodeResult:
        """Choose the deterministic minimum-cost complete byte segmentation."""

        if request.add_special_tokens:
            raise TokenizerContractError(
                "the experimental Unigram candidate has no special-token allocation"
            )
        encoded = request.text.encode("utf-8")
        piece_ids = {piece: token_id for token_id, piece in enumerate(self.tokens)}
        size = len(encoded)
        best_cost: list[int | None] = [None] * (size + 1)
        best_count = [0] * (size + 1)
        best_token = [0] * size
        best_next = [0] * size
        best_cost[size] = 0
        for offset in range(size - 1, -1, -1):
            best_key: tuple[int, int, int] | None = None
            max_piece = min(MAX_UNIGRAM_PIECE_BYTES, size - offset)
            matching_ids: list[int] = []
            for piece_size in range(1, max_piece + 1):
                token_id = piece_ids.get(encoded[offset : offset + piece_size])
                if token_id is not None:
                    matching_ids.append(token_id)
            for token_id in sorted(matching_ids):
                piece_size = len(self.tokens[token_id])
                following = offset + piece_size
                following_cost = cast(int, best_cost[following])
                key = (
                    self.costs[token_id] + following_cost,
                    1 + best_count[following],
                    token_id,
                )
                if best_key is None or key < best_key:
                    best_key = key
                    best_cost[offset] = key[0]
                    best_count[offset] = key[1]
                    best_token[offset] = token_id
                    best_next[offset] = following
        token_ids: list[int] = []
        offset = 0
        while offset < size:
            token_ids.append(best_token[offset])
            offset = best_next[offset]
        selected = token_ids[: request.max_tokens]
        finish_status = (
            FinishStatus.TRUNCATED
            if len(selected) < len(token_ids)
            else FinishStatus.COMPLETED
        )
        return EncodeResult(tuple(selected), self.descriptor.fingerprint, finish_status)

    def decode(self, request: DecodeRequest) -> DecodeResult:
        """Decode candidate IDs using strict UTF-8 with no replacement."""

        if any(token_id >= len(self.tokens) for token_id in request.token_ids):
            raise TokenizerContractError(
                "token_ids contains an invalid Unigram candidate ID"
            )
        output_size = sum(len(self.tokens[token_id]) for token_id in request.token_ids)
        if output_size > MAX_TEXT_BYTES:
            raise TokenizerContractError("decoded bytes exceeds the output limit")
        encoded = b"".join(self.tokens[token_id] for token_id in request.token_ids)
        try:
            text = encoded.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise TokenizerContractError(
                "token_ids is not a complete valid UTF-8 byte sequence"
            ) from error
        return DecodeResult(text, self.descriptor.fingerprint, FinishStatus.COMPLETED)


@dataclass(frozen=True, slots=True)
class ByteUnigramTrainingResult:
    """Candidate plus content-minimizing deterministic construction evidence."""

    candidate: ByteUnigramCandidate
    manifest_id: str
    manifest_version: str
    sample_digests: tuple[str, ...]
    requested_vocabulary_limit: int
    max_training_bytes: int
    source_revision: str
    implementation_version: str
    finish_status: UnigramTrainingFinishStatus


def train_byte_unigram_candidate(
    manifest: EvaluationManifest, config: ByteUnigramTrainingConfig
) -> ByteUnigramTrainingResult:
    """Construct a deterministic bounded in-memory frequency-Unigram candidate."""

    contents = tuple(sample.text.encode("utf-8") for sample in manifest.samples)
    total_bytes = sum(len(content) for content in contents)
    if total_bytes > config.max_training_bytes:
        raise TokenizerContractError("training manifest exceeds max_training_bytes")

    byte_counts: Counter[int] = Counter()
    substring_counts: Counter[bytes] = Counter()
    for content in contents:
        byte_counts.update(content)
        for start in range(len(content)):
            stop = min(len(content), start + MAX_UNIGRAM_PIECE_BYTES)
            for end in range(start + 2, stop + 1):
                piece = content[start:end]
                if (
                    piece not in substring_counts
                    and len(substring_counts) >= MAX_UNIGRAM_DISTINCT_SUBSTRINGS
                ):
                    raise TokenizerContractError(
                        "resource_limit: too many distinct Unigram substrings"
                    )
                substring_counts[piece] += 1

    ranked = sorted(
        ((piece, count) for piece, count in substring_counts.items() if count >= 2),
        key=lambda item: (-item[1], item[0]),
    )[:MAX_UNIGRAM_SEED_PIECES]
    learned_limit = config.vocabulary_limit - BYTE_ALPHABET_SIZE
    selected = ranked[:learned_limit]
    alphabet = tuple(bytes((value,)) for value in range(BYTE_ALPHABET_SIZE))
    tokens = alphabet + tuple(piece for piece, _ in selected)
    observed = tuple(byte_counts[value] for value in range(BYTE_ALPHABET_SIZE)) + tuple(
        count for _, count in selected
    )
    effective = tuple(count + 1 for count in observed)
    total = sum(effective)
    costs = tuple(
        max(1, (total * UNIGRAM_COST_SCALE + count - 1) // count) for count in effective
    )
    finish_status = (
        UnigramTrainingFinishStatus.VOCABULARY_LIMIT
        if len(selected) == learned_limit
        else UnigramTrainingFinishStatus.CANDIDATE_EXHAUSTED
    )
    return ByteUnigramTrainingResult(
        candidate=ByteUnigramCandidate(tokens, costs),
        manifest_id=manifest.manifest_id,
        manifest_version=manifest.version,
        sample_digests=tuple(sample.content_sha256 for sample in manifest.samples),
        requested_vocabulary_limit=config.vocabulary_limit,
        max_training_bytes=config.max_training_bytes,
        source_revision=config.source_revision,
        implementation_version=_ALGORITHM_ID,
        finish_status=finish_status,
    )
