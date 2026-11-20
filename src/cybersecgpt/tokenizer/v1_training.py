"""Deterministic exact-snapshot construction and evaluation for Tokenizer v1."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from enum import StrEnum
from hashlib import sha256
from struct import pack
from threading import Event
from time import monotonic_ns
from typing import Final, NoReturn

from cybersecgpt.tokenizer.byte_bpe import (
    MAX_BPE_TRAINING_DEADLINE_NS,
    BpeTrainingCancelledError,
    BpeTrainingControl,
    BpeTrainingDeadlineError,
    BpeTrainingFinishStatus,
    ByteBpeCandidate,
    ByteBpeTrainingConfig,
    train_byte_bpe_candidate,
)
from cybersecgpt.tokenizer.contracts import FinishStatus, TokenizerContractError
from cybersecgpt.tokenizer.corpus_manifest import (
    CorpusAdmissionManifest,
    CorpusSampleContent,
    admit_corpus,
)
from cybersecgpt.tokenizer.evaluation import (
    EvaluationDomain,
    EvaluationManifest,
    EvaluationSample,
)
from cybersecgpt.tokenizer.v1_semantics import (
    V1_BOS_ID,
    V1_EOS_ID,
    V1_ORDINARY_VOCABULARY_SIZE,
    V1_PAD_ID,
    V1_SEMANTIC_PROFILE,
    TokenizerV1SemanticCandidate,
    TokenizerV1StreamingEncoder,
    V1DecodeRequest,
    V1EncodeRequest,
    V1SpecialDecodeMode,
)

V1_TRAINING_EVIDENCE_SCHEMA_VERSION: Final = "csgpt-tokenizer-v1-training-v1"
V1_TRAINING_PROFILE_ID: Final = "cybersecgpt-tokenizer-v1-byte-bpe-training-1"
V1_TRAINING_GATE_HEAD: Final = "7c7cabf453c856fd460c99e0693afb0da41128a6"
V1_TRAINING_GATE_MERGE: Final = "2e7cad0900ec2b1a065e5688f520e8f7c624bd69"
V1_TRAINING_GATE_ACCEPTANCE_COMMENT_ID: Final = 6_162_346_557
V1_TOKENIZER_BASELINE_REVISION: Final = "0d3b1bff2328392a5b385b0c5b2bd7d08177b792"
V1_DATASET_SNAPSHOT_REVISION: Final = "a8573904fd944e9be26e911d768e7335e4bdf1e0"
V1_DATASET_IMPLEMENTATION_REVISION: Final = "cfda1cea94e0501a2b9c67491d47e04294ce35d8"
V1_CORPUS_ID: Final = "csgpt-tokenizer-v1-first-party-pilot-1"
V1_DATASET_MANIFEST_SHA256: Final = (
    "374773d05a9aae380ad88f477210da75d40adc90cca1afac9ee8800a93656fef"
)
V1_DATASET_REPLAY_SHA256: Final = (
    "002ea5b42cd67d94dcc3e03531c272499963a5a9ffa0171ab01adfdb8a554206"
)
V1_ADMISSION_MANIFEST_SHA256: Final = (
    "a2f676b2717e86717d469b9274b91cb3c3bf48daf58e83efe97221e4d5a7151a"
)
V1_HOLDOUT_MANIFEST_ID: Final = "p6.4-generated-evaluation"
V1_HOLDOUT_MANIFEST_VERSION: Final = "1"
V1_HOLDOUT_MANIFEST_SHA256: Final = (
    "1250db8007142344e51a6c8114ed80032f0d2226f38304097ec1c1345eb72c23"
)
V1_PRIOR_BPE_FINGERPRINT: Final = (
    "fe32ae1b111956debd74643c1273a47c1b4e542514b7b25a570d57b9bdbedd80"
)
V1_PRIOR_BPE_TOKEN_COUNT: Final = 928
V1_TRAINING_SAMPLE_COUNT: Final = 1_024
V1_TRAINING_SOURCE_COUNT: Final = 8
V1_TRAINING_TOTAL_BYTES: Final = 112_467
V1_TRAINING_MAX_BYTES: Final = 1_048_576
V1_TRAINING_MERGE_BUDGET: Final = 256
_DIGEST_LENGTH: Final = 64
_EXPECTED_DOMAIN_COUNTS: Final = tuple((domain, 128) for domain in EvaluationDomain)
_PROJECTION_PROFILE: Final = "csgpt-dataset-tokenizer-admission-projection-v1"
_ERROR: Final = "Tokenizer v1 training run failed"


class V1TrainingRunState(StrEnum):
    """Deterministic coordinator states, including fail-closed terminals."""

    REQUESTED = "requested"
    ADMITTING = "admitting"
    ADMITTED = "admitted"
    CONSTRUCTING = "constructing"
    CONSTRUCTED = "constructed"
    EVALUATING = "evaluating"
    EVIDENCE_READY = "evidence_ready"
    ADMISSION_ERROR = "admission_error"
    CANCELLED = "cancelled"
    DEADLINE_EXCEEDED = "deadline_exceeded"
    RESOURCE_LIMIT = "resource_limit"
    INVALID_UTF8 = "invalid_utf8"
    CONSTRUCTION_ERROR = "construction_error"
    VERIFICATION_ERROR = "verification_error"


_SUCCESS_STATES: Final = (
    V1TrainingRunState.REQUESTED,
    V1TrainingRunState.ADMITTING,
    V1TrainingRunState.ADMITTED,
    V1TrainingRunState.CONSTRUCTING,
    V1TrainingRunState.CONSTRUCTED,
    V1TrainingRunState.EVALUATING,
    V1TrainingRunState.EVIDENCE_READY,
)


class V1TrainingRunError(TokenizerContractError):
    """Content-minimized terminal failure with an explicit lifecycle state."""

    def __init__(self, state: V1TrainingRunState) -> None:
        super().__init__(f"{_ERROR}: {state.value}")
        self.state = state


class _AdmissionFailure(Exception):
    pass


class _ResourceFailure(Exception):
    pass


class _InvalidUtf8Failure(Exception):
    pass


def _digest(value: str, field_name: str) -> None:
    if (
        type(value) is not str
        or len(value) != _DIGEST_LENGTH
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise TokenizerContractError(f"{field_name} must be a lowercase SHA-256")


def _revision(value: str, field_name: str) -> None:
    if (
        type(value) is not str
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise TokenizerContractError(f"{field_name} must be an exact Git revision")


def _identifier(value: str, field_name: str) -> None:
    if (
        type(value) is not str
        or not value
        or len(value.encode("utf-8")) > 256
        or not value.isascii()
        or any(character.isspace() for character in value)
    ):
        raise TokenizerContractError(f"{field_name} must be a bounded ASCII identifier")


def _frame(value: str) -> bytes:
    encoded = value.encode("utf-8", errors="strict")
    return pack("!I", len(encoded)) + encoded


def _integer(value: int) -> bytes:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TokenizerContractError("canonical evidence integer is invalid")
    return pack("!Q", value)


def _boolean(value: bool) -> bytes:
    if type(value) is not bool:
        raise TokenizerContractError("canonical evidence boolean is invalid")
    return bytes((value,))


def _digest_sequence(values: tuple[str, ...], domain: str) -> str:
    digest = sha256(_frame(domain) + _integer(len(values)))
    for value in values:
        _digest(value, "sequence digest")
        digest.update(bytes.fromhex(value))
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class V1TrainingRunRequest:
    """Immutable exact-input request; it carries no authorization."""

    training_profile_id: str
    corpus_id: str
    tokenizer_implementation_revision: str
    dataset_snapshot_revision: str
    dataset_implementation_revision: str
    dataset_manifest_sha256: str
    dataset_replay_sha256: str
    admission_manifest_sha256: str
    deadline_ns: int | None = None

    def __post_init__(self) -> None:
        _identifier(self.training_profile_id, "training_profile_id")
        _identifier(self.corpus_id, "corpus_id")
        for field_name in (
            "tokenizer_implementation_revision",
            "dataset_snapshot_revision",
            "dataset_implementation_revision",
        ):
            _revision(getattr(self, field_name), field_name)
        for field_name in (
            "dataset_manifest_sha256",
            "dataset_replay_sha256",
            "admission_manifest_sha256",
        ):
            _digest(getattr(self, field_name), field_name)
        if self.deadline_ns is not None and (
            isinstance(self.deadline_ns, bool)
            or not isinstance(self.deadline_ns, int)
            or not 0 <= self.deadline_ns <= MAX_BPE_TRAINING_DEADLINE_NS
        ):
            raise TokenizerContractError("deadline_ns is outside the supported range")


class V1TrainingCancellation:
    """Tokenizer-owned cancellation state with no executable callback."""

    __slots__ = ("_event",)

    def __init__(self) -> None:
        self._event = Event()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def cancel(self) -> None:
        """Make cancellation monotonic and visible at the next checkpoint."""

        self._event.set()


@dataclass(frozen=True, slots=True)
class V1TrainingDomainEvidence:
    """Content-minimized deterministic quality outcome for one domain."""

    domain: EvaluationDomain
    sample_count: int
    utf8_byte_count: int
    unicode_scalar_count: int
    candidate_token_count: int
    byte_reference_token_count: int
    reversible: bool
    no_worse_than_byte_reference: bool

    def __post_init__(self) -> None:
        values = (
            self.sample_count,
            self.utf8_byte_count,
            self.unicode_scalar_count,
            self.candidate_token_count,
            self.byte_reference_token_count,
        )
        if not isinstance(self.domain, EvaluationDomain) or any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in values
        ):
            raise TokenizerContractError("domain evidence is invalid")
        if (
            self.byte_reference_token_count != self.utf8_byte_count
            or type(self.reversible) is not bool
            or type(self.no_worse_than_byte_reference) is not bool
            or self.no_worse_than_byte_reference
            != (self.candidate_token_count <= self.byte_reference_token_count)
        ):
            raise TokenizerContractError("domain evidence is inconsistent")


@dataclass(frozen=True, slots=True)
class V1TrainingEvidence:
    """Canonical evidence without corpus text, token bytes, paths, or timing."""

    schema_version: str
    training_profile_id: str
    tokenizer_gate_head: str
    tokenizer_gate_merge: str
    tokenizer_gate_acceptance_comment_id: int
    tokenizer_baseline_revision: str
    tokenizer_implementation_revision: str
    dataset_snapshot_revision: str
    dataset_implementation_revision: str
    corpus_id: str
    dataset_manifest_sha256: str
    dataset_replay_sha256: str
    admission_manifest_sha256: str
    ordered_sample_digests_sha256: str
    source_count: int
    sample_count: int
    total_training_bytes: int
    ordinary_vocabulary_size: int
    merge_count: int
    merge_budget: int
    maximum_training_bytes: int
    construction_finish_status: BpeTrainingFinishStatus
    ordinary_candidate_fingerprint: str
    behavior_fingerprint: str
    semantic_profile: str
    holdout_manifest_id: str
    holdout_manifest_version: str
    holdout_manifest_sha256: str
    holdout_digest_disjoint: bool
    holdout_sample_count: int
    holdout_utf8_byte_count: int
    holdout_unicode_scalar_count: int
    holdout_candidate_token_count: int
    holdout_byte_reference_token_count: int
    prior_bpe_fingerprint: str
    prior_bpe_token_count: int
    domain_evidence: tuple[V1TrainingDomainEvidence, ...]
    streaming_equivalent: bool
    independent_oracle_conformant: bool
    v1_semantics_conformant: bool
    negative_cases_conformant: bool
    evaluation_sha256: str
    conformance_sha256: str
    lifecycle: tuple[V1TrainingRunState, ...]
    promotion_authorized: bool
    evidence_sha256: str = ""

    def __post_init__(self) -> None:
        for field_name in (
            "tokenizer_gate_head",
            "tokenizer_gate_merge",
            "tokenizer_baseline_revision",
            "tokenizer_implementation_revision",
            "dataset_snapshot_revision",
            "dataset_implementation_revision",
        ):
            _revision(getattr(self, field_name), field_name)
        for field_name in (
            "dataset_manifest_sha256",
            "dataset_replay_sha256",
            "admission_manifest_sha256",
            "ordered_sample_digests_sha256",
            "ordinary_candidate_fingerprint",
            "behavior_fingerprint",
            "holdout_manifest_sha256",
            "prior_bpe_fingerprint",
            "evaluation_sha256",
            "conformance_sha256",
        ):
            _digest(getattr(self, field_name), field_name)
        expected_domains = tuple(EvaluationDomain)
        if (
            self.schema_version != V1_TRAINING_EVIDENCE_SCHEMA_VERSION
            or self.training_profile_id != V1_TRAINING_PROFILE_ID
            or self.tokenizer_gate_head != V1_TRAINING_GATE_HEAD
            or self.tokenizer_gate_merge != V1_TRAINING_GATE_MERGE
            or self.tokenizer_gate_acceptance_comment_id
            != V1_TRAINING_GATE_ACCEPTANCE_COMMENT_ID
            or self.tokenizer_baseline_revision != V1_TOKENIZER_BASELINE_REVISION
            or self.semantic_profile != V1_SEMANTIC_PROFILE
            or self.construction_finish_status
            is not BpeTrainingFinishStatus.VOCABULARY_LIMIT
            or tuple(item.domain for item in self.domain_evidence) != expected_domains
            or self.lifecycle != _SUCCESS_STATES
            or not all(
                (
                    self.holdout_digest_disjoint,
                    self.streaming_equivalent,
                    self.independent_oracle_conformant,
                    self.v1_semantics_conformant,
                    self.negative_cases_conformant,
                )
            )
            or self.promotion_authorized
        ):
            raise TokenizerContractError("training evidence is not eligible")
        if self.evidence_sha256:
            _digest(self.evidence_sha256, "evidence_sha256")
            if self.evidence_sha256 != sha256(self.canonical_bytes()).hexdigest():
                raise TokenizerContractError("training evidence digest mismatch")

    def canonical_bytes(self) -> bytes:
        """Return deterministic evidence bytes excluding the self digest."""

        fields: list[bytes] = []
        for text_value in (
            "CSGPT-TOKENIZER-V1-TRAINING-EVIDENCE",
            self.schema_version,
            self.training_profile_id,
            self.tokenizer_gate_head,
            self.tokenizer_gate_merge,
        ):
            fields.append(_frame(text_value))
        fields.append(_integer(self.tokenizer_gate_acceptance_comment_id))
        for text_value in (
            self.tokenizer_baseline_revision,
            self.tokenizer_implementation_revision,
            self.dataset_snapshot_revision,
            self.dataset_implementation_revision,
            self.corpus_id,
            self.dataset_manifest_sha256,
            self.dataset_replay_sha256,
            self.admission_manifest_sha256,
            self.ordered_sample_digests_sha256,
        ):
            fields.append(_frame(text_value))
        for integer_value in (
            self.source_count,
            self.sample_count,
            self.total_training_bytes,
            self.ordinary_vocabulary_size,
            self.merge_count,
            self.merge_budget,
            self.maximum_training_bytes,
        ):
            fields.append(_integer(integer_value))
        for text_value in (
            self.construction_finish_status.value,
            self.ordinary_candidate_fingerprint,
            self.behavior_fingerprint,
            self.semantic_profile,
            self.holdout_manifest_id,
            self.holdout_manifest_version,
            self.holdout_manifest_sha256,
        ):
            fields.append(_frame(text_value))
        fields.append(_boolean(self.holdout_digest_disjoint))
        for integer_value in (
            self.holdout_sample_count,
            self.holdout_utf8_byte_count,
            self.holdout_unicode_scalar_count,
            self.holdout_candidate_token_count,
            self.holdout_byte_reference_token_count,
        ):
            fields.append(_integer(integer_value))
        fields.extend(
            (
                _frame(self.prior_bpe_fingerprint),
                _integer(self.prior_bpe_token_count),
                _integer(len(self.domain_evidence)),
            )
        )
        for item in self.domain_evidence:
            fields.append(_frame(item.domain.value))
            for integer_value in (
                item.sample_count,
                item.utf8_byte_count,
                item.unicode_scalar_count,
                item.candidate_token_count,
                item.byte_reference_token_count,
            ):
                fields.append(_integer(integer_value))
            fields.extend(
                (_boolean(item.reversible), _boolean(item.no_worse_than_byte_reference))
            )
        fields.extend(
            (
                _boolean(self.streaming_equivalent),
                _boolean(self.independent_oracle_conformant),
                _boolean(self.v1_semantics_conformant),
                _boolean(self.negative_cases_conformant),
                _frame(self.evaluation_sha256),
                _frame(self.conformance_sha256),
                _integer(len(self.lifecycle)),
            )
        )
        fields.extend(_frame(state.value) for state in self.lifecycle)
        fields.append(_boolean(self.promotion_authorized))
        return b"".join(fields)

    def with_computed_digest(self) -> V1TrainingEvidence:
        """Seal canonical evidence without adding release authority."""

        if self.evidence_sha256:
            return self
        return replace(self, evidence_sha256=sha256(self.canonical_bytes()).hexdigest())


@dataclass(frozen=True, slots=True)
class V1TrainingRunResult:
    """In-memory candidate and content-minimized evidence only."""

    candidate: ByteBpeCandidate
    tokenizer: TokenizerV1SemanticCandidate
    evidence: V1TrainingEvidence
    lifecycle: tuple[V1TrainingRunState, ...]


@dataclass(frozen=True, slots=True)
class _EvaluationResult:
    domains: tuple[V1TrainingDomainEvidence, ...]
    sample_count: int
    byte_count: int
    scalar_count: int
    token_count: int
    evaluation_sha256: str
    conformance_sha256: str


def holdout_manifest_sha256(manifest: EvaluationManifest) -> str:
    """Bind fixed holdout metadata and content digests without exposing text."""

    if type(manifest) is not EvaluationManifest:
        raise TokenizerContractError("holdout manifest type is invalid")
    fields = [
        _frame("CSGPT-TOKENIZER-V1-HOLDOUT"),
        _frame(manifest.manifest_id),
        _frame(manifest.version),
        _integer(len(manifest.samples)),
    ]
    for sample in manifest.samples:
        fields.extend(
            (
                _frame(sample.sample_id),
                _frame(sample.domain.value),
                _frame(sample.source_ref),
                _frame(sample.license_id),
                _frame(sample.content_sha256),
                _integer(len(sample.text.encode("utf-8"))),
                _integer(len(sample.text)),
            )
        )
    return sha256(b"".join(fields)).hexdigest()


def _oracle_encode(data: bytes, candidate: ByteBpeCandidate) -> tuple[int, ...]:
    pieces = list(data)
    for merge in candidate.merges:
        output: list[int] = []
        index = 0
        pair = (merge.left_id, merge.right_id)
        while index < len(pieces):
            if index + 1 < len(pieces) and (pieces[index], pieces[index + 1]) == pair:
                output.append(merge.token_id)
                index += 2
            else:
                output.append(pieces[index])
                index += 1
        pieces = output
    return tuple(pieces)


class TokenizerV1TrainingCoordinator:
    """Single-use fail-closed coordinator for the accepted P6.11 run."""

    __slots__ = ("_cancellation", "_lifecycle", "_request", "_state")

    def __init__(
        self,
        request: V1TrainingRunRequest,
        cancellation: V1TrainingCancellation | None = None,
    ) -> None:
        if type(request) is not V1TrainingRunRequest:
            raise TokenizerContractError("request type is invalid")
        if (
            cancellation is not None
            and type(cancellation) is not V1TrainingCancellation
        ):
            raise TokenizerContractError("cancellation type is invalid")
        self._request = request
        self._cancellation = cancellation or V1TrainingCancellation()
        self._state = V1TrainingRunState.REQUESTED
        self._lifecycle = [self._state]

    @property
    def state(self) -> V1TrainingRunState:
        return self._state

    @property
    def lifecycle(self) -> tuple[V1TrainingRunState, ...]:
        return tuple(self._lifecycle)

    def cancel(self) -> None:
        """Propagate cancellation without granting any other authority."""

        self._cancellation.cancel()

    def _transition(self, state: V1TrainingRunState) -> None:
        self._state = state
        self._lifecycle.append(state)

    def _terminal(self, state: V1TrainingRunState) -> NoReturn:
        self._transition(state)
        raise V1TrainingRunError(state) from None

    def _checkpoint(self) -> None:
        if self._cancellation.cancelled:
            raise BpeTrainingCancelledError("training cancelled")
        deadline = self._request.deadline_ns
        if deadline is not None and monotonic_ns() >= deadline:
            raise BpeTrainingDeadlineError("training deadline expired")

    def _validate_exact_inputs(
        self,
        manifest: CorpusAdmissionManifest,
        supplied: tuple[CorpusSampleContent, ...],
    ) -> None:
        request = self._request
        if type(manifest) is not CorpusAdmissionManifest or type(supplied) is not tuple:
            raise _AdmissionFailure
        if (
            sum(sample.byte_count for sample in manifest.samples)
            > V1_TRAINING_MAX_BYTES
        ):
            raise _ResourceFailure
        domain_counts = tuple(
            sorted(Counter(item.domain for item in manifest.samples).items())
        )
        final_stage = manifest.transformations[-1]
        if (
            request.training_profile_id != V1_TRAINING_PROFILE_ID
            or request.corpus_id != V1_CORPUS_ID
            or request.dataset_snapshot_revision != V1_DATASET_SNAPSHOT_REVISION
            or request.dataset_implementation_revision
            != V1_DATASET_IMPLEMENTATION_REVISION
            or request.dataset_manifest_sha256 != V1_DATASET_MANIFEST_SHA256
            or request.dataset_replay_sha256 != V1_DATASET_REPLAY_SHA256
            or request.admission_manifest_sha256 != V1_ADMISSION_MANIFEST_SHA256
            or manifest.corpus_id != V1_CORPUS_ID
            or manifest.manifest_sha256 != V1_ADMISSION_MANIFEST_SHA256
            or len(manifest.sources) != V1_TRAINING_SOURCE_COUNT
            or len(manifest.samples) != V1_TRAINING_SAMPLE_COUNT
            or sum(sample.byte_count for sample in manifest.samples)
            != V1_TRAINING_TOTAL_BYTES
            or domain_counts != tuple(sorted(_EXPECTED_DOMAIN_COUNTS))
            or final_stage.stage_id != "admission-projection"
            or final_stage.tool_id
            != f"{_PROJECTION_PROFILE}@{V1_DATASET_IMPLEMENTATION_REVISION}"
            or final_stage.configuration_sha256 != V1_DATASET_MANIFEST_SHA256
        ):
            raise _AdmissionFailure
        try:
            admit_corpus(
                manifest,
                supplied,
                cancelled=self._cancellation.cancelled,
                deadline_ns=request.deadline_ns,
                now_ns=(monotonic_ns() if request.deadline_ns is not None else None),
            )
        except TokenizerContractError:
            raise _AdmissionFailure from None

    def _training_manifest(
        self,
        manifest: CorpusAdmissionManifest,
        supplied: tuple[CorpusSampleContent, ...],
    ) -> EvaluationManifest:
        samples: list[EvaluationSample] = []
        for record, content in zip(manifest.samples, supplied, strict=True):
            self._checkpoint()
            try:
                text = content.content.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                raise _InvalidUtf8Failure from None
            samples.append(
                EvaluationSample.from_text(
                    sample_id=record.sample_id,
                    domain=record.domain,
                    text=text,
                    source_ref=f"admitted:{record.source_id}",
                    license_id="owner-reviewed-first-party",
                )
            )
            self._checkpoint()
        return EvaluationManifest(
            V1_TRAINING_PROFILE_ID,
            manifest.manifest_sha256,
            tuple(samples),
        )

    def _evaluate(
        self,
        tokenizer: TokenizerV1SemanticCandidate,
        training_digests: tuple[str, ...],
        holdout: EvaluationManifest,
    ) -> _EvaluationResult:
        if (
            type(holdout) is not EvaluationManifest
            or holdout.manifest_id != V1_HOLDOUT_MANIFEST_ID
            or holdout.version != V1_HOLDOUT_MANIFEST_VERSION
            or holdout_manifest_sha256(holdout) != V1_HOLDOUT_MANIFEST_SHA256
            or set(training_digests)
            & {sample.content_sha256 for sample in holdout.samples}
            or {sample.domain for sample in holdout.samples} != set(EvaluationDomain)
        ):
            raise TokenizerContractError("holdout verification failed")
        domain_values: dict[EvaluationDomain, list[int]] = {
            domain: [0, 0, 0, 0] for domain in EvaluationDomain
        }
        evaluation = sha256(_frame("CSGPT-TOKENIZER-V1-EVALUATION"))
        conformance = sha256(_frame("CSGPT-TOKENIZER-V1-CONFORMANCE"))
        total_bytes = 0
        total_scalars = 0
        total_tokens = 0
        for sample in holdout.samples:
            self._checkpoint()
            encoded_bytes = sample.text.encode("utf-8")
            oracle = _oracle_encode(encoded_bytes, tokenizer.candidate)
            result = tokenizer.encode(V1EncodeRequest(sample.text, return_offsets=True))
            if (
                result.finish_status is not FinishStatus.COMPLETED
                or result.token_ids != oracle
                or V1_PAD_ID in result.token_ids
                or tokenizer.decode(V1DecodeRequest(result.token_ids)).text
                != sample.text
            ):
                raise TokenizerContractError("candidate evaluation failed")
            stream = TokenizerV1StreamingEncoder(tokenizer, return_offsets=True)
            for value in encoded_bytes:
                stream.push(bytes((value,)))
            if stream.finish() != result:
                raise TokenizerContractError("streaming equivalence failed")
            bounded = tokenizer.encode(
                V1EncodeRequest(sample.text, max_tokens=len(oracle) // 2)
            )
            bounded_text = tokenizer.decode(V1DecodeRequest(bounded.token_ids)).text
            special = tokenizer.encode(
                V1EncodeRequest(sample.text, add_bos=True, add_eos=True)
            )
            preserved = tokenizer.decode(
                V1DecodeRequest(
                    special.token_ids,
                    special_mode=V1SpecialDecodeMode.PRESERVE,
                )
            )
            rendered = tokenizer.decode(
                V1DecodeRequest(
                    special.token_ids,
                    special_mode=V1SpecialDecodeMode.RENDER,
                )
            )
            if (
                bounded.finish_status is not FinishStatus.TRUNCATED
                or bounded_text is None
                or not sample.text.startswith(bounded_text)
                or V1_EOS_ID in bounded.token_ids
                or V1_PAD_ID in bounded.token_ids
                or special.token_ids[0] != V1_BOS_ID
                or special.token_ids[-1] != V1_EOS_ID
                or V1_PAD_ID in special.token_ids
                or preserved.text is not None
                or tuple(segment.value for segment in preserved.segments)[0] != "bos"
                or tuple(segment.value for segment in preserved.segments)[-1] != "eos"
                or rendered.text != f"<|bos|>{sample.text}<|eos|>"
            ):
                raise TokenizerContractError("v1 semantic verification failed")
            values = domain_values[sample.domain]
            values[0] += 1
            values[1] += len(encoded_bytes)
            values[2] += len(sample.text)
            values[3] += len(result.token_ids)
            total_bytes += len(encoded_bytes)
            total_scalars += len(sample.text)
            total_tokens += len(result.token_ids)
            for text_value in (
                sample.sample_id,
                sample.domain.value,
                sample.content_sha256,
                tokenizer.descriptor.fingerprint,
            ):
                evaluation.update(_frame(text_value))
            for integer_value in (
                len(encoded_bytes),
                len(sample.text),
                len(result.token_ids),
            ):
                evaluation.update(_integer(integer_value))
            conformance.update(_frame(sample.sample_id))
            conformance.update(_integer(len(result.token_ids)))
            for token_id in result.token_ids:
                conformance.update(_integer(token_id))
            conformance.update(_integer(len(bounded.token_ids)))
            for token_id in bounded.token_ids:
                conformance.update(_integer(token_id))
            self._checkpoint()
        tokenizer.require_compatible_fingerprint(tokenizer.descriptor.fingerprint)
        negative_count = 0
        try:
            tokenizer.require_compatible_fingerprint("0" * 64)
        except TokenizerContractError:
            negative_count += 1
        try:
            tokenizer.decode(V1DecodeRequest((V1_BOS_ID,)))
        except TokenizerContractError:
            negative_count += 1
        try:
            tokenizer.decode(V1DecodeRequest((0xC3,)))
        except TokenizerContractError:
            negative_count += 1
        try:
            V1DecodeRequest((V1_PAD_ID + 1,))
        except TokenizerContractError:
            negative_count += 1
        if negative_count != 4 or total_tokens >= total_bytes:
            raise TokenizerContractError("negative or quality verification failed")
        conformance.update(_integer(negative_count))
        domains = tuple(
            V1TrainingDomainEvidence(
                domain,
                values[0],
                values[1],
                values[2],
                values[3],
                values[1],
                True,
                values[3] <= values[1],
            )
            for domain, values in domain_values.items()
        )
        if any(
            item.sample_count == 0
            or not item.reversible
            or not item.no_worse_than_byte_reference
            for item in domains
        ):
            raise TokenizerContractError("per-domain quality verification failed")
        return _EvaluationResult(
            domains,
            len(holdout.samples),
            total_bytes,
            total_scalars,
            total_tokens,
            evaluation.hexdigest(),
            conformance.hexdigest(),
        )

    def run(
        self,
        manifest: CorpusAdmissionManifest,
        supplied: tuple[CorpusSampleContent, ...],
        holdout: EvaluationManifest,
    ) -> V1TrainingRunResult:
        """Admit, construct, verify, and return no persistent artifact."""

        if self._state is not V1TrainingRunState.REQUESTED:
            raise TokenizerContractError("training coordinator is single-use")
        try:
            self._transition(V1TrainingRunState.ADMITTING)
            self._checkpoint()
            self._validate_exact_inputs(manifest, supplied)
            self._checkpoint()
            self._transition(V1TrainingRunState.ADMITTED)
            training_manifest = self._training_manifest(manifest, supplied)
            self._transition(V1TrainingRunState.CONSTRUCTING)
            control = BpeTrainingControl(
                self._cancellation._event,
                self._request.deadline_ns,
            )
            trained = train_byte_bpe_candidate(
                training_manifest,
                ByteBpeTrainingConfig(
                    vocabulary_limit=V1_ORDINARY_VOCABULARY_SIZE,
                    merge_budget=V1_TRAINING_MERGE_BUDGET,
                    max_training_bytes=V1_TRAINING_MAX_BYTES,
                    source_revision=self._request.tokenizer_implementation_revision,
                ),
                control=control,
            )
            if (
                trained.finish_status is not BpeTrainingFinishStatus.VOCABULARY_LIMIT
                or len(trained.candidate.tokens) != V1_ORDINARY_VOCABULARY_SIZE
                or len(trained.candidate.merges) != V1_TRAINING_MERGE_BUDGET
            ):
                raise TokenizerContractError("construction outcome is ineligible")
            self._checkpoint()
            self._transition(V1TrainingRunState.CONSTRUCTED)
            tokenizer = TokenizerV1SemanticCandidate(trained.candidate)
            self._transition(V1TrainingRunState.EVALUATING)
            evaluated = self._evaluate(tokenizer, trained.sample_digests, holdout)
            self._checkpoint()
            anticipated_lifecycle = tuple(
                self._lifecycle + [V1TrainingRunState.EVIDENCE_READY]
            )
            evidence = V1TrainingEvidence(
                schema_version=V1_TRAINING_EVIDENCE_SCHEMA_VERSION,
                training_profile_id=V1_TRAINING_PROFILE_ID,
                tokenizer_gate_head=V1_TRAINING_GATE_HEAD,
                tokenizer_gate_merge=V1_TRAINING_GATE_MERGE,
                tokenizer_gate_acceptance_comment_id=V1_TRAINING_GATE_ACCEPTANCE_COMMENT_ID,
                tokenizer_baseline_revision=V1_TOKENIZER_BASELINE_REVISION,
                tokenizer_implementation_revision=self._request.tokenizer_implementation_revision,
                dataset_snapshot_revision=self._request.dataset_snapshot_revision,
                dataset_implementation_revision=self._request.dataset_implementation_revision,
                corpus_id=manifest.corpus_id,
                dataset_manifest_sha256=self._request.dataset_manifest_sha256,
                dataset_replay_sha256=self._request.dataset_replay_sha256,
                admission_manifest_sha256=manifest.manifest_sha256,
                ordered_sample_digests_sha256=_digest_sequence(
                    trained.sample_digests,
                    "CSGPT-TOKENIZER-V1-ORDERED-TRAINING-DIGESTS",
                ),
                source_count=len(manifest.sources),
                sample_count=len(manifest.samples),
                total_training_bytes=sum(
                    sample.byte_count for sample in manifest.samples
                ),
                ordinary_vocabulary_size=len(trained.candidate.tokens),
                merge_count=len(trained.candidate.merges),
                merge_budget=trained.merge_budget,
                maximum_training_bytes=trained.max_training_bytes,
                construction_finish_status=trained.finish_status,
                ordinary_candidate_fingerprint=trained.candidate.descriptor.fingerprint,
                behavior_fingerprint=tokenizer.descriptor.fingerprint,
                semantic_profile=V1_SEMANTIC_PROFILE,
                holdout_manifest_id=holdout.manifest_id,
                holdout_manifest_version=holdout.version,
                holdout_manifest_sha256=holdout_manifest_sha256(holdout),
                holdout_digest_disjoint=True,
                holdout_sample_count=evaluated.sample_count,
                holdout_utf8_byte_count=evaluated.byte_count,
                holdout_unicode_scalar_count=evaluated.scalar_count,
                holdout_candidate_token_count=evaluated.token_count,
                holdout_byte_reference_token_count=evaluated.byte_count,
                prior_bpe_fingerprint=V1_PRIOR_BPE_FINGERPRINT,
                prior_bpe_token_count=V1_PRIOR_BPE_TOKEN_COUNT,
                domain_evidence=evaluated.domains,
                streaming_equivalent=True,
                independent_oracle_conformant=True,
                v1_semantics_conformant=True,
                negative_cases_conformant=True,
                evaluation_sha256=evaluated.evaluation_sha256,
                conformance_sha256=evaluated.conformance_sha256,
                lifecycle=anticipated_lifecycle,
                promotion_authorized=False,
            ).with_computed_digest()
            self._transition(V1TrainingRunState.EVIDENCE_READY)
            return V1TrainingRunResult(
                trained.candidate, tokenizer, evidence, self.lifecycle
            )
        except BpeTrainingCancelledError:
            self._terminal(V1TrainingRunState.CANCELLED)
        except BpeTrainingDeadlineError:
            self._terminal(V1TrainingRunState.DEADLINE_EXCEEDED)
        except _ResourceFailure:
            self._terminal(V1TrainingRunState.RESOURCE_LIMIT)
        except _InvalidUtf8Failure:
            self._terminal(V1TrainingRunState.INVALID_UTF8)
        except _AdmissionFailure:
            self._terminal(V1TrainingRunState.ADMISSION_ERROR)
        except TokenizerContractError:
            terminal = (
                V1TrainingRunState.CONSTRUCTION_ERROR
                if self._lifecycle[-1] is V1TrainingRunState.CONSTRUCTING
                else V1TrainingRunState.VERIFICATION_ERROR
            )
            self._terminal(terminal)
