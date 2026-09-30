"""Canonical, bounded corpus manifests and offline admission verification."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from hashlib import sha256
from struct import pack
from typing import Final

from cybersecgpt.tokenizer.contracts import MAX_TEXT_BYTES, TokenizerContractError
from cybersecgpt.tokenizer.evaluation import EvaluationDomain

CORPUS_MANIFEST_SCHEMA_VERSION: Final = "csgpt-corpus-manifest-v1"
MAX_CORPUS_SOURCES: Final = 1_024
MAX_CORPUS_SAMPLES: Final = 100_000
MAX_CORPUS_TRANSFORMATIONS: Final = 128
MAX_CORPUS_EXCLUSION_REASONS: Final = 128
MAX_CORPUS_IDENTIFIER_BYTES: Final = 256
MAX_CORPUS_TEXT_BYTES: Final = 2_048
_DIGEST_LENGTH: Final = 64
_ERROR: Final = "invalid corpus admission manifest"


class RightsDecision(StrEnum):
    """Explicit source-rights review result."""

    APPROVED = "approved"
    REJECTED = "rejected"
    UNKNOWN = "unknown"
    REVOKED = "revoked"


class SafetyDecision(StrEnum):
    """Explicit sensitive-content and contamination review result."""

    CLEAN = "clean"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


def _invalid() -> TokenizerContractError:
    return TokenizerContractError(_ERROR)


def _digest(value: str) -> None:
    if len(value) != _DIGEST_LENGTH or any(c not in "0123456789abcdef" for c in value):
        raise _invalid()


def _text(value: str, *, maximum: int = MAX_CORPUS_TEXT_BYTES) -> bytes:
    encoded = value.encode("utf-8")
    if not encoded or len(encoded) > maximum or "\x00" in value:
        raise _invalid()
    return pack("!I", len(encoded)) + encoded


def _identifier(value: str) -> bytes:
    encoded = _text(value, maximum=MAX_CORPUS_IDENTIFIER_BYTES)
    if not value.isascii() or any(character.isspace() for character in value):
        raise _invalid()
    return encoded


def _date(value: str) -> bytes:
    if (
        len(value) != 10
        or value[4] != "-"
        or value[7] != "-"
        or not (value[:4] + value[5:7] + value[8:]).isdigit()
    ):
        raise _invalid()
    year, month, day = (int(part) for part in value.split("-"))
    if year < 2000 or month not in range(1, 13) or day not in range(1, 32):
        raise _invalid()
    return _text(value)


@dataclass(frozen=True, slots=True)
class CorpusSourceRecord:
    """Content-minimizing source provenance and reviewed rights."""

    source_id: str
    origin_ref: str
    acquisition_method: str
    acquired_at: str
    source_revision: str
    source_sha256: str
    license_expression: str
    obligations_sha256: str
    reviewer_id: str
    reviewed_at: str
    rights_decision: RightsDecision
    sensitive_data_decision: SafetyDecision
    contamination_decision: SafetyDecision
    acquisition_allowed: bool
    processing_allowed: bool
    training_allowed: bool
    derived_statistics_allowed: bool
    artifact_distribution_allowed: bool

    def __post_init__(self) -> None:
        for value in (
            self.source_id,
            self.acquisition_method,
            self.source_revision,
            self.reviewer_id,
        ):
            _identifier(value)
        for value in (self.origin_ref, self.license_expression):
            _text(value)
        _date(self.acquired_at)
        _date(self.reviewed_at)
        _digest(self.source_sha256)
        _digest(self.obligations_sha256)


@dataclass(frozen=True, slots=True)
class CorpusTransformation:
    """One deterministic, versioned corpus transformation."""

    stage_id: str
    tool_id: str
    configuration_sha256: str

    def __post_init__(self) -> None:
        _identifier(self.stage_id)
        _identifier(self.tool_id)
        _digest(self.configuration_sha256)


@dataclass(frozen=True, slots=True)
class CorpusSampleRecord:
    """One ordered sample identity without retaining raw content."""

    sample_id: str
    source_id: str
    domain: EvaluationDomain
    byte_count: int
    content_sha256: str

    def __post_init__(self) -> None:
        _identifier(self.sample_id)
        _identifier(self.source_id)
        if not 0 <= self.byte_count <= MAX_TEXT_BYTES:
            raise _invalid()
        _digest(self.content_sha256)


@dataclass(frozen=True, slots=True)
class CorpusAdmissionManifest:
    """Canonical exact corpus snapshot admission manifest."""

    corpus_id: str
    schema_version: str
    approved_purpose: str
    artifact_distribution_terms: str
    sources: tuple[CorpusSourceRecord, ...]
    transformations: tuple[CorpusTransformation, ...]
    samples: tuple[CorpusSampleRecord, ...]
    exclusion_counts: tuple[tuple[str, int], ...]
    manifest_sha256: str

    def __post_init__(self) -> None:
        _identifier(self.corpus_id)
        if self.schema_version != CORPUS_MANIFEST_SCHEMA_VERSION:
            raise _invalid()
        _text(self.approved_purpose)
        _text(self.artifact_distribution_terms)
        if not 1 <= len(self.sources) <= MAX_CORPUS_SOURCES:
            raise _invalid()
        if not 1 <= len(self.samples) <= MAX_CORPUS_SAMPLES:
            raise _invalid()
        if not 1 <= len(self.transformations) <= MAX_CORPUS_TRANSFORMATIONS:
            raise _invalid()
        if len(self.exclusion_counts) > MAX_CORPUS_EXCLUSION_REASONS:
            raise _invalid()
        source_ids = tuple(source.source_id for source in self.sources)
        sample_ids = tuple(sample.sample_id for sample in self.samples)
        sample_digests = tuple(sample.content_sha256 for sample in self.samples)
        stage_ids = tuple(stage.stage_id for stage in self.transformations)
        reasons = tuple(reason for reason, _ in self.exclusion_counts)
        if any(
            len(values) != len(set(values))
            for values in (source_ids, sample_ids, sample_digests, stage_ids, reasons)
        ):
            raise _invalid()
        if any(sample.source_id not in source_ids for sample in self.samples):
            raise _invalid()
        total = sum(sample.byte_count for sample in self.samples)
        if total > MAX_TEXT_BYTES:
            raise _invalid()
        for reason, count in self.exclusion_counts:
            _identifier(reason)
            if not 0 <= count <= MAX_CORPUS_SAMPLES:
                raise _invalid()
        if self.manifest_sha256:
            _digest(self.manifest_sha256)
            if self.manifest_sha256 != sha256(self.canonical_bytes()).hexdigest():
                raise _invalid()

    def canonical_bytes(self) -> bytes:
        """Return canonical bytes excluding the self-referential manifest digest."""

        parts = [
            _text("CSGPT-CORPUS-MANIFEST"),
            _identifier(self.schema_version),
            _identifier(self.corpus_id),
            _text(self.approved_purpose),
            _text(self.artifact_distribution_terms),
            pack("!I", len(self.sources)),
        ]
        for source in self.sources:
            parts.extend(
                (
                    _identifier(source.source_id),
                    _text(source.origin_ref),
                    _identifier(source.acquisition_method),
                    _date(source.acquired_at),
                    _identifier(source.source_revision),
                    bytes.fromhex(source.source_sha256),
                    _text(source.license_expression),
                    bytes.fromhex(source.obligations_sha256),
                    _identifier(source.reviewer_id),
                    _date(source.reviewed_at),
                    _identifier(source.rights_decision.value),
                    _identifier(source.sensitive_data_decision.value),
                    _identifier(source.contamination_decision.value),
                    bytes(
                        (
                            source.acquisition_allowed,
                            source.processing_allowed,
                            source.training_allowed,
                            source.derived_statistics_allowed,
                            source.artifact_distribution_allowed,
                        )
                    ),
                )
            )
        parts.append(pack("!I", len(self.transformations)))
        for stage in self.transformations:
            parts.extend(
                (
                    _identifier(stage.stage_id),
                    _identifier(stage.tool_id),
                    bytes.fromhex(stage.configuration_sha256),
                )
            )
        parts.append(pack("!I", len(self.samples)))
        for sample in self.samples:
            parts.extend(
                (
                    _identifier(sample.sample_id),
                    _identifier(sample.source_id),
                    _identifier(sample.domain.value),
                    pack("!Q", sample.byte_count),
                    bytes.fromhex(sample.content_sha256),
                )
            )
        parts.append(pack("!I", len(self.exclusion_counts)))
        for reason, count in self.exclusion_counts:
            parts.extend((_identifier(reason), pack("!Q", count)))
        return b"".join(parts)

    def with_computed_digest(self) -> CorpusAdmissionManifest:
        """Return this validated manifest with its exact canonical digest."""

        if self.manifest_sha256:
            return self
        return replace(self, manifest_sha256=sha256(self.canonical_bytes()).hexdigest())


@dataclass(frozen=True, slots=True)
class CorpusSampleContent:
    """Locally supplied inert bytes for one exact manifest sample."""

    sample_id: str
    content: bytes

    def __post_init__(self) -> None:
        _identifier(self.sample_id)
        if type(self.content) is not bytes or len(self.content) > MAX_TEXT_BYTES:
            raise _invalid()


@dataclass(frozen=True, slots=True)
class CorpusAdmissionResult:
    """Content-minimizing successful admission evidence."""

    corpus_id: str
    manifest_sha256: str
    sample_count: int
    total_bytes: int
    source_ids: tuple[str, ...]
    sample_digests: tuple[str, ...]
    domains: tuple[EvaluationDomain, ...]


def admit_corpus(
    manifest: CorpusAdmissionManifest,
    supplied: tuple[CorpusSampleContent, ...],
    *,
    cancelled: bool = False,
    deadline_ns: int | None = None,
    now_ns: int | None = None,
) -> CorpusAdmissionResult:
    """Verify exact local content without I/O, networking, or raw-content output."""

    if not manifest.manifest_sha256 or cancelled:
        raise _invalid()
    if (deadline_ns is None) != (now_ns is None):
        raise _invalid()
    if deadline_ns is not None and now_ns is not None and now_ns >= deadline_ns:
        raise _invalid()
    if any(
        source.rights_decision is not RightsDecision.APPROVED
        or source.sensitive_data_decision is not SafetyDecision.CLEAN
        or source.contamination_decision is not SafetyDecision.CLEAN
        or not all(
            (
                source.acquisition_allowed,
                source.processing_allowed,
                source.training_allowed,
                source.derived_statistics_allowed,
                source.artifact_distribution_allowed,
            )
        )
        for source in manifest.sources
    ):
        raise _invalid()
    if len(supplied) != len(manifest.samples):
        raise _invalid()
    total_bytes = 0
    for expected, actual in zip(manifest.samples, supplied, strict=True):
        if actual.sample_id != expected.sample_id:
            raise _invalid()
        total_bytes += len(actual.content)
        if (
            total_bytes > MAX_TEXT_BYTES
            or len(actual.content) != expected.byte_count
            or sha256(actual.content).hexdigest() != expected.content_sha256
        ):
            raise _invalid()
    domains = tuple(dict.fromkeys(sample.domain for sample in manifest.samples))
    return CorpusAdmissionResult(
        corpus_id=manifest.corpus_id,
        manifest_sha256=manifest.manifest_sha256,
        sample_count=len(manifest.samples),
        total_bytes=total_bytes,
        source_ids=tuple(source.source_id for source in manifest.sources),
        sample_digests=tuple(sample.content_sha256 for sample in manifest.samples),
        domains=domains,
    )
