"""Deterministic controlled comparison of experimental tokenizer candidates."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import Final

from cybersecgpt.tokenizer.byte_bpe import (
    ByteBpeTrainingConfig,
    train_byte_bpe_candidate,
)
from cybersecgpt.tokenizer.contracts import (
    MAX_TOKEN_COUNT,
    FinishStatus,
    TokenizerContractError,
)
from cybersecgpt.tokenizer.evaluation import (
    CandidateEvaluationReport,
    CandidateSampleMetrics,
    EvaluationDomain,
    EvaluationManifest,
    ExactRatio,
    evaluate_candidate,
)
from cybersecgpt.tokenizer.reference import Utf8ByteReferenceTokenizer
from cybersecgpt.tokenizer.unigram import (
    MAX_UNIGRAM_DISTINCT_SUBSTRINGS,
    MAX_UNIGRAM_PIECE_BYTES,
    MAX_UNIGRAM_SEED_PIECES,
    ByteUnigramTrainingConfig,
    train_byte_unigram_candidate,
)

BENCHMARK_SCHEMA_VERSION: Final = "p6.4-benchmark-report-v1"
BENCHMARK_POLICY_ID: Final = "p6.4-controlled-bpe-unigram-v1"
BENCHMARK_VOCABULARY_LIMIT: Final = 512
BENCHMARK_BPE_MERGE_BUDGET: Final = 256
BENCHMARK_MAX_TRAINING_BYTES: Final = 1024 * 1024
BYTE_REFERENCE_ALGORITHM_ID: Final = "utf8-byte-reference-v1"
BPE_ALGORITHM_ID: Final = "experimental-byte-bpe-v1"
UNIGRAM_ALGORITHM_ID: Final = "experimental-byte-frequency-unigram-v1"


@dataclass(frozen=True, slots=True)
class DomainAggregate:
    """Exact content-minimizing totals for one candidate and domain."""

    domain: EvaluationDomain
    utf8_byte_count: int
    unicode_scalar_count: int
    token_count: int
    tokens_per_utf8_byte: ExactRatio | None


@dataclass(frozen=True, slots=True)
class CandidateBenchmarkEvidence:
    """Replay and structural evidence for one benchmark candidate."""

    algorithm_id: str
    tokenizer_fingerprint: str
    vocabulary_size: int
    construction_finish_status: str
    construction_repeated: bool
    evaluation_repeated: bool
    eligible: bool
    total_token_count: int
    domain_wins: int
    domains: tuple[DomainAggregate, ...]
    samples: tuple[CandidateSampleMetrics, ...]


@dataclass(frozen=True, slots=True)
class AlgorithmBenchmarkReport:
    """Immutable deterministic BPE-versus-Unigram recommendation evidence."""

    schema_version: str
    policy_id: str
    construction_manifest_id: str
    construction_manifest_version: str
    construction_sample_digests: tuple[str, ...]
    evaluation_manifest_id: str
    evaluation_manifest_version: str
    evaluation_sample_digests: tuple[str, ...]
    vocabulary_limit: int
    bpe_merge_budget: int
    max_training_bytes: int
    max_unigram_piece_bytes: int
    max_unigram_distinct_substrings: int
    max_unigram_seed_pieces: int
    max_tokens: int
    source_revision: str
    candidates: tuple[CandidateBenchmarkEvidence, ...]
    recommendation: str | None
    recommendation_reason: str
    tie_break_used: bool
    report_fingerprint: str


def _aggregate(report: CandidateEvaluationReport) -> tuple[DomainAggregate, ...]:
    aggregates: list[DomainAggregate] = []
    for domain in EvaluationDomain:
        metrics = tuple(item for item in report.samples if item.domain is domain)
        if not metrics:
            continue
        byte_count = sum(item.utf8_byte_count for item in metrics)
        scalar_count = sum(item.unicode_scalar_count for item in metrics)
        token_count = sum(item.candidate_token_count for item in metrics)
        aggregates.append(
            DomainAggregate(
                domain=domain,
                utf8_byte_count=byte_count,
                unicode_scalar_count=scalar_count,
                token_count=token_count,
                tokens_per_utf8_byte=ExactRatio.from_counts(token_count, byte_count),
            )
        )
    return tuple(aggregates)


def _eligible(report: CandidateEvaluationReport) -> bool:
    return all(
        metric.finish_status is FinishStatus.COMPLETED
        and metric.decode_succeeded
        and metric.reversible
        and metric.tokenizer_fingerprint == report.tokenizer_fingerprint
        for metric in report.samples
    )


def _evidence(
    first: CandidateEvaluationReport,
    second: CandidateEvaluationReport,
    *,
    vocabulary_size: int,
    construction_finish_status: str,
    construction_repeated: bool,
) -> CandidateBenchmarkEvidence:
    evaluation_repeated = first == second
    domains = _aggregate(first)
    return CandidateBenchmarkEvidence(
        algorithm_id=first.algorithm_id,
        tokenizer_fingerprint=first.tokenizer_fingerprint,
        vocabulary_size=vocabulary_size,
        construction_finish_status=construction_finish_status,
        construction_repeated=construction_repeated,
        evaluation_repeated=evaluation_repeated,
        eligible=construction_repeated and evaluation_repeated and _eligible(first),
        total_token_count=sum(item.candidate_token_count for item in first.samples),
        domain_wins=0,
        domains=domains,
        samples=first.samples,
    )


def _with_domain_wins(
    left: CandidateBenchmarkEvidence, right: CandidateBenchmarkEvidence
) -> tuple[CandidateBenchmarkEvidence, CandidateBenchmarkEvidence]:
    left_counts = {item.domain: item.token_count for item in left.domains}
    right_counts = {item.domain: item.token_count for item in right.domains}
    if left_counts.keys() != right_counts.keys():
        return replace(left, eligible=False), replace(right, eligible=False)
    left_wins = sum(
        left_counts[domain] < right_counts[domain] for domain in left_counts
    )
    right_wins = sum(
        right_counts[domain] < left_counts[domain] for domain in left_counts
    )
    return replace(left, domain_wins=left_wins), replace(right, domain_wins=right_wins)


def select_algorithm(
    bpe: CandidateBenchmarkEvidence,
    unigram: CandidateBenchmarkEvidence,
) -> tuple[str | None, str, bool]:
    """Apply the accepted fail-closed learned-candidate recommendation rule."""

    if {bpe.algorithm_id, unigram.algorithm_id} != {
        BPE_ALGORITHM_ID,
        UNIGRAM_ALGORITHM_ID,
    }:
        return None, "candidate_binding_mismatch", False
    eligible = tuple(item for item in (bpe, unigram) if item.eligible)
    if not eligible:
        return None, "no_eligible_learned_candidate", False
    if len(eligible) == 1:
        return eligible[0].algorithm_id, "only_eligible_learned_candidate", False
    if bpe.domain_wins != unigram.domain_wins:
        winner = max((bpe, unigram), key=lambda item: item.domain_wins)
        return winner.algorithm_id, "more_domain_wins", False
    if bpe.total_token_count != unigram.total_token_count:
        winner = min((bpe, unigram), key=lambda item: item.total_token_count)
        return winner.algorithm_id, "lower_total_token_count", False
    winner = min((bpe, unigram), key=lambda item: item.algorithm_id.encode("utf-8"))
    return winner.algorithm_id, "algorithm_id_tie_break", True


def _validate_manifests(
    construction: EvaluationManifest, evaluation: EvaluationManifest
) -> None:
    if construction.manifest_id == evaluation.manifest_id:
        raise TokenizerContractError("benchmark manifest IDs must be distinct")
    construction_digests = {sample.content_sha256 for sample in construction.samples}
    evaluation_digests = {sample.content_sha256 for sample in evaluation.samples}
    if construction_digests & evaluation_digests:
        raise TokenizerContractError("benchmark manifest contents must be disjoint")
    covered_domains = {sample.domain for sample in evaluation.samples}
    if covered_domains != set(EvaluationDomain):
        raise TokenizerContractError("evaluation manifest must cover every domain")


def _add_field(buffer: bytearray, value: object) -> None:
    encoded = str(value).encode("utf-8")
    buffer.extend(str(len(encoded)).encode("ascii"))
    buffer.extend(b":")
    buffer.extend(encoded)


def _report_fingerprint(report: AlgorithmBenchmarkReport) -> str:
    canonical = bytearray()
    scalar_fields = (
        report.schema_version,
        report.policy_id,
        report.construction_manifest_id,
        report.construction_manifest_version,
        report.evaluation_manifest_id,
        report.evaluation_manifest_version,
        report.vocabulary_limit,
        report.bpe_merge_budget,
        report.max_training_bytes,
        report.max_unigram_piece_bytes,
        report.max_unigram_distinct_substrings,
        report.max_unigram_seed_pieces,
        report.max_tokens,
        report.source_revision,
        report.recommendation or "",
        report.recommendation_reason,
        int(report.tie_break_used),
        len(report.construction_sample_digests),
        len(report.evaluation_sample_digests),
        len(report.candidates),
    )
    for value in scalar_fields:
        _add_field(canonical, value)
    for value in (
        *report.construction_sample_digests,
        *report.evaluation_sample_digests,
    ):
        _add_field(canonical, value)
    for candidate in report.candidates:
        for value in (
            candidate.algorithm_id,
            candidate.tokenizer_fingerprint,
            candidate.vocabulary_size,
            candidate.construction_finish_status,
            int(candidate.construction_repeated),
            int(candidate.evaluation_repeated),
            int(candidate.eligible),
            candidate.total_token_count,
            candidate.domain_wins,
            len(candidate.domains),
            len(candidate.samples),
        ):
            _add_field(canonical, value)
        for domain in candidate.domains:
            for value in (
                domain.domain.value,
                domain.utf8_byte_count,
                domain.unicode_scalar_count,
                domain.token_count,
                (
                    domain.tokens_per_utf8_byte.numerator
                    if domain.tokens_per_utf8_byte
                    else ""
                ),
                (
                    domain.tokens_per_utf8_byte.denominator
                    if domain.tokens_per_utf8_byte
                    else ""
                ),
            ):
                _add_field(canonical, value)
        for sample in candidate.samples:
            for value in (
                sample.sample_id,
                sample.domain.value,
                sample.content_sha256,
                sample.tokenizer_fingerprint,
                sample.utf8_byte_count,
                sample.unicode_scalar_count,
                sample.byte_reference_token_count,
                sample.candidate_token_count,
                (
                    sample.tokens_per_utf8_byte.numerator
                    if sample.tokens_per_utf8_byte
                    else ""
                ),
                (
                    sample.tokens_per_utf8_byte.denominator
                    if sample.tokens_per_utf8_byte
                    else ""
                ),
                (
                    sample.tokens_per_unicode_scalar.numerator
                    if sample.tokens_per_unicode_scalar
                    else ""
                ),
                (
                    sample.tokens_per_unicode_scalar.denominator
                    if sample.tokens_per_unicode_scalar
                    else ""
                ),
                (
                    sample.compression_ratio_to_byte_reference.numerator
                    if sample.compression_ratio_to_byte_reference
                    else ""
                ),
                (
                    sample.compression_ratio_to_byte_reference.denominator
                    if sample.compression_ratio_to_byte_reference
                    else ""
                ),
                sample.finish_status.value,
                int(sample.decode_succeeded),
                int(sample.reversible),
            ):
                _add_field(canonical, value)
    return sha256(canonical).hexdigest()


def run_algorithm_benchmark(
    construction_manifest: EvaluationManifest,
    evaluation_manifest: EvaluationManifest,
    *,
    source_revision: str,
) -> AlgorithmBenchmarkReport:
    """Build twice, evaluate twice, and return deterministic recommendation evidence."""

    _validate_manifests(construction_manifest, evaluation_manifest)

    bpe_config = ByteBpeTrainingConfig(
        BENCHMARK_VOCABULARY_LIMIT,
        merge_budget=BENCHMARK_BPE_MERGE_BUDGET,
        max_training_bytes=BENCHMARK_MAX_TRAINING_BYTES,
        source_revision=source_revision,
    )
    unigram_config = ByteUnigramTrainingConfig(
        BENCHMARK_VOCABULARY_LIMIT,
        max_training_bytes=BENCHMARK_MAX_TRAINING_BYTES,
        source_revision=source_revision,
    )
    bpe_first = train_byte_bpe_candidate(construction_manifest, bpe_config)
    bpe_second = train_byte_bpe_candidate(construction_manifest, bpe_config)
    unigram_first = train_byte_unigram_candidate(construction_manifest, unigram_config)
    unigram_second = train_byte_unigram_candidate(construction_manifest, unigram_config)

    reference = Utf8ByteReferenceTokenizer()
    reference_report = evaluate_candidate(evaluation_manifest, reference)
    reference_evidence = _evidence(
        reference_report,
        evaluate_candidate(evaluation_manifest, reference),
        vocabulary_size=reference.descriptor.vocabulary_size,
        construction_finish_status="not_applicable",
        construction_repeated=True,
    )
    reference_evidence = replace(reference_evidence, eligible=False)
    bpe_report = evaluate_candidate(evaluation_manifest, bpe_first.candidate)
    bpe_evidence = _evidence(
        bpe_report,
        evaluate_candidate(evaluation_manifest, bpe_first.candidate),
        vocabulary_size=bpe_first.candidate.descriptor.vocabulary_size,
        construction_finish_status=bpe_first.finish_status.value,
        construction_repeated=bpe_first == bpe_second,
    )
    unigram_report = evaluate_candidate(evaluation_manifest, unigram_first.candidate)
    unigram_evidence = _evidence(
        unigram_report,
        evaluate_candidate(evaluation_manifest, unigram_first.candidate),
        vocabulary_size=unigram_first.candidate.descriptor.vocabulary_size,
        construction_finish_status=unigram_first.finish_status.value,
        construction_repeated=unigram_first == unigram_second,
    )
    bpe_evidence, unigram_evidence = _with_domain_wins(bpe_evidence, unigram_evidence)
    recommendation, reason, tie = select_algorithm(bpe_evidence, unigram_evidence)
    report = AlgorithmBenchmarkReport(
        schema_version=BENCHMARK_SCHEMA_VERSION,
        policy_id=BENCHMARK_POLICY_ID,
        construction_manifest_id=construction_manifest.manifest_id,
        construction_manifest_version=construction_manifest.version,
        construction_sample_digests=tuple(
            sample.content_sha256 for sample in construction_manifest.samples
        ),
        evaluation_manifest_id=evaluation_manifest.manifest_id,
        evaluation_manifest_version=evaluation_manifest.version,
        evaluation_sample_digests=tuple(
            sample.content_sha256 for sample in evaluation_manifest.samples
        ),
        vocabulary_limit=BENCHMARK_VOCABULARY_LIMIT,
        bpe_merge_budget=BENCHMARK_BPE_MERGE_BUDGET,
        max_training_bytes=BENCHMARK_MAX_TRAINING_BYTES,
        max_unigram_piece_bytes=MAX_UNIGRAM_PIECE_BYTES,
        max_unigram_distinct_substrings=MAX_UNIGRAM_DISTINCT_SUBSTRINGS,
        max_unigram_seed_pieces=MAX_UNIGRAM_SEED_PIECES,
        max_tokens=MAX_TOKEN_COUNT,
        source_revision=source_revision,
        candidates=(reference_evidence, bpe_evidence, unigram_evidence),
        recommendation=recommendation,
        recommendation_reason=reason,
        tie_break_used=tie,
        report_fingerprint="",
    )
    return replace(report, report_fingerprint=_report_fingerprint(report))
