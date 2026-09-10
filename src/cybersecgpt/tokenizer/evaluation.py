"""Deterministic, content-minimizing evaluation-manifest contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256

from cybersecgpt.tokenizer.contracts import (
    MAX_TEXT_BYTES,
    MAX_TOKEN_COUNT,
    DecodeRequest,
    EncodeRequest,
    FinishStatus,
    TokenizerContractError,
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

    measurements: list[ReferenceSampleMetrics] = []
    for sample in manifest.samples:
        encoded_text = sample.text.encode("utf-8")
        encoded = Utf8ByteReferenceTokenizer.encode(
            EncodeRequest(sample.text, max_tokens=max_tokens)
        )
        decode_succeeded = True
        reversible = False
        try:
            decoded = Utf8ByteReferenceTokenizer.decode(
                DecodeRequest(encoded.token_ids)
            )
            reversible = (
                encoded.finish_status is FinishStatus.COMPLETED
                and decoded.text == sample.text
            )
        except TokenizerContractError:
            decode_succeeded = False
        measurements.append(
            ReferenceSampleMetrics(
                sample_id=sample.sample_id,
                domain=sample.domain,
                content_sha256=sample.content_sha256,
                tokenizer_fingerprint=encoded.tokenizer_fingerprint,
                utf8_byte_count=len(encoded_text),
                unicode_scalar_count=len(sample.text),
                token_count=len(encoded.token_ids),
                finish_status=encoded.finish_status,
                decode_succeeded=decode_succeeded,
                reversible=reversible,
            )
        )
    return tuple(measurements)
