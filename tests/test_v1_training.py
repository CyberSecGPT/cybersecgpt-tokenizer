"""P6.11 deterministic Tokenizer v1 training-run evidence tests."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from types import SimpleNamespace

import pytest
from benchmarks.p6_4_corpus import CONSTRUCTION_MANIFEST, EVALUATION_MANIFEST

import cybersecgpt.tokenizer.v1_training as training
from cybersecgpt.tokenizer import (
    MAX_BPE_TRAINING_DEADLINE_NS,
    CorpusAdmissionManifest,
    CorpusSampleContent,
    CorpusSampleRecord,
    CorpusSourceRecord,
    CorpusTransformation,
    EvaluationDomain,
    EvaluationManifest,
    RightsDecision,
    SafetyDecision,
    TokenizerContractError,
    TokenizerV1TrainingCoordinator,
    V1TrainingCancellation,
    V1TrainingDomainEvidence,
    V1TrainingRunError,
    V1TrainingRunRequest,
    V1TrainingRunState,
)

_TOKENIZER_REVISION = "c" * 40
_DATASET_SNAPSHOT_REVISION = "a" * 40
_DATASET_IMPLEMENTATION_REVISION = "b" * 40
_DATASET_MANIFEST = "1" * 64
_DATASET_REPLAY = "2" * 64


def _source() -> CorpusSourceRecord:
    return CorpusSourceRecord(
        source_id="source-1",
        origin_ref="repository:test",
        acquisition_method="first-party",
        acquired_at="2026-10-01",
        source_revision="accepted-source",
        source_sha256="3" * 64,
        license_expression="LicenseRef-Test",
        obligations_sha256="4" * 64,
        reviewer_id="project-owner",
        reviewed_at="2026-10-01",
        rights_decision=RightsDecision.APPROVED,
        sensitive_data_decision=SafetyDecision.CLEAN,
        contamination_decision=SafetyDecision.CLEAN,
        acquisition_allowed=True,
        processing_allowed=True,
        training_allowed=True,
        derived_statistics_allowed=True,
        artifact_distribution_allowed=True,
    )


def _manifest_from_evaluation(
    source: EvaluationManifest = CONSTRUCTION_MANIFEST,
) -> tuple[CorpusAdmissionManifest, tuple[CorpusSampleContent, ...]]:
    records = tuple(
        CorpusSampleRecord(
            sample.sample_id,
            "source-1",
            sample.domain,
            len(sample.text.encode("utf-8")),
            sample.content_sha256,
        )
        for sample in source.samples
    )
    supplied = tuple(
        CorpusSampleContent(sample.sample_id, sample.text.encode("utf-8"))
        for sample in source.samples
    )
    manifest = CorpusAdmissionManifest(
        corpus_id="test-corpus",
        schema_version="csgpt-corpus-manifest-v1",
        approved_purpose="controlled-tokenizer-training",
        artifact_distribution_terms="separately-reviewed-artifact-only",
        sources=(_source(),),
        transformations=(
            CorpusTransformation("fixture", "test@1", "5" * 64),
            CorpusTransformation(
                "admission-projection",
                (
                    "csgpt-dataset-tokenizer-admission-projection-v1@"
                    f"{_DATASET_IMPLEMENTATION_REVISION}"
                ),
                _DATASET_MANIFEST,
            ),
        ),
        samples=records,
        exclusion_counts=(),
        manifest_sha256="",
    ).with_computed_digest()
    return manifest, supplied


def _accepted_inputs(
    monkeypatch: pytest.MonkeyPatch,
    *,
    deadline_ns: int | None = MAX_BPE_TRAINING_DEADLINE_NS,
) -> tuple[
    V1TrainingRunRequest,
    CorpusAdmissionManifest,
    tuple[CorpusSampleContent, ...],
    EvaluationManifest,
]:
    manifest, supplied = _manifest_from_evaluation()
    domain_counts = tuple(
        sorted(Counter(sample.domain for sample in manifest.samples).items())
    )
    monkeypatch.setattr(training, "V1_CORPUS_ID", manifest.corpus_id)
    monkeypatch.setattr(
        training, "V1_DATASET_SNAPSHOT_REVISION", _DATASET_SNAPSHOT_REVISION
    )
    monkeypatch.setattr(
        training, "V1_DATASET_IMPLEMENTATION_REVISION", _DATASET_IMPLEMENTATION_REVISION
    )
    monkeypatch.setattr(training, "V1_DATASET_MANIFEST_SHA256", _DATASET_MANIFEST)
    monkeypatch.setattr(training, "V1_DATASET_REPLAY_SHA256", _DATASET_REPLAY)
    monkeypatch.setattr(
        training, "V1_ADMISSION_MANIFEST_SHA256", manifest.manifest_sha256
    )
    monkeypatch.setattr(training, "V1_TRAINING_SOURCE_COUNT", 1)
    monkeypatch.setattr(training, "V1_TRAINING_SAMPLE_COUNT", len(manifest.samples))
    monkeypatch.setattr(
        training,
        "V1_TRAINING_TOTAL_BYTES",
        sum(sample.byte_count for sample in manifest.samples),
    )
    monkeypatch.setattr(training, "_EXPECTED_DOMAIN_COUNTS", domain_counts)
    monkeypatch.setattr(
        training,
        "V1_HOLDOUT_MANIFEST_SHA256",
        training.holdout_manifest_sha256(EVALUATION_MANIFEST),
    )
    request = V1TrainingRunRequest(
        training_profile_id=training.V1_TRAINING_PROFILE_ID,
        corpus_id=manifest.corpus_id,
        tokenizer_implementation_revision=_TOKENIZER_REVISION,
        dataset_snapshot_revision=_DATASET_SNAPSHOT_REVISION,
        dataset_implementation_revision=_DATASET_IMPLEMENTATION_REVISION,
        dataset_manifest_sha256=_DATASET_MANIFEST,
        dataset_replay_sha256=_DATASET_REPLAY,
        admission_manifest_sha256=manifest.manifest_sha256,
        deadline_ns=deadline_ns,
    )
    return request, manifest, supplied, EVALUATION_MANIFEST


def _successful_result(monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    request, manifest, supplied, holdout = _accepted_inputs(monkeypatch)
    return TokenizerV1TrainingCoordinator(request).run(manifest, supplied, holdout)


def test_exact_run_is_repeated_content_minimized_and_non_promoting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request, manifest, supplied, holdout = _accepted_inputs(monkeypatch)
    first_coordinator = TokenizerV1TrainingCoordinator(request)
    first = first_coordinator.run(manifest, supplied, holdout)
    second_request, second_manifest, second_supplied, second_holdout = _accepted_inputs(
        monkeypatch, deadline_ns=None
    )
    second = TokenizerV1TrainingCoordinator(second_request).run(
        second_manifest, second_supplied, second_holdout
    )
    assert first == second
    assert first_coordinator.state is V1TrainingRunState.EVIDENCE_READY
    assert first_coordinator.lifecycle == first.lifecycle
    assert first.evidence.lifecycle == first.lifecycle
    assert first.evidence.holdout_digest_disjoint
    assert first.evidence.holdout_candidate_token_count < 1499
    assert all(item.reversible for item in first.evidence.domain_evidence)
    assert all(
        item.no_worse_than_byte_reference for item in first.evidence.domain_evidence
    )
    assert not first.evidence.promotion_authorized
    assert first.evidence.with_computed_digest() is first.evidence
    assert (
        first.evidence.evidence_sha256
        == training.sha256(first.evidence.canonical_bytes()).hexdigest()
    )
    assert not hasattr(first.evidence, "text")
    assert not hasattr(first.evidence, "tokens")
    assert not hasattr(first.evidence, "path")
    assert first.candidate is first.tokenizer.candidate
    with pytest.raises(TokenizerContractError, match="single-use"):
        first_coordinator.run(manifest, supplied, holdout)


def test_external_cancellation_and_expired_deadline_are_terminal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request, manifest, supplied, holdout = _accepted_inputs(monkeypatch)
    cancellation = V1TrainingCancellation()
    coordinator = TokenizerV1TrainingCoordinator(request, cancellation)
    assert not cancellation.cancelled
    coordinator.cancel()
    assert cancellation.cancelled
    with pytest.raises(V1TrainingRunError) as cancelled:
        coordinator.run(manifest, supplied, holdout)
    assert cancelled.value.state is V1TrainingRunState.CANCELLED
    assert coordinator.state is V1TrainingRunState.CANCELLED
    expired = TokenizerV1TrainingCoordinator(replace(request, deadline_ns=0))
    with pytest.raises(V1TrainingRunError) as deadline:
        expired.run(manifest, supplied, holdout)
    assert deadline.value.state is V1TrainingRunState.DEADLINE_EXCEEDED


def test_admission_resource_utf8_construction_and_verification_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request, manifest, supplied, holdout = _accepted_inputs(monkeypatch)
    with pytest.raises(V1TrainingRunError) as admission:
        TokenizerV1TrainingCoordinator(
            replace(request, corpus_id="different-corpus")
        ).run(manifest, supplied, holdout)
    assert admission.value.state is V1TrainingRunState.ADMISSION_ERROR
    changed = CorpusSampleContent(supplied[0].sample_id, b"x" + supplied[0].content[1:])
    with pytest.raises(V1TrainingRunError) as byte_mismatch:
        TokenizerV1TrainingCoordinator(request).run(
            manifest, (changed,) + supplied[1:], holdout
        )
    assert byte_mismatch.value.state is V1TrainingRunState.ADMISSION_ERROR
    monkeypatch.setattr(
        training,
        "V1_TRAINING_MAX_BYTES",
        sum(sample.byte_count for sample in manifest.samples) - 1,
    )
    with pytest.raises(V1TrainingRunError) as resource:
        TokenizerV1TrainingCoordinator(request).run(manifest, supplied, holdout)
    assert resource.value.state is V1TrainingRunState.RESOURCE_LIMIT
    monkeypatch.setattr(training, "V1_TRAINING_MAX_BYTES", 1_048_576)
    invalid_content = CorpusSampleContent(supplied[0].sample_id, b"\xff")
    invalid_record = replace(
        manifest.samples[0],
        byte_count=1,
        content_sha256=training.sha256(b"\xff").hexdigest(),
    )
    invalid_manifest = replace(
        manifest, samples=(invalid_record,) + manifest.samples[1:], manifest_sha256=""
    ).with_computed_digest()
    invalid_supplied = (invalid_content,) + supplied[1:]
    monkeypatch.setattr(
        training, "V1_ADMISSION_MANIFEST_SHA256", invalid_manifest.manifest_sha256
    )
    monkeypatch.setattr(
        training,
        "V1_TRAINING_TOTAL_BYTES",
        sum(sample.byte_count for sample in invalid_manifest.samples),
    )
    invalid_request = replace(
        request, admission_manifest_sha256=invalid_manifest.manifest_sha256
    )
    with pytest.raises(V1TrainingRunError) as invalid_utf8:
        TokenizerV1TrainingCoordinator(invalid_request).run(
            invalid_manifest, invalid_supplied, holdout
        )
    assert invalid_utf8.value.state is V1TrainingRunState.INVALID_UTF8
    request, manifest, supplied, holdout = _accepted_inputs(monkeypatch)

    def reject_construction(*args: object, **kwargs: object) -> None:
        raise TokenizerContractError("not exposed")

    monkeypatch.setattr(training, "train_byte_bpe_candidate", reject_construction)
    with pytest.raises(V1TrainingRunError) as construction:
        TokenizerV1TrainingCoordinator(request).run(manifest, supplied, holdout)
    assert construction.value.state is V1TrainingRunState.CONSTRUCTION_ERROR
    monkeypatch.undo()
    request, manifest, supplied, holdout = _accepted_inputs(monkeypatch)
    original_train = training.train_byte_bpe_candidate

    def ineligible_construction(*args: object, **kwargs: object):  # type: ignore[no-untyped-def]
        result = original_train(*args, **kwargs)  # type: ignore[arg-type]
        return replace(
            result,
            finish_status=training.BpeTrainingFinishStatus.MERGE_BUDGET,
        )

    monkeypatch.setattr(training, "train_byte_bpe_candidate", ineligible_construction)
    with pytest.raises(V1TrainingRunError) as ineligible:
        TokenizerV1TrainingCoordinator(request).run(manifest, supplied, holdout)
    assert ineligible.value.state is V1TrainingRunState.CONSTRUCTION_ERROR
    monkeypatch.undo()
    request, manifest, supplied, holdout = _accepted_inputs(monkeypatch)
    with pytest.raises(V1TrainingRunError) as verification:
        TokenizerV1TrainingCoordinator(request).run(
            manifest, supplied, replace(holdout, manifest_id="wrong")
        )
    assert verification.value.state is V1TrainingRunState.VERIFICATION_ERROR


def test_evaluation_failure_paths_remain_verification_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request, manifest, supplied, holdout = _accepted_inputs(monkeypatch)
    successful = TokenizerV1TrainingCoordinator(request).run(
        manifest, supplied, holdout
    )
    training_digests = tuple(sample.content_sha256 for sample in manifest.samples)
    original_encode = training.TokenizerV1SemanticCandidate.encode

    def wrong_full(self: object, value: training.V1EncodeRequest):  # type: ignore[no-untyped-def]
        result = original_encode(self, value)  # type: ignore[arg-type]
        return (
            replace(result, finish_status=training.FinishStatus.TRUNCATED)
            if value.return_offsets
            else result
        )

    with monkeypatch.context() as context:
        context.setattr(training.TokenizerV1SemanticCandidate, "encode", wrong_full)
        with pytest.raises(TokenizerContractError, match="candidate evaluation"):
            TokenizerV1TrainingCoordinator(request)._evaluate(
                successful.tokenizer, training_digests, holdout
            )
    with monkeypatch.context() as context:
        context.setattr(
            training.TokenizerV1StreamingEncoder, "finish", lambda self: None
        )
        with pytest.raises(TokenizerContractError, match="streaming equivalence"):
            TokenizerV1TrainingCoordinator(request)._evaluate(
                successful.tokenizer, training_digests, holdout
            )

    def wrong_special(self: object, value: training.V1EncodeRequest):  # type: ignore[no-untyped-def]
        result = original_encode(self, value)  # type: ignore[arg-type]
        return (
            replace(result, token_ids=(0,) + result.token_ids[1:])
            if value.add_bos
            else result
        )

    with monkeypatch.context() as context:
        context.setattr(training.TokenizerV1SemanticCandidate, "encode", wrong_special)
        with pytest.raises(TokenizerContractError, match="v1 semantic"):
            TokenizerV1TrainingCoordinator(request)._evaluate(
                successful.tokenizer, training_digests, holdout
            )
    with monkeypatch.context() as context:
        context.setattr(
            training.TokenizerV1SemanticCandidate,
            "require_compatible_fingerprint",
            lambda self, fingerprint: None,
        )
        with pytest.raises(TokenizerContractError, match="negative or quality"):
            TokenizerV1TrainingCoordinator(request)._evaluate(
                successful.tokenizer, training_digests, holdout
            )

    def invalid_domain(*args: object, **kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(
            domain=args[0],
            sample_count=args[1],
            utf8_byte_count=args[2],
            unicode_scalar_count=args[3],
            candidate_token_count=args[4],
            byte_reference_token_count=args[5],
            reversible=False,
            no_worse_than_byte_reference=True,
        )

    with monkeypatch.context() as context:
        context.setattr(training, "V1TrainingDomainEvidence", invalid_domain)
        with pytest.raises(TokenizerContractError, match="per-domain quality"):
            TokenizerV1TrainingCoordinator(request)._evaluate(
                successful.tokenizer, training_digests, holdout
            )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("training_profile_id", "", "training_profile_id"),
        ("training_profile_id", "contains space", "training_profile_id"),
        ("training_profile_id", "é", "training_profile_id"),
        ("training_profile_id", "x" * 257, "training_profile_id"),
        ("training_profile_id", 1, "training_profile_id"),
        ("tokenizer_implementation_revision", "0" * 39, "Git revision"),
        ("tokenizer_implementation_revision", "g" * 40, "Git revision"),
        ("tokenizer_implementation_revision", 1, "Git revision"),
        ("dataset_manifest_sha256", "0" * 63, "SHA-256"),
        ("dataset_manifest_sha256", "g" * 64, "SHA-256"),
        ("dataset_manifest_sha256", 1, "SHA-256"),
        ("deadline_ns", True, "deadline_ns"),
        ("deadline_ns", "1", "deadline_ns"),
        ("deadline_ns", -1, "deadline_ns"),
        ("deadline_ns", MAX_BPE_TRAINING_DEADLINE_NS + 1, "deadline_ns"),
    ],
)
def test_request_validation_rejects_malformed_fields(
    field: str, value: object, message: str
) -> None:
    values: dict[str, object] = {
        "training_profile_id": training.V1_TRAINING_PROFILE_ID,
        "corpus_id": "corpus",
        "tokenizer_implementation_revision": _TOKENIZER_REVISION,
        "dataset_snapshot_revision": _DATASET_SNAPSHOT_REVISION,
        "dataset_implementation_revision": _DATASET_IMPLEMENTATION_REVISION,
        "dataset_manifest_sha256": _DATASET_MANIFEST,
        "dataset_replay_sha256": _DATASET_REPLAY,
        "admission_manifest_sha256": "3" * 64,
        "deadline_ns": None,
    }
    values[field] = value
    with pytest.raises(TokenizerContractError, match=message):
        V1TrainingRunRequest(**values)  # type: ignore[arg-type]


def test_coordinator_rejects_untrusted_contract_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request, manifest, supplied, holdout = _accepted_inputs(monkeypatch)
    with pytest.raises(TokenizerContractError, match="request type"):
        TokenizerV1TrainingCoordinator(object())  # type: ignore[arg-type]
    with pytest.raises(TokenizerContractError, match="cancellation type"):
        TokenizerV1TrainingCoordinator(request, object())  # type: ignore[arg-type]
    with pytest.raises(V1TrainingRunError) as invalid_manifest:
        TokenizerV1TrainingCoordinator(request).run(object(), supplied, holdout)  # type: ignore[arg-type]
    assert invalid_manifest.value.state is V1TrainingRunState.ADMISSION_ERROR
    with pytest.raises(V1TrainingRunError) as invalid_supplied:
        TokenizerV1TrainingCoordinator(request).run(manifest, list(supplied), holdout)  # type: ignore[arg-type]
    assert invalid_supplied.value.state is V1TrainingRunState.ADMISSION_ERROR


def test_holdout_identity_and_canonical_helpers_reject_invalid_values() -> None:
    expected = training.holdout_manifest_sha256(EVALUATION_MANIFEST)
    assert expected == training.holdout_manifest_sha256(EVALUATION_MANIFEST)
    with pytest.raises(TokenizerContractError, match="holdout manifest type"):
        training.holdout_manifest_sha256(object())  # type: ignore[arg-type]
    with pytest.raises(TokenizerContractError, match="integer"):
        training._integer(True)
    with pytest.raises(TokenizerContractError, match="integer"):
        training._integer("1")  # type: ignore[arg-type]
    with pytest.raises(TokenizerContractError, match="integer"):
        training._integer(-1)
    with pytest.raises(TokenizerContractError, match="boolean"):
        training._boolean(1)  # type: ignore[arg-type]
    with pytest.raises(TokenizerContractError, match="sequence digest"):
        training._digest_sequence(("x",), "test")


@pytest.mark.parametrize(
    "changes",
    [
        {"domain": "code"},
        {"sample_count": -1},
        {"sample_count": True},
        {"byte_reference_token_count": 2},
        {"reversible": 1},
        {"no_worse_than_byte_reference": 1},
        {"candidate_token_count": 2, "no_worse_than_byte_reference": True},
        {"candidate_token_count": 0, "no_worse_than_byte_reference": False},
    ],
)
def test_domain_evidence_rejects_inconsistent_values(
    changes: dict[str, object],
) -> None:
    values: dict[str, object] = {
        "domain": EvaluationDomain.CODE,
        "sample_count": 1,
        "utf8_byte_count": 1,
        "unicode_scalar_count": 1,
        "candidate_token_count": 1,
        "byte_reference_token_count": 1,
        "reversible": True,
        "no_worse_than_byte_reference": True,
    }
    values.update(changes)
    with pytest.raises(TokenizerContractError, match="domain evidence"):
        V1TrainingDomainEvidence(**values)  # type: ignore[arg-type]


def test_evidence_rejects_changed_identity_or_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = _successful_result(monkeypatch).evidence
    cases = (
        ("schema_version", "wrong", "not eligible"),
        ("training_profile_id", "wrong", "not eligible"),
        ("tokenizer_gate_head", "0" * 40, "not eligible"),
        ("tokenizer_gate_merge", "0" * 40, "not eligible"),
        ("tokenizer_gate_acceptance_comment_id", 1, "not eligible"),
        ("tokenizer_baseline_revision", "0" * 40, "not eligible"),
        ("semantic_profile", "wrong", "not eligible"),
        (
            "construction_finish_status",
            training.BpeTrainingFinishStatus.MERGE_BUDGET,
            "not eligible",
        ),
        ("domain_evidence", (), "not eligible"),
        ("lifecycle", (), "not eligible"),
        ("holdout_digest_disjoint", False, "not eligible"),
        ("streaming_equivalent", False, "not eligible"),
        ("independent_oracle_conformant", False, "not eligible"),
        ("v1_semantics_conformant", False, "not eligible"),
        ("negative_cases_conformant", False, "not eligible"),
        ("promotion_authorized", True, "not eligible"),
        ("evaluation_sha256", "x", "SHA-256"),
        ("evidence_sha256", "0" * 64, "digest mismatch"),
    )
    for field, value, message in cases:
        with pytest.raises(TokenizerContractError, match=message):
            replace(evidence, **{field: value})
