"""Replay the exact accepted snapshot through the P6.11 training run offline."""

from __future__ import annotations

import json
import socket
from dataclasses import asdict
from importlib import import_module
from typing import NoReturn

from benchmarks.p6_4_corpus import EVALUATION_MANIFEST

from cybersecgpt.tokenizer import (
    MAX_BPE_TRAINING_DEADLINE_NS,
    V1_TRAINING_PROFILE_ID,
    CorpusAdmissionManifest,
    CorpusSampleContent,
    CorpusSampleRecord,
    CorpusSourceRecord,
    CorpusTransformation,
    EvaluationDomain,
    RightsDecision,
    SafetyDecision,
    TokenizerV1TrainingCoordinator,
    V1TrainingRunRequest,
)

TOKENIZER_IMPLEMENTATION_REVISION = "1b1519233b54f55326709b198ad7e95e9834219f"
DATASET_SNAPSHOT_REVISION = "a8573904fd944e9be26e911d768e7335e4bdf1e0"
DATASET_IMPLEMENTATION_REVISION = "cfda1cea94e0501a2b9c67491d47e04294ce35d8"
EXPECTED_CANDIDATE_FINGERPRINT = (
    "072d8850d68f5c16b152c87d15eb01bd2e86100a6012be9fea05fbfa36410e5d"
)
EXPECTED_BEHAVIOR_FINGERPRINT = (
    "ef23540517cb696d57f722c43663e8bc52dac9d9a5e2f7ff9d72ab6e8d0bd347"
)
EXPECTED_ORDERED_SAMPLE_DIGESTS_SHA256 = (
    "ec76753c7d3c4353f8b91d56f34373704fd49b78f22af15f3192a74d0c92fae6"
)
EXPECTED_EVALUATION_SHA256 = (
    "4833fb4b840297a553127630d9555cfcc8653db501b844735d40a8900e320172"
)
EXPECTED_CONFORMANCE_SHA256 = (
    "0d30e646dfc9c1d658b0931b50dd0a5e1616a800a997108cdfe822dcd0732581"
)
EXPECTED_EVIDENCE_SHA256 = (
    "279d62e1c7617ed8d873509cfc8947ef8ae816827495166335d187a61ec00ab0"
)
_ERROR = "P6.11 training-run verification failed"


class TrainingRunVerificationError(RuntimeError):
    """Content-minimized exact-evidence verification failure."""


def _require(condition: bool) -> None:
    if not condition:
        raise TrainingRunVerificationError(_ERROR)


def _blocked_socket(*args: object, **kwargs: object) -> NoReturn:
    raise TrainingRunVerificationError(_ERROR)


def _build_inputs() -> tuple[
    V1TrainingRunRequest,
    CorpusAdmissionManifest,
    tuple[CorpusSampleContent, ...],
]:
    datasets = import_module("cybersecgpt.datasets")
    snapshot = datasets.build_first_party_snapshot()
    projection = datasets.project_tokenizer_admission_manifest(
        snapshot.manifest,
        DATASET_IMPLEMENTATION_REVISION,
    )
    manifest = CorpusAdmissionManifest(
        corpus_id=projection.corpus_id,
        schema_version=projection.schema_version,
        approved_purpose=projection.approved_purpose,
        artifact_distribution_terms=projection.artifact_distribution_terms,
        sources=tuple(
            CorpusSourceRecord(
                source.source_id,
                source.origin_ref,
                source.acquisition_method,
                source.acquired_at,
                source.source_revision,
                source.source_sha256,
                source.license_expression,
                source.obligations_sha256,
                source.reviewer_id,
                source.reviewed_at,
                RightsDecision(source.rights_decision),
                SafetyDecision(source.sensitive_data_decision),
                SafetyDecision(source.contamination_decision),
                source.acquisition_allowed,
                source.processing_allowed,
                source.training_allowed,
                source.derived_statistics_allowed,
                source.artifact_distribution_allowed,
            )
            for source in projection.sources
        ),
        transformations=tuple(
            CorpusTransformation(
                stage.stage_id,
                stage.tool_id,
                stage.configuration_sha256,
            )
            for stage in projection.transformations
        ),
        samples=tuple(
            CorpusSampleRecord(
                sample.sample_id,
                sample.source_id,
                EvaluationDomain(sample.domain),
                sample.byte_count,
                sample.content_sha256,
            )
            for sample in projection.samples
        ),
        exclusion_counts=projection.exclusion_counts,
        manifest_sha256=projection.manifest_sha256,
    )
    fixtures = tuple(
        sorted(
            (
                fixture
                for generator in datasets.first_party_generators(
                    datasets.ACCEPTED_GENERATOR_SOURCE_REVISION
                )
                for fixture in datasets.generate_fixtures(generator)
            ),
            key=lambda item: (item.domain, item.source_id, item.template_id),
        )
    )
    _require(len(fixtures) == len(projection.samples))
    supplied = tuple(
        CorpusSampleContent(sample.sample_id, fixture.content)
        for sample, fixture in zip(projection.samples, fixtures, strict=True)
    )
    _require(manifest.canonical_bytes() == projection.canonical_bytes())
    request = V1TrainingRunRequest(
        training_profile_id=V1_TRAINING_PROFILE_ID,
        corpus_id=projection.corpus_id,
        tokenizer_implementation_revision=TOKENIZER_IMPLEMENTATION_REVISION,
        dataset_snapshot_revision=DATASET_SNAPSHOT_REVISION,
        dataset_implementation_revision=DATASET_IMPLEMENTATION_REVISION,
        dataset_manifest_sha256=snapshot.manifest.manifest_sha256,
        dataset_replay_sha256=snapshot.replay_sha256,
        admission_manifest_sha256=projection.manifest_sha256,
        deadline_ns=MAX_BPE_TRAINING_DEADLINE_NS,
    )
    return request, manifest, supplied


def main() -> None:
    original_socket = socket.socket
    socket.socket = _blocked_socket  # type: ignore[assignment,misc]
    try:
        request, manifest, supplied = _build_inputs()
        first = TokenizerV1TrainingCoordinator(request).run(
            manifest,
            supplied,
            EVALUATION_MANIFEST,
        )
        second = TokenizerV1TrainingCoordinator(request).run(
            manifest,
            supplied,
            EVALUATION_MANIFEST,
        )
    finally:
        socket.socket = original_socket  # type: ignore[misc]

    evidence = first.evidence
    _require(
        first.candidate.tokens == second.candidate.tokens
        and first.candidate.merges == second.candidate.merges
        and first.evidence == second.evidence
        and evidence.tokenizer_implementation_revision
        == TOKENIZER_IMPLEMENTATION_REVISION
        and evidence.dataset_snapshot_revision == DATASET_SNAPSHOT_REVISION
        and evidence.dataset_implementation_revision == DATASET_IMPLEMENTATION_REVISION
        and evidence.ordinary_candidate_fingerprint == EXPECTED_CANDIDATE_FINGERPRINT
        and evidence.behavior_fingerprint == EXPECTED_BEHAVIOR_FINGERPRINT
        and evidence.ordered_sample_digests_sha256
        == EXPECTED_ORDERED_SAMPLE_DIGESTS_SHA256
        and evidence.evaluation_sha256 == EXPECTED_EVALUATION_SHA256
        and evidence.conformance_sha256 == EXPECTED_CONFORMANCE_SHA256
        and evidence.holdout_candidate_token_count == 1_005
        and evidence.holdout_byte_reference_token_count == 1_499
        and not evidence.promotion_authorized
    )
    _require(evidence.evidence_sha256 == EXPECTED_EVIDENCE_SHA256)
    report = asdict(evidence)
    report["network_enabled_during_run"] = False
    report["repeated_construction"] = True
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
