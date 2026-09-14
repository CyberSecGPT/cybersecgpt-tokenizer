"""Canonical non-executable artifacts for the experimental byte-BPE candidate."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from struct import pack, unpack_from
from typing import Final

from cybersecgpt.tokenizer.byte_bpe import (
    BYTE_ALPHABET_SIZE,
    MAX_EXPERIMENTAL_BPE_MERGES,
    MAX_EXPERIMENTAL_BPE_TRAINING_BYTES,
    BpeMerge,
    BpeTrainingFinishStatus,
    ByteBpeCandidate,
    ByteBpeTrainingResult,
)
from cybersecgpt.tokenizer.contracts import (
    MAX_IDENTIFIER_LENGTH,
    TokenizerContractError,
)
from cybersecgpt.tokenizer.evaluation import (
    MAX_EVALUATION_SAMPLES,
    EvaluationDomain,
    EvaluationManifest,
)

ARTIFACT_FORMAT_ID: Final = "csgpt-experimental-bpe-artifact-v1"
ARTIFACT_FORMAT_VERSION: Final = 1
MAX_BPE_ARTIFACT_BYTES: Final = 16 * 1024 * 1024
MAX_BPE_ARTIFACT_TOKEN_BYTES: Final = 1024 * 1024
_MAX_ARTIFACT_VOCABULARY: Final = BYTE_ALPHABET_SIZE + MAX_EXPERIMENTAL_BPE_MERGES
_MAGIC: Final = b"CSGPTB1\x00"
_HEADER_SIZE: Final = 14
_DIGEST_SIZE: Final = 32
_ERROR: Final = "invalid canonical BPE artifact"


@dataclass(frozen=True, slots=True)
class ArtifactSampleProvenance:
    """Content-minimizing provenance for one artifact sample."""

    sample_id: str
    domain: EvaluationDomain
    source_ref: str
    license_id: str
    content_sha256: str


@dataclass(frozen=True, slots=True)
class LoadedByteBpeArtifact:
    """Validated immutable artifact content."""

    candidate: ByteBpeCandidate
    manifest_id: str
    manifest_version: str
    samples: tuple[ArtifactSampleProvenance, ...]
    requested_vocabulary_limit: int
    merge_budget: int
    max_training_bytes: int
    source_revision: str
    implementation_version: str
    finish_status: BpeTrainingFinishStatus
    artifact_digest: str
    canonical_bytes: bytes


def _invalid() -> TokenizerContractError:
    return TokenizerContractError(_ERROR)


def _text(value: str) -> bytes:
    encoded = value.encode("utf-8")
    if not encoded or len(encoded) > 0xFFFF:
        raise _invalid()
    return pack("!H", len(encoded)) + encoded


def _identifier(value: str, maximum: int = MAX_IDENTIFIER_LENGTH) -> None:
    if not value or len(value) > maximum or any(char.isspace() for char in value):
        raise _invalid()


def _source_revision(value: str) -> None:
    _identifier(value, 128)
    if not value.isascii():
        raise _invalid()


def _digest(value: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise _invalid()


def _expected_finish_status(
    vocabulary_count: int,
    merge_count: int,
    requested_vocabulary_limit: int,
    merge_budget: int,
) -> BpeTrainingFinishStatus:
    if vocabulary_count >= requested_vocabulary_limit:
        return BpeTrainingFinishStatus.VOCABULARY_LIMIT
    if merge_count >= merge_budget:
        return BpeTrainingFinishStatus.MERGE_BUDGET
    return BpeTrainingFinishStatus.NO_ELIGIBLE_PAIR


def _validate_binding(
    result: ByteBpeTrainingResult, manifest: EvaluationManifest
) -> None:
    if (
        result.manifest_id != manifest.manifest_id
        or result.manifest_version != manifest.version
        or result.sample_digests
        != tuple(sample.content_sha256 for sample in manifest.samples)
        or result.requested_vocabulary_limit < len(result.candidate.tokens)
        or not BYTE_ALPHABET_SIZE
        <= result.requested_vocabulary_limit
        <= _MAX_ARTIFACT_VOCABULARY
        or not 0 <= result.merge_budget <= MAX_EXPERIMENTAL_BPE_MERGES
        or len(result.candidate.merges) > result.merge_budget
        or not 0 <= result.max_training_bytes <= MAX_EXPERIMENTAL_BPE_TRAINING_BYTES
        or result.finish_status
        is not _expected_finish_status(
            len(result.candidate.tokens),
            len(result.candidate.merges),
            result.requested_vocabulary_limit,
            result.merge_budget,
        )
    ):
        raise _invalid()
    _source_revision(result.source_revision)
    _identifier(result.implementation_version)
    if result.implementation_version != result.candidate.descriptor.algorithm_id:
        raise _invalid()


def serialize_byte_bpe_artifact(
    result: ByteBpeTrainingResult, manifest: EvaluationManifest
) -> bytes:
    """Serialize a training result and its exact manifest to canonical bytes."""

    if not isinstance(result, ByteBpeTrainingResult) or not isinstance(
        manifest, EvaluationManifest
    ):
        raise _invalid()
    _validate_binding(result, manifest)
    descriptor = result.candidate.descriptor
    fields = [
        _text(ARTIFACT_FORMAT_ID),
        *(
            _text(value)
            for value in (
                descriptor.tokenizer_id,
                descriptor.contract_version,
                descriptor.algorithm_id,
                descriptor.artifact_format_version,
                descriptor.normalization_profile,
                descriptor.pretokenization_profile,
                descriptor.fingerprint,
                manifest.manifest_id,
                manifest.version,
            )
        ),
        pack("!I", len(manifest.samples)),
    ]
    for sample in manifest.samples:
        fields.extend(
            (
                _text(sample.sample_id),
                _text(sample.domain.value),
                _text(sample.source_ref),
                _text(sample.license_id),
                _text(sample.content_sha256),
            )
        )
    fields.extend(
        (
            pack(
                "!III",
                result.requested_vocabulary_limit,
                result.merge_budget,
                result.max_training_bytes,
            ),
            _text(result.source_revision),
            _text(result.implementation_version),
            _text(result.finish_status.value),
            pack("!I", len(result.candidate.tokens)),
        )
    )
    for token in result.candidate.tokens:
        if not token or len(token) > MAX_BPE_ARTIFACT_TOKEN_BYTES:
            raise _invalid()
        fields.extend((pack("!I", len(token)), token))
    fields.append(pack("!I", len(result.candidate.merges)))
    fields.extend(
        pack("!III", merge.left_id, merge.right_id, merge.token_id)
        for merge in result.candidate.merges
    )
    payload = b"".join(fields)
    envelope = _MAGIC + pack("!HI", ARTIFACT_FORMAT_VERSION, len(payload)) + payload
    if len(envelope) + _DIGEST_SIZE > MAX_BPE_ARTIFACT_BYTES:
        raise _invalid()
    return envelope + sha256(envelope).digest()


class _Reader:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.offset = 0

    def _take(self, size: int) -> bytes:
        if size < 0 or size > len(self.payload) - self.offset:
            raise _invalid()
        start = self.offset
        self.offset += size
        return self.payload[start : self.offset]

    def integer(self) -> int:
        return int(unpack_from("!I", self._take(4))[0])

    def text(self, maximum_bytes: int = 0xFFFF) -> str:
        size = unpack_from("!H", self._take(2))[0]
        if size == 0 or size > maximum_bytes:
            raise _invalid()
        try:
            return self._take(size).decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise _invalid() from error


def _read_identifier(reader: _Reader, maximum: int = MAX_IDENTIFIER_LENGTH) -> str:
    value = reader.text()
    _identifier(value, maximum)
    return value


def load_byte_bpe_artifact(data: bytes) -> LoadedByteBpeArtifact:
    """Load canonical bytes after bounded, fail-closed validation."""

    if (
        type(data) is not bytes
        or not _HEADER_SIZE + _DIGEST_SIZE <= len(data) <= MAX_BPE_ARTIFACT_BYTES
    ):
        raise _invalid()
    if data[:8] != _MAGIC:
        raise _invalid()
    version, payload_size = unpack_from("!HI", data, 8)
    if version != ARTIFACT_FORMAT_VERSION:
        raise _invalid()
    if payload_size != len(data) - _HEADER_SIZE - _DIGEST_SIZE:
        raise _invalid()
    envelope = data[:-_DIGEST_SIZE]
    if sha256(envelope).digest() != data[-_DIGEST_SIZE:]:
        raise _invalid()
    reader = _Reader(data[_HEADER_SIZE:-_DIGEST_SIZE])
    if reader.text() != ARTIFACT_FORMAT_ID:
        raise _invalid()
    descriptor_values = tuple(_read_identifier(reader) for _ in range(6))
    candidate_fingerprint = reader.text(64)
    _digest(candidate_fingerprint)
    manifest_id = _read_identifier(reader, 128)
    manifest_version = _read_identifier(reader, 128)
    sample_count = reader.integer()
    if not 1 <= sample_count <= MAX_EVALUATION_SAMPLES:
        raise _invalid()
    samples: list[ArtifactSampleProvenance] = []
    identities: set[str] = set()
    for _ in range(sample_count):
        sample_id = _read_identifier(reader, 256)
        domain_value = _read_identifier(reader, 256)
        source_ref = _read_identifier(reader, 256)
        license_id = _read_identifier(reader, 256)
        content_digest = reader.text(64)
        _digest(content_digest)
        if sample_id in identities:
            raise _invalid()
        identities.add(sample_id)
        try:
            domain = EvaluationDomain(domain_value)
        except ValueError as error:
            raise _invalid() from error
        samples.append(
            ArtifactSampleProvenance(
                sample_id, domain, source_ref, license_id, content_digest
            )
        )
    requested_vocabulary_limit = reader.integer()
    merge_budget = reader.integer()
    max_training_bytes = reader.integer()
    source_revision = _read_identifier(reader, 128)
    _source_revision(source_revision)
    implementation_version = _read_identifier(reader)
    try:
        finish_status = BpeTrainingFinishStatus(_read_identifier(reader))
    except ValueError as error:
        raise _invalid() from error
    vocabulary_count = reader.integer()
    if not BYTE_ALPHABET_SIZE <= vocabulary_count <= _MAX_ARTIFACT_VOCABULARY:
        raise _invalid()
    tokens: list[bytes] = []
    for _ in range(vocabulary_count):
        token_size = reader.integer()
        if not 1 <= token_size <= MAX_BPE_ARTIFACT_TOKEN_BYTES:
            raise _invalid()
        tokens.append(reader._take(token_size))
    merge_count = reader.integer()
    if (
        merge_count > MAX_EXPERIMENTAL_BPE_MERGES
        or merge_count != vocabulary_count - BYTE_ALPHABET_SIZE
        or merge_count > (len(reader.payload) - reader.offset) // 12
    ):
        raise _invalid()
    merges = tuple(
        BpeMerge(reader.integer(), reader.integer(), reader.integer())
        for _ in range(merge_count)
    )
    if reader.offset != len(reader.payload):
        raise _invalid()
    try:
        candidate = ByteBpeCandidate(tuple(tokens), merges)
    except TokenizerContractError as error:
        raise _invalid() from error
    descriptor = candidate.descriptor
    if (
        descriptor_values
        != (
            descriptor.tokenizer_id,
            descriptor.contract_version,
            descriptor.algorithm_id,
            descriptor.artifact_format_version,
            descriptor.normalization_profile,
            descriptor.pretokenization_profile,
        )
        or candidate_fingerprint != descriptor.fingerprint
    ):
        raise _invalid()
    if (
        not BYTE_ALPHABET_SIZE <= requested_vocabulary_limit <= _MAX_ARTIFACT_VOCABULARY
        or requested_vocabulary_limit < vocabulary_count
        or not 0 <= merge_budget <= MAX_EXPERIMENTAL_BPE_MERGES
        or merge_count > merge_budget
        or not 0 <= max_training_bytes <= MAX_EXPERIMENTAL_BPE_TRAINING_BYTES
        or implementation_version != descriptor.algorithm_id
        or finish_status
        is not _expected_finish_status(
            vocabulary_count,
            merge_count,
            requested_vocabulary_limit,
            merge_budget,
        )
    ):
        raise _invalid()
    loaded = LoadedByteBpeArtifact(
        candidate,
        manifest_id,
        manifest_version,
        tuple(samples),
        requested_vocabulary_limit,
        merge_budget,
        max_training_bytes,
        source_revision,
        implementation_version,
        finish_status,
        sha256(envelope).hexdigest(),
        data,
    )
    if _serialize_loaded(loaded) != data:
        raise _invalid()
    return loaded


def _serialize_loaded(loaded: LoadedByteBpeArtifact) -> bytes:
    """Rebuild canonical bytes without inventing manifest text."""

    descriptor = loaded.candidate.descriptor
    fields = [
        _text(ARTIFACT_FORMAT_ID),
        *(
            _text(value)
            for value in (
                descriptor.tokenizer_id,
                descriptor.contract_version,
                descriptor.algorithm_id,
                descriptor.artifact_format_version,
                descriptor.normalization_profile,
                descriptor.pretokenization_profile,
                descriptor.fingerprint,
                loaded.manifest_id,
                loaded.manifest_version,
            )
        ),
        pack("!I", len(loaded.samples)),
    ]
    for sample in loaded.samples:
        fields.extend(
            _text(value)
            for value in (
                sample.sample_id,
                sample.domain.value,
                sample.source_ref,
                sample.license_id,
                sample.content_sha256,
            )
        )
    fields.extend(
        (
            pack(
                "!III",
                loaded.requested_vocabulary_limit,
                loaded.merge_budget,
                loaded.max_training_bytes,
            ),
            _text(loaded.source_revision),
            _text(loaded.implementation_version),
            _text(loaded.finish_status.value),
            pack("!I", len(loaded.candidate.tokens)),
        )
    )
    for token in loaded.candidate.tokens:
        fields.extend((pack("!I", len(token)), token))
    fields.append(pack("!I", len(loaded.candidate.merges)))
    fields.extend(
        pack("!III", merge.left_id, merge.right_id, merge.token_id)
        for merge in loaded.candidate.merges
    )
    payload = b"".join(fields)
    envelope = _MAGIC + pack("!HI", ARTIFACT_FORMAT_VERSION, len(payload)) + payload
    return envelope + sha256(envelope).digest()
