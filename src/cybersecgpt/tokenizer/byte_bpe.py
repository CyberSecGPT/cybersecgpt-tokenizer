"""Deterministic, evaluation-only byte-BPE candidate."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from typing import Final

from cybersecgpt.tokenizer.contracts import (
    MAX_TEXT_BYTES,
    MAX_VOCABULARY_SIZE,
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
MAX_EXPERIMENTAL_BPE_MERGES: Final = 256
MAX_EXPERIMENTAL_BPE_TRAINING_BYTES: Final = 1024 * 1024
_ALGORITHM_ID: Final = "experimental-byte-bpe-v1"


class BpeTrainingFinishStatus(StrEnum):
    """Explicit reasons for ending bounded candidate construction."""

    VOCABULARY_LIMIT = "vocabulary_limit"
    NO_ELIGIBLE_PAIR = "no_eligible_pair"
    MERGE_BUDGET = "merge_budget"


@dataclass(frozen=True, slots=True)
class ByteBpeTrainingConfig:
    """Bounded deterministic construction settings."""

    vocabulary_limit: int
    merge_budget: int = MAX_EXPERIMENTAL_BPE_MERGES
    max_training_bytes: int = MAX_EXPERIMENTAL_BPE_TRAINING_BYTES
    source_revision: str = "unspecified"

    def __post_init__(self) -> None:
        if not BYTE_ALPHABET_SIZE <= self.vocabulary_limit <= MAX_VOCABULARY_SIZE:
            raise TokenizerContractError(
                "vocabulary_limit is outside the supported range"
            )
        if not 0 <= self.merge_budget <= MAX_EXPERIMENTAL_BPE_MERGES:
            raise TokenizerContractError("merge_budget is outside the supported range")
        if not 0 <= self.max_training_bytes <= MAX_EXPERIMENTAL_BPE_TRAINING_BYTES:
            raise TokenizerContractError(
                "max_training_bytes is outside the supported range"
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


@dataclass(frozen=True, slots=True)
class BpeMerge:
    """One ordered adjacent-token merge."""

    left_id: int
    right_id: int
    token_id: int


def _candidate_fingerprint(
    tokens: tuple[bytes, ...], merges: tuple[BpeMerge, ...]
) -> str:
    digest = sha256()
    digest.update(b"cybersecgpt-experimental-byte-bpe-v1\x00")
    for merge in merges:
        digest.update(f"{merge.left_id}:{merge.right_id}:{merge.token_id}:".encode())
        digest.update(tokens[merge.token_id].hex().encode())
        digest.update(b"\n")
    return digest.hexdigest()


def _merge_pair(sequence: list[int], pair: tuple[int, int], token_id: int) -> list[int]:
    merged: list[int] = []
    index = 0
    while index < len(sequence):
        if index + 1 < len(sequence) and (sequence[index], sequence[index + 1]) == pair:
            merged.append(token_id)
            index += 2
        else:
            merged.append(sequence[index])
            index += 1
    return merged


@dataclass(frozen=True, slots=True)
class ByteBpeCandidate:
    """Immutable in-memory byte-BPE evaluation candidate."""

    tokens: tuple[bytes, ...]
    merges: tuple[BpeMerge, ...]

    def __post_init__(self) -> None:
        if not BYTE_ALPHABET_SIZE <= len(self.tokens) <= MAX_VOCABULARY_SIZE:
            raise TokenizerContractError("candidate vocabulary size is invalid")
        if self.tokens[:BYTE_ALPHABET_SIZE] != tuple(
            bytes((value,)) for value in range(BYTE_ALPHABET_SIZE)
        ):
            raise TokenizerContractError("candidate byte fallback alphabet is invalid")
        if len(self.merges) != len(self.tokens) - BYTE_ALPHABET_SIZE:
            raise TokenizerContractError(
                "candidate merge and vocabulary counts disagree"
            )
        for expected_id, merge in enumerate(self.merges, BYTE_ALPHABET_SIZE):
            if merge.token_id != expected_id:
                raise TokenizerContractError("candidate merge IDs are not consecutive")
            if (
                min(merge.left_id, merge.right_id) < 0
                or max(merge.left_id, merge.right_id) >= merge.token_id
            ):
                raise TokenizerContractError("candidate merge references an invalid ID")
            if self.tokens[merge.token_id] != (
                self.tokens[merge.left_id] + self.tokens[merge.right_id]
            ):
                raise TokenizerContractError("candidate merge bytes are inconsistent")

    @property
    def descriptor(self) -> TokenizerDescriptor:
        """Return identity bound to ordered merges and learned bytes."""

        return TokenizerDescriptor(
            tokenizer_id="experimental-byte-bpe",
            contract_version="1",
            algorithm_id=_ALGORITHM_ID,
            artifact_format_version="in-memory-1",
            normalization_profile="none",
            pretokenization_profile="utf8-bytes",
            vocabulary_size=len(self.tokens),
            fingerprint=_candidate_fingerprint(self.tokens, self.merges),
        )

    def encode(self, request: EncodeRequest) -> EncodeResult:
        """Encode with ordered learned merges and explicit truncation."""

        if request.add_special_tokens:
            raise TokenizerContractError(
                "the experimental BPE candidate has no special-token allocation"
            )
        sequence = list(request.text.encode("utf-8"))
        for merge in self.merges:
            sequence = _merge_pair(
                sequence, (merge.left_id, merge.right_id), merge.token_id
            )
        selected = sequence[: request.max_tokens]
        status = (
            FinishStatus.TRUNCATED
            if len(selected) < len(sequence)
            else FinishStatus.COMPLETED
        )
        return EncodeResult(tuple(selected), self.descriptor.fingerprint, status)

    def decode(self, request: DecodeRequest) -> DecodeResult:
        """Decode candidate IDs using strict UTF-8 with no replacement."""

        if any(token_id >= len(self.tokens) for token_id in request.token_ids):
            raise TokenizerContractError(
                "token_ids contains an invalid BPE candidate ID"
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
class ByteBpeTrainingResult:
    """Candidate plus content-minimizing construction evidence."""

    candidate: ByteBpeCandidate
    manifest_id: str
    manifest_version: str
    sample_digests: tuple[str, ...]
    requested_vocabulary_limit: int
    merge_budget: int
    max_training_bytes: int
    source_revision: str
    implementation_version: str
    finish_status: BpeTrainingFinishStatus


def train_byte_bpe_candidate(
    manifest: EvaluationManifest, config: ByteBpeTrainingConfig
) -> ByteBpeTrainingResult:
    """Construct a deterministic bounded in-memory byte-BPE candidate."""

    total_bytes = sum(len(sample.text.encode("utf-8")) for sample in manifest.samples)
    if total_bytes > config.max_training_bytes:
        raise TokenizerContractError("training manifest exceeds max_training_bytes")
    sequences = [list(sample.text.encode("utf-8")) for sample in manifest.samples]
    tokens = [bytes((value,)) for value in range(BYTE_ALPHABET_SIZE)]
    merges: list[BpeMerge] = []
    finish_status = BpeTrainingFinishStatus.NO_ELIGIBLE_PAIR
    while len(tokens) < config.vocabulary_limit and len(merges) < config.merge_budget:
        counts: Counter[tuple[int, int]] = Counter()
        for sequence in sequences:
            counts.update(zip(sequence, sequence[1:], strict=False))
        existing = set(tokens)
        eligible = [
            pair for pair in counts if tokens[pair[0]] + tokens[pair[1]] not in existing
        ]
        if not eligible:
            break
        pair = min(
            eligible,
            key=lambda item: (-counts[item], tokens[item[0]], tokens[item[1]]),
        )
        token_id = len(tokens)
        tokens.append(tokens[pair[0]] + tokens[pair[1]])
        merges.append(BpeMerge(pair[0], pair[1], token_id))
        sequences = [_merge_pair(sequence, pair, token_id) for sequence in sequences]
    if len(tokens) >= config.vocabulary_limit:
        finish_status = BpeTrainingFinishStatus.VOCABULARY_LIMIT
    elif len(merges) >= config.merge_budget:
        finish_status = BpeTrainingFinishStatus.MERGE_BUDGET
    candidate = ByteBpeCandidate(tuple(tokens), tuple(merges))
    return ByteBpeTrainingResult(
        candidate=candidate,
        manifest_id=manifest.manifest_id,
        manifest_version=manifest.version,
        sample_digests=tuple(sample.content_sha256 for sample in manifest.samples),
        requested_vocabulary_limit=config.vocabulary_limit,
        merge_budget=config.merge_budget,
        max_training_bytes=config.max_training_bytes,
        source_revision=config.source_revision,
        implementation_version=_ALGORITHM_ID,
        finish_status=finish_status,
    )
