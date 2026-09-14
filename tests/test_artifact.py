"""Conformance tests for canonical non-executable byte-BPE artifacts."""

from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from struct import pack

import pytest

import cybersecgpt.tokenizer.artifact as artifact
from cybersecgpt.tokenizer import (
    ARTIFACT_FORMAT_ID,
    ARTIFACT_FORMAT_VERSION,
    MAX_BPE_ARTIFACT_BYTES,
    ArtifactSampleProvenance,
    BpeTrainingFinishStatus,
    ByteBpeTrainingConfig,
    ByteBpeTrainingResult,
    DecodeRequest,
    EncodeRequest,
    EvaluationDomain,
    EvaluationManifest,
    EvaluationSample,
    TokenizerContractError,
    load_byte_bpe_artifact,
    serialize_byte_bpe_artifact,
    train_byte_bpe_candidate,
)


def _manifest(source: str = "generated:test") -> EvaluationManifest:
    return EvaluationManifest(
        "fixture",
        "1",
        (
            EvaluationSample.from_text(
                sample_id="sample-0",
                domain=EvaluationDomain.CODE,
                text="abab jingïaroh",
                source_ref=source,
                license_id="CC0-1.0",
            ),
        ),
    )


def _fixture() -> tuple[ByteBpeTrainingResult, EvaluationManifest, bytes]:
    manifest = _manifest()
    result = train_byte_bpe_candidate(
        manifest,
        ByteBpeTrainingConfig(258, source_revision="test-sha"),
    )
    return result, manifest, serialize_byte_bpe_artifact(result, manifest)


def _redigest(data: bytes) -> bytes:
    return data[:-32] + sha256(data[:-32]).digest()


def _replace(data: bytes, old: bytes, new: bytes) -> bytes:
    assert len(old) == len(new)
    assert old in data
    return _redigest(data.replace(old, new, 1))


def test_known_vector_round_trip_identity_and_behavior() -> None:
    result, manifest, encoded = _fixture()
    loaded = load_byte_bpe_artifact(encoded)

    assert encoded == serialize_byte_bpe_artifact(result, manifest)
    assert encoded[:8] == b"CSGPTB1\0"
    assert ARTIFACT_FORMAT_ID.encode() in encoded
    assert ARTIFACT_FORMAT_VERSION == 1
    assert len(encoded) == 1744
    assert result.candidate.descriptor.fingerprint == (
        "858fada45bcd428a9198e29da156f2c1b11f3922ecf985606b574eb6b293e71b"
    )
    assert sha256(encoded[:-32]).hexdigest() == (
        "7e5f465535fc69b7f260369c1044ac569aca468c14b1b41215837c1c9d3edb25"
    )
    assert sha256(encoded).hexdigest() == (
        "8206b62e3349e1cacf36b8451e199224717d1fa875494b1cf6098291ef844853"
    )
    assert sha256(encoded[:-32]).hexdigest() == loaded.artifact_digest
    assert loaded.canonical_bytes == encoded
    assert loaded.manifest_id == manifest.manifest_id
    assert loaded.samples == (
        ArtifactSampleProvenance(
            "sample-0",
            EvaluationDomain.CODE,
            "generated:test",
            "CC0-1.0",
            manifest.samples[0].content_sha256,
        ),
    )
    request = EncodeRequest(manifest.samples[0].text)
    before = result.candidate.encode(request)
    after = loaded.candidate.encode(request)
    assert before == after
    assert loaded.candidate.decode(DecodeRequest(after.token_ids)).text == request.text
    with pytest.raises(FrozenInstanceError):
        loaded.manifest_id = "changed"  # type: ignore[misc]


def test_provenance_changes_artifact_digest_not_candidate_fingerprint() -> None:
    first_manifest = _manifest("generated:first")
    second_manifest = _manifest("generated:other")
    config = ByteBpeTrainingConfig(258, source_revision="test-sha")
    first_result = train_byte_bpe_candidate(first_manifest, config)
    second_result = train_byte_bpe_candidate(second_manifest, config)
    first = load_byte_bpe_artifact(
        serialize_byte_bpe_artifact(first_result, first_manifest)
    )
    second = load_byte_bpe_artifact(
        serialize_byte_bpe_artifact(second_result, second_manifest)
    )

    assert (
        first.candidate.descriptor.fingerprint
        == second.candidate.descriptor.fingerprint
    )
    assert first.artifact_digest != second.artifact_digest


@pytest.mark.parametrize("value", [None, bytearray(), memoryview(b"")])
def test_loader_rejects_non_bytes(value: object) -> None:
    with pytest.raises(TokenizerContractError, match="invalid canonical"):
        load_byte_bpe_artifact(value)  # type: ignore[arg-type]


def test_loader_rejects_envelope_corruption_before_payload_parsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, encoded = _fixture()
    malformed = (
        b"",
        encoded[:45],
        b"x" + encoded[1:],
        encoded[:8] + pack("!H", 2) + encoded[10:],
        encoded[:10] + pack("!I", 1) + encoded[14:],
        encoded[:-1] + bytes((encoded[-1] ^ 1,)),
    )
    for value in malformed:
        with pytest.raises(TokenizerContractError, match="invalid canonical"):
            load_byte_bpe_artifact(value)
    monkeypatch.setattr(artifact, "MAX_BPE_ARTIFACT_BYTES", len(encoded) - 1)
    with pytest.raises(TokenizerContractError, match="invalid canonical"):
        load_byte_bpe_artifact(encoded)


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (ARTIFACT_FORMAT_ID.encode(), b"x" * len(ARTIFACT_FORMAT_ID)),
        (b"vocabulary_limit", b"no_eligible_pair"),
    ],
)
def test_loader_rejects_independently_mutated_payload(old: bytes, new: bytes) -> None:
    _, _, encoded = _fixture()
    with pytest.raises(TokenizerContractError, match="invalid canonical"):
        load_byte_bpe_artifact(_replace(encoded, old, new))


def test_loaded_provenance_mutations_remain_data_but_change_digest() -> None:
    _, _, encoded = _fixture()
    for old, new in (
        (b"generated:test", b"generated:else"),
        (b"CC0-1.0", b"CC0-1.x"),
    ):
        changed = load_byte_bpe_artifact(_replace(encoded, old, new))
        assert changed.artifact_digest != sha256(encoded[:-32]).hexdigest()


def test_loader_rejects_trailing_payload_and_invalid_utf8() -> None:
    _, _, encoded = _fixture()
    payload = encoded[14:-32]
    envelope = encoded[:10] + pack("!I", len(payload) + 1) + payload + b"x"
    trailing = envelope + sha256(envelope).digest()
    with pytest.raises(TokenizerContractError, match="invalid canonical"):
        load_byte_bpe_artifact(trailing)
    invalid_utf8 = bytearray(encoded)
    position = encoded.index(b"fixture")
    invalid_utf8[position] = 0xFF
    with pytest.raises(TokenizerContractError, match="invalid canonical"):
        load_byte_bpe_artifact(_redigest(bytes(invalid_utf8)))


def test_internal_bounded_readers_reject_invalid_lengths_and_metadata() -> None:
    for value in ("", "x" * 65_536):
        with pytest.raises(TokenizerContractError, match="invalid canonical"):
            artifact._text(value)
    for value in ("", "bad value", "x" * 257):
        with pytest.raises(TokenizerContractError, match="invalid canonical"):
            artifact._identifier(value)
    with pytest.raises(TokenizerContractError, match="invalid canonical"):
        artifact._source_revision("é")
    for value in ("0" * 63, "g" * 64):
        with pytest.raises(TokenizerContractError, match="invalid canonical"):
            artifact._digest(value)
    reader = artifact._Reader(b"\x00\x00")
    with pytest.raises(TokenizerContractError, match="invalid canonical"):
        reader.text()
    with pytest.raises(TokenizerContractError, match="invalid canonical"):
        artifact._Reader(b"").integer()
    with pytest.raises(TokenizerContractError, match="invalid canonical"):
        artifact._Reader(b"")._take(-1)


def test_finish_status_paths_are_canonical() -> None:
    manifest = EvaluationManifest(
        "empty",
        "1",
        (
            EvaluationSample.from_text(
                sample_id="sample",
                domain=EvaluationDomain.CODE,
                text="",
                source_ref="generated:test",
                license_id="CC0-1.0",
            ),
        ),
    )
    no_pair = train_byte_bpe_candidate(manifest, ByteBpeTrainingConfig(257))
    budget = train_byte_bpe_candidate(
        _manifest(), ByteBpeTrainingConfig(300, merge_budget=1)
    )
    assert (
        load_byte_bpe_artifact(
            serialize_byte_bpe_artifact(no_pair, manifest)
        ).finish_status
        is BpeTrainingFinishStatus.NO_ELIGIBLE_PAIR
    )
    assert (
        load_byte_bpe_artifact(
            serialize_byte_bpe_artifact(budget, _manifest())
        ).finish_status
        is BpeTrainingFinishStatus.MERGE_BUDGET
    )


def test_loader_rejects_sample_count_duplicate_domain_status_and_descriptor() -> None:
    result, manifest, encoded = _fixture()
    marker = b"\x00\x07fixture\x00\x011"
    count_position = encoded.index(marker) + len(marker)
    bad_count = _redigest(
        encoded[:count_position] + pack("!I", 0) + encoded[count_position + 4 :]
    )
    invalid_domain = _replace(encoded, b"\x00\x04code", b"\x00\x04fail")
    invalid_status = _replace(
        encoded,
        b"\x00\x10vocabulary_limit",
        b"\x00\x10invalid_statusxx",
    )
    fingerprint = result.candidate.descriptor.fingerprint.encode()
    invalid_descriptor = _replace(encoded, fingerprint, b"0" * 64)
    for value in (bad_count, invalid_domain, invalid_status, invalid_descriptor):
        with pytest.raises(TokenizerContractError, match="invalid canonical"):
            load_byte_bpe_artifact(value)

    two_manifest = EvaluationManifest(
        "fixture",
        "1",
        manifest.samples
        + (
            EvaluationSample.from_text(
                sample_id="sample-1",
                domain=EvaluationDomain.CODE,
                text="cdcd",
                source_ref="generated:test",
                license_id="CC0-1.0",
            ),
        ),
    )
    two_result = train_byte_bpe_candidate(
        two_manifest, ByteBpeTrainingConfig(258, source_revision="test-sha")
    )
    duplicate = serialize_byte_bpe_artifact(two_result, two_manifest)
    duplicate = _replace(duplicate, b"sample-1", b"sample-0")
    with pytest.raises(TokenizerContractError, match="invalid canonical"):
        load_byte_bpe_artifact(duplicate)


def test_loader_rejects_noncanonical_rebuild(monkeypatch: pytest.MonkeyPatch) -> None:
    _, _, encoded = _fixture()
    monkeypatch.setattr(artifact, "_serialize_loaded", lambda loaded: b"")
    with pytest.raises(TokenizerContractError, match="invalid canonical"):
        load_byte_bpe_artifact(encoded)


def test_serializer_rejects_forged_or_unbound_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, manifest, _ = _fixture()
    bad_results = (
        replace(result, manifest_id="other"),
        replace(result, sample_digests=("0" * 64,)),
        replace(result, requested_vocabulary_limit=256),
        replace(result, requested_vocabulary_limit=513),
        replace(result, merge_budget=1),
        replace(result, max_training_bytes=-1),
        replace(result, source_revision="bad revision"),
        replace(result, implementation_version="other"),
        replace(result, finish_status=BpeTrainingFinishStatus.NO_ELIGIBLE_PAIR),
    )
    for bad in bad_results:
        with pytest.raises(TokenizerContractError, match="invalid canonical"):
            serialize_byte_bpe_artifact(bad, manifest)
    with pytest.raises(TokenizerContractError, match="invalid canonical"):
        serialize_byte_bpe_artifact(object(), manifest)  # type: ignore[arg-type]
    with pytest.raises(TokenizerContractError, match="invalid canonical"):
        serialize_byte_bpe_artifact(result, object())  # type: ignore[arg-type]

    monkeypatch.setattr(artifact, "MAX_BPE_ARTIFACT_BYTES", 1)
    with pytest.raises(TokenizerContractError, match="invalid canonical"):
        serialize_byte_bpe_artifact(result, manifest)  # type: ignore[arg-type]


def test_loader_rejects_invalid_counts_tokens_merges_and_canonical_data() -> None:
    _, _, encoded = _fixture()
    mutations = []
    vocab_marker = pack("!I", 258) + pack("!I", 1) + b"\x00"
    vocab_position = encoded.index(vocab_marker)
    mutations.append(
        _redigest(
            encoded[:vocab_position] + pack("!I", 255) + encoded[vocab_position + 4 :]
        )
    )
    token_position = vocab_position + 4
    mutations.append(
        _redigest(
            encoded[:token_position] + pack("!I", 0) + encoded[token_position + 4 :]
        )
    )
    merge_count_position = len(encoded) - 32 - 4 - (2 * 12)
    mutations.append(
        _redigest(
            encoded[:merge_count_position]
            + pack("!I", 257)
            + encoded[merge_count_position + 4 :]
        )
    )
    merge_position = merge_count_position + 4
    mutations.append(
        _redigest(
            encoded[:merge_position] + pack("!I", 256) + encoded[merge_position + 4 :]
        )
    )
    for value in mutations:
        with pytest.raises(TokenizerContractError, match="invalid canonical"):
            load_byte_bpe_artifact(value)


def test_serializer_rejects_oversized_learned_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, manifest, _ = _fixture()
    monkeypatch.setattr(artifact, "MAX_BPE_ARTIFACT_TOKEN_BYTES", 1)
    with pytest.raises(TokenizerContractError, match="invalid canonical"):
        serialize_byte_bpe_artifact(result, manifest)


def test_limits_are_fixed() -> None:
    assert MAX_BPE_ARTIFACT_BYTES == 16 * 1024 * 1024
    assert BpeTrainingFinishStatus.VOCABULARY_LIMIT.value == "vocabulary_limit"
