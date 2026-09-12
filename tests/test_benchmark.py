"""Controlled P6.4 benchmark and algorithm recommendation tests."""

from dataclasses import replace

import pytest
from benchmarks.p6_4_corpus import CONSTRUCTION_MANIFEST, EVALUATION_MANIFEST
from scripts.run_p6_4_benchmark import render_report

from cybersecgpt.tokenizer import (
    BPE_ALGORITHM_ID,
    UNIGRAM_ALGORITHM_ID,
    CandidateBenchmarkEvidence,
    CandidateEvaluationReport,
    DomainAggregate,
    EvaluationDomain,
    EvaluationManifest,
    TokenizerContractError,
    run_algorithm_benchmark,
    select_algorithm,
)
from cybersecgpt.tokenizer.benchmark import _aggregate, _with_domain_wins

SOURCE_REVISION = "p6.4-gate-dd063926"


def _evidence(
    algorithm_id: str,
    *,
    eligible: bool = True,
    domain_wins: int = 0,
    total_tokens: int = 10,
) -> CandidateBenchmarkEvidence:
    return CandidateBenchmarkEvidence(
        algorithm_id=algorithm_id,
        tokenizer_fingerprint="a" * 64,
        vocabulary_size=512,
        construction_finish_status="vocabulary_limit",
        construction_repeated=True,
        evaluation_repeated=True,
        eligible=eligible,
        total_token_count=total_tokens,
        domain_wins=domain_wins,
        domains=(),
        samples=(),
    )


def test_controlled_benchmark_is_reproducible_complete_and_content_minimizing() -> None:
    first = run_algorithm_benchmark(
        CONSTRUCTION_MANIFEST,
        EVALUATION_MANIFEST,
        source_revision=SOURCE_REVISION,
    )
    second = run_algorithm_benchmark(
        CONSTRUCTION_MANIFEST,
        EVALUATION_MANIFEST,
        source_revision=SOURCE_REVISION,
    )

    assert first == second
    assert first.report_fingerprint == second.report_fingerprint
    assert first.construction_manifest_id != first.evaluation_manifest_id
    assert len(first.construction_sample_digests) == len(CONSTRUCTION_MANIFEST.samples)
    assert len(first.evaluation_sample_digests) == len(EVALUATION_MANIFEST.samples)
    assert first.recommendation == BPE_ALGORITHM_ID
    assert first.recommendation_reason == "more_domain_wins"
    assert first.tie_break_used is False
    assert [candidate.eligible for candidate in first.candidates] == [False, True, True]
    assert all(candidate.evaluation_repeated for candidate in first.candidates)
    assert all(candidate.construction_repeated for candidate in first.candidates)
    assert all(
        {aggregate.domain for aggregate in candidate.domains} == set(EvaluationDomain)
        for candidate in first.candidates
    )
    assert all(
        not hasattr(metric, "text")
        for candidate in first.candidates
        for metric in candidate.samples
    )


def test_report_fingerprint_changes_with_bound_source_revision() -> None:
    first = run_algorithm_benchmark(
        CONSTRUCTION_MANIFEST,
        EVALUATION_MANIFEST,
        source_revision=SOURCE_REVISION,
    )
    changed = run_algorithm_benchmark(
        CONSTRUCTION_MANIFEST,
        EVALUATION_MANIFEST,
        source_revision="p6.4-gate-different",
    )

    assert first.report_fingerprint != changed.report_fingerprint


def test_recommendation_is_fail_closed_for_bindings_and_eligibility() -> None:
    bpe = _evidence(BPE_ALGORITHM_ID, eligible=False)
    unigram = _evidence(UNIGRAM_ALGORITHM_ID, eligible=False)
    assert select_algorithm(bpe, unigram) == (
        None,
        "no_eligible_learned_candidate",
        False,
    )
    assert select_algorithm(replace(bpe, algorithm_id="unexpected"), unigram) == (
        None,
        "candidate_binding_mismatch",
        False,
    )
    assert select_algorithm(replace(bpe, eligible=True), unigram) == (
        BPE_ALGORITHM_ID,
        "only_eligible_learned_candidate",
        False,
    )


def test_recommendation_order_is_domain_then_total_then_algorithm_id() -> None:
    bpe = _evidence(BPE_ALGORITHM_ID, domain_wins=5, total_tokens=20)
    unigram = _evidence(UNIGRAM_ALGORITHM_ID, domain_wins=4, total_tokens=10)
    assert select_algorithm(bpe, unigram) == (
        BPE_ALGORITHM_ID,
        "more_domain_wins",
        False,
    )
    bpe = replace(bpe, domain_wins=4)
    assert select_algorithm(bpe, unigram) == (
        UNIGRAM_ALGORITHM_ID,
        "lower_total_token_count",
        False,
    )
    bpe = replace(bpe, total_token_count=10)
    assert select_algorithm(bpe, unigram) == (
        BPE_ALGORITHM_ID,
        "algorithm_id_tie_break",
        True,
    )


def test_missing_domains_make_both_learned_candidates_ineligible() -> None:
    bpe = replace(
        _evidence(BPE_ALGORITHM_ID),
        domains=(DomainAggregate(EvaluationDomain.CODE, 2, 2, 1, None),),
    )
    unigram = replace(
        _evidence(UNIGRAM_ALGORITHM_ID),
        domains=(DomainAggregate(EvaluationDomain.LOGS, 2, 2, 1, None),),
    )

    checked_bpe, checked_unigram = _with_domain_wins(bpe, unigram)

    assert checked_bpe.eligible is False
    assert checked_unigram.eligible is False


def test_domain_aggregation_omits_domains_without_samples() -> None:
    empty = CandidateEvaluationReport(
        manifest_id="empty",
        manifest_version="1",
        algorithm_id=BPE_ALGORITHM_ID,
        tokenizer_fingerprint="a" * 64,
        max_tokens=1,
        samples=(),
    )

    assert _aggregate(empty) == ()


def test_benchmark_rejects_non_separated_or_incomplete_manifests() -> None:
    with pytest.raises(TokenizerContractError, match="IDs must be distinct"):
        run_algorithm_benchmark(
            CONSTRUCTION_MANIFEST,
            replace(
                EVALUATION_MANIFEST,
                manifest_id=CONSTRUCTION_MANIFEST.manifest_id,
            ),
            source_revision=SOURCE_REVISION,
        )
    with pytest.raises(TokenizerContractError, match="contents must be disjoint"):
        run_algorithm_benchmark(
            CONSTRUCTION_MANIFEST,
            EvaluationManifest(
                "overlap",
                "1",
                (
                    CONSTRUCTION_MANIFEST.samples[0],
                    *EVALUATION_MANIFEST.samples,
                ),
            ),
            source_revision=SOURCE_REVISION,
        )
    with pytest.raises(TokenizerContractError, match="cover every domain"):
        run_algorithm_benchmark(
            CONSTRUCTION_MANIFEST,
            EvaluationManifest("incomplete", "1", EVALUATION_MANIFEST.samples[:1]),
            source_revision=SOURCE_REVISION,
        )


def test_rendered_evidence_is_stable_and_excludes_raw_samples() -> None:
    report = run_algorithm_benchmark(
        CONSTRUCTION_MANIFEST,
        EVALUATION_MANIFEST,
        source_revision=SOURCE_REVISION,
    )
    rendered = render_report(report)

    assert rendered == render_report(report)
    assert f"report_fingerprint={report.report_fingerprint}" in rendered
    assert "recommendation=experimental-byte-bpe-v1" in rendered
    assert EVALUATION_MANIFEST.samples[0].text not in rendered
