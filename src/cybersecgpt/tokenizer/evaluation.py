"""Deterministic, content-minimizing evaluation-manifest contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from math import gcd
from typing import Protocol

from cybersecgpt.tokenizer.contracts import (
    MAX_TEXT_BYTES,
    MAX_TOKEN_COUNT,
    DecodeRequest,
    DecodeResult,
    EncodeRequest,
    EncodeResult,
    FinishStatus,
    TokenizerContractError,
    TokenizerDescriptor,
)
from cybersecgpt.tokenizer.reference import Utf8ByteReferenceTokenizer

MAX_EVALUATION_SAMPLES = 10_000


class EvaluationDomain(StrEnum):
    """Required P6 tokenizer evaluation domains."""

    NATURAL_LANGUAGE = "natural_language"
    CODE = "code"
    LOGS = "logs"
    STRUCTURED_DATA = "structured_data"
    NETWORK = "network"
    SECURITY_IDENTIFIERS = "security_identifiers"
    DETECTION_RULES = "detection_rules"
    SECURITY_PROSE = "security_prose"


@dataclass(frozen=True, slots=True)
class EvaluationSample:
    """One inert sample with provenance and no implicit license assertion."""

    sample_id: str
    domain: EvaluationDomain
    text: str
    source_ref: str
    license_id: str
    content_sha256: str

    def __post_init__(self) -> None:
        for name in ("sample_id", "source_ref", "license_id"):
            value = getattr(self, name)
            if not value or len(value) > 256 or any(char.isspace() for char in value):
                raise TokenizerContractError(
                    f"{name} must contain 1..256 non-whitespace characters"
                )
        encoded = self.text.encode("utf-8")
        if len(encoded) > MAX_TEXT_BYTES:
            raise TokenizerContractError("evaluation sample exceeds the byte limit")
        expected = sha256(encoded).hexdigest()
        if self.content_sha256 != expected:
            raise TokenizerContractError("evaluation sample digest mismatch")

    @classmethod
    def from_text(
        cls,
        *,
        sample_id: str,
        domain: EvaluationDomain,
        text: str,
        source_ref: str,
        license_id: str,
    ) -> EvaluationSample:
        """Create a sample with its canonical UTF-8 content digest."""

        return cls(
            sample_id=sample_id,
            domain=domain,
            text=text,
            source_ref=source_ref,
            license_id=license_id,
            content_sha256=sha256(text.encode("utf-8")).hexdigest(),
        )


@dataclass(frozen=True, slots=True)
class EvaluationManifest:
    """A bounded, uniquely identified evaluation sample set."""

    manifest_id: str
    version: str
    samples: tuple[EvaluationSample, ...]

    def __post_init__(self) -> None:
        for name in ("manifest_id", "version"):
            value = getattr(self, name)
            if not value or len(value) > 128 or any(char.isspace() for char in value):
                raise TokenizerContractError(
                    f"{name} must contain 1..128 non-whitespace characters"
                )
        if not self.samples or len(self.samples) > MAX_EVALUATION_SAMPLES:
            raise TokenizerContractError(
                f"samples must contain 1..{MAX_EVALUATION_SAMPLES} entries"
            )
        identities = tuple(sample.sample_id for sample in self.samples)
        if len(identities) != len(set(identities)):
            raise TokenizerContractError("evaluation sample IDs must be unique")
        total_bytes = sum(len(sample.text.encode("utf-8")) for sample in self.samples)
        if total_bytes > MAX_TEXT_BYTES:
            raise TokenizerContractError("evaluation manifest exceeds the byte limit")


class EvaluationCandidate(Protocol):
    """Candidate operations required by deterministic structural evaluation."""

    @property
    def descriptor(self) -> TokenizerDescriptor:
        """Return the candidate's behavior-defining identity."""

    def encode(self, request: EncodeRequest) -> EncodeResult:
        """Encode one bounded request."""

    def decode(self, request: DecodeRequest) -> DecodeResult:
        """Decode one bounded request."""


@dataclass(frozen=True, slots=True)
class ExactRatio:
    """Reduced non-negative ratio with no floating-point variability."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if self.numerator < 0 or self.denominator <= 0:
            raise TokenizerContractError("ratio values are outside the supported range")
        divisor = gcd(self.numerator, self.denominator)
        if divisor != 1:
            raise TokenizerContractError("ratio must be reduced")

    @classmethod
    def from_counts(cls, numerator: int, denominator: int) -> ExactRatio | None:
        """Return a reduced ratio, or no ratio when the denominator is zero."""

        if numerator < 0 or denominator < 0:
            raise TokenizerContractError("ratio counts must be non-negative")
        if denominator == 0:
            return None
        divisor = gcd(numerator, denominator)
        return cls(numerator // divisor, denominator // divisor)


@dataclass(frozen=True, slots=True)
class CandidateSampleMetrics:
    """Content-minimizing structural metrics for one candidate and sample."""

    sample_id: str
    domain: EvaluationDomain
    content_sha256: str
    tokenizer_fingerprint: str
    utf8_byte_count: int
    unicode_scalar_count: int
    byte_reference_token_count: int
    candidate_token_count: int
    tokens_per_utf8_byte: ExactRatio | None
    tokens_per_unicode_scalar: ExactRatio | None
    compression_ratio_to_byte_reference: ExactRatio | None
    finish_status: FinishStatus
    decode_succeeded: bool
    reversible: bool


@dataclass(frozen=True, slots=True)
class CandidateEvaluationReport:
    """Deterministic structural report bound to a manifest and candidate."""

    manifest_id: str
    manifest_version: str
    algorithm_id: str
    tokenizer_fingerprint: str
    max_tokens: int
    samples: tuple[CandidateSampleMetrics, ...]


def evaluate_candidate(
    manifest: EvaluationManifest,
    candidate: EvaluationCandidate,
    *,
    max_tokens: int = MAX_TOKEN_COUNT,
) -> CandidateEvaluationReport:
    """Evaluate one candidate without timing noise or raw-text report fields."""

    descriptor = candidate.descriptor
    measurements: list[CandidateSampleMetrics] = []
    for sample in manifest.samples:
        encoded_text = sample.text.encode("utf-8")
        encoded = candidate.encode(EncodeRequest(sample.text, max_tokens=max_tokens))
        if encoded.tokenizer_fingerprint != descriptor.fingerprint:
            raise TokenizerContractError("encode result fingerprint mismatch")
        decode_succeeded = True
        reversible = False
        try:
            decoded = candidate.decode(DecodeRequest(encoded.token_ids))
        except TokenizerContractError:
            decode_succeeded = False
        else:
            if decoded.tokenizer_fingerprint != descriptor.fingerprint:
                raise TokenizerContractError("decode result fingerprint mismatch")
            reversible = (
                encoded.finish_status is FinishStatus.COMPLETED
                and decoded.finish_status is FinishStatus.COMPLETED
                and decoded.text == sample.text
            )
        candidate_count = len(encoded.token_ids)
        completed = encoded.finish_status is FinishStatus.COMPLETED
        measurements.append(
            CandidateSampleMetrics(
                sample_id=sample.sample_id,
                domain=sample.domain,
                content_sha256=sample.content_sha256,
                tokenizer_fingerprint=descriptor.fingerprint,
                utf8_byte_count=len(encoded_text),
                unicode_scalar_count=len(sample.text),
                byte_reference_token_count=len(encoded_text),
                candidate_token_count=candidate_count,
                tokens_per_utf8_byte=(
                    ExactRatio.from_counts(candidate_count, len(encoded_text))
                    if completed
                    else None
                ),
                tokens_per_unicode_scalar=(
                    ExactRatio.from_counts(candidate_count, len(sample.text))
                    if completed
                    else None
                ),
                compression_ratio_to_byte_reference=(
                    ExactRatio.from_counts(candidate_count, len(encoded_text))
                    if completed
                    else None
                ),
                finish_status=encoded.finish_status,
                decode_succeeded=decode_succeeded,
                reversible=reversible,
            )
        )
    return CandidateEvaluationReport(
        manifest_id=manifest.manifest_id,
        manifest_version=manifest.version,
        algorithm_id=descriptor.algorithm_id,
        tokenizer_fingerprint=descriptor.fingerprint,
        max_tokens=max_tokens,
        samples=tuple(measurements),
    )


@dataclass(frozen=True, slots=True)
class ReferenceSampleMetrics:
    """Content-minimizing structural measurements for one reference sample."""

    sample_id: str
    domain: EvaluationDomain
    content_sha256: str
    tokenizer_fingerprint: str
    utf8_byte_count: int
    unicode_scalar_count: int
    token_count: int
    finish_status: FinishStatus
    decode_succeeded: bool
    reversible: bool


def evaluate_utf8_byte_reference(
    manifest: EvaluationManifest,
    *,
    max_tokens: int = MAX_TOKEN_COUNT,
) -> tuple[ReferenceSampleMetrics, ...]:
    """Measure the fixed byte baseline without retaining text in the result."""

    report = evaluate_candidate(
        manifest, Utf8ByteReferenceTokenizer(), max_tokens=max_tokens
    )
    return tuple(
        ReferenceSampleMetrics(
            sample_id=metric.sample_id,
            domain=metric.domain,
            content_sha256=metric.content_sha256,
            tokenizer_fingerprint=metric.tokenizer_fingerprint,
            utf8_byte_count=metric.utf8_byte_count,
            unicode_scalar_count=metric.unicode_scalar_count,
            token_count=metric.candidate_token_count,
            finish_status=metric.finish_status,
            decode_succeeded=metric.decode_succeeded,
            reversible=metric.reversible,
        )
        for metric in report.samples
    )
