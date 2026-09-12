"""Emit the deterministic, content-minimizing P6.4 benchmark evidence."""

from benchmarks.p6_4_corpus import CONSTRUCTION_MANIFEST, EVALUATION_MANIFEST

from cybersecgpt.tokenizer import (
    AlgorithmBenchmarkReport,
    ExactRatio,
    run_algorithm_benchmark,
)

SOURCE_REVISION = "p6.4-gate-dd063926"


def _ratio(value: ExactRatio | None) -> str:
    if value is None:
        return "none"
    return f"{value.numerator}/{value.denominator}"


def render_report(report: AlgorithmBenchmarkReport) -> str:
    """Render stable evidence without including fixture text or host observations."""

    lines = [
        f"schema_version={report.schema_version}",
        f"policy_id={report.policy_id}",
        f"source_revision={report.source_revision}",
        f"construction_manifest={report.construction_manifest_id}@{report.construction_manifest_version}",
        "construction_digests=" + ",".join(report.construction_sample_digests),
        f"evaluation_manifest={report.evaluation_manifest_id}@{report.evaluation_manifest_version}",
        "evaluation_digests=" + ",".join(report.evaluation_sample_digests),
        f"vocabulary_limit={report.vocabulary_limit}",
        f"bpe_merge_budget={report.bpe_merge_budget}",
        f"max_training_bytes={report.max_training_bytes}",
        f"max_unigram_piece_bytes={report.max_unigram_piece_bytes}",
        f"max_unigram_distinct_substrings={report.max_unigram_distinct_substrings}",
        f"max_unigram_seed_pieces={report.max_unigram_seed_pieces}",
        f"max_tokens={report.max_tokens}",
    ]
    for candidate in report.candidates:
        prefix = f"candidate[{candidate.algorithm_id}]"
        lines.extend(
            (
                f"{prefix}.fingerprint={candidate.tokenizer_fingerprint}",
                f"{prefix}.vocabulary_size={candidate.vocabulary_size}",
                f"{prefix}.construction_finish={candidate.construction_finish_status}",
                f"{prefix}.construction_repeated={str(candidate.construction_repeated).lower()}",
                f"{prefix}.evaluation_repeated={str(candidate.evaluation_repeated).lower()}",
                f"{prefix}.eligible={str(candidate.eligible).lower()}",
                f"{prefix}.total_tokens={candidate.total_token_count}",
                f"{prefix}.domain_wins={candidate.domain_wins}",
            )
        )
        for domain in candidate.domains:
            lines.append(
                f"{prefix}.domain[{domain.domain.value}]="
                f"bytes:{domain.utf8_byte_count},scalars:{domain.unicode_scalar_count},"
                f"tokens:{domain.token_count},ratio:{_ratio(domain.tokens_per_utf8_byte)}"
            )
    lines.extend(
        (
            f"recommendation={report.recommendation or 'none'}",
            f"recommendation_reason={report.recommendation_reason}",
            f"tie_break_used={str(report.tie_break_used).lower()}",
            f"report_fingerprint={report.report_fingerprint}",
        )
    )
    return "\n".join(lines)


def main() -> None:
    report = run_algorithm_benchmark(
        CONSTRUCTION_MANIFEST,
        EVALUATION_MANIFEST,
        source_revision=SOURCE_REVISION,
    )
    print(render_report(report))


if __name__ == "__main__":
    main()
