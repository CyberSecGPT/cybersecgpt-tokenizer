"""Replay pinned, inert P6.8 experimental conformance vectors offline."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any, Final, cast

from benchmarks.p6_4_corpus import CONSTRUCTION_MANIFEST

from cybersecgpt.tokenizer import (
    BENCHMARK_BPE_MERGE_BUDGET,
    BENCHMARK_MAX_TRAINING_BYTES,
    BENCHMARK_VOCABULARY_LIMIT,
    ByteBpeStreamingEncoder,
    ByteBpeTrainingConfig,
    DecodeRequest,
    EncodeRequest,
    EvaluationDomain,
    FinishStatus,
    StreamingDeadlineError,
    TokenizerContractError,
    Utf8ByteReferenceTokenizer,
    load_byte_bpe_artifact,
    serialize_byte_bpe_artifact,
    train_byte_bpe_candidate,
)

SCHEMA_VERSION: Final = "p6.8-experimental-conformance-v1"
SOURCE_REVISION: Final = "c863af96bfee43889b8c2be8d98e5d9c55868433"
VECTOR_PATH: Final = (
    Path(__file__).resolve().parents[1] / "docs/evidence/P6_8_vectors.json"
)
MAX_FIXTURE_BYTES: Final = 65_536
MAX_VECTOR_COUNT: Final = 32
MAX_VECTOR_BYTES: Final = 256
MAX_VECTOR_PARTITIONS: Final = 256


class ConformanceError(ValueError):
    """A bounded fixture or its pinned expected behavior disagrees."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ConformanceError(message)


def _object(value: Any, fields: set[str]) -> dict[str, Any]:
    _require(type(value) is dict and set(value) == fields, "invalid vector schema")
    return cast(dict[str, Any], value)


def _sha(value: Any) -> str:
    _require(
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value),
        "invalid digest",
    )
    return cast(str, value)


def _ids(value: Any, maximum: int) -> tuple[int, ...]:
    _require(
        type(value) is list
        and len(value) <= maximum
        and all(type(item) is int and 0 <= item < 512 for item in value),
        "invalid expected token IDs",
    )
    return tuple(value)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result, "duplicate fixture field")
        result[key] = value
    return result


def _oracle_bpe(data: bytes, merges: tuple[tuple[int, int], ...]) -> tuple[int, ...]:
    """Independent left-to-right token-list calculation of ordered merge rules."""

    pieces = list(data)
    for rank, pair in enumerate(merges, start=256):
        output: list[int] = []
        cursor = 0
        while cursor < len(pieces):
            if tuple(pieces[cursor : cursor + 2]) == pair:
                output.append(rank)
                cursor += 2
            else:
                output.append(pieces[cursor])
                cursor += 1
        pieces = output
    return tuple(pieces)


def verify_vectors(path: Path = VECTOR_PATH) -> tuple[int, str]:
    """Validate fixture metadata and exact behavior without logging sample text."""

    _require(path.stat().st_size <= MAX_FIXTURE_BYTES, "fixture exceeds byte limit")
    raw = path.read_bytes()
    _require(len(raw) <= MAX_FIXTURE_BYTES, "fixture exceeds byte limit")
    try:
        data = json.loads(
            raw,
            parse_constant=lambda _: _require(False, "invalid JSON number"),
            object_pairs_hook=_unique_object,
        )
    except (UnicodeError, ValueError) as error:
        raise ConformanceError("invalid fixture JSON") from error
    _require(
        raw == (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        "non-canonical fixture JSON",
    )
    record = _object(
        data,
        {
            "schema_version",
            "source_revision",
            "construction_manifest_id",
            "construction_manifest_version",
            "construction_sample_digests",
            "bpe_fingerprint",
            "artifact_sha256",
            "artifact_digest",
            "vectors",
        },
    )
    _require(record["schema_version"] == SCHEMA_VERSION, "schema version mismatch")
    _require(record["source_revision"] == SOURCE_REVISION, "source revision mismatch")
    _require(
        record["construction_manifest_id"] == CONSTRUCTION_MANIFEST.manifest_id
        and record["construction_manifest_version"] == CONSTRUCTION_MANIFEST.version,
        "construction manifest mismatch",
    )
    _require(
        record["construction_sample_digests"]
        == [item.content_sha256 for item in CONSTRUCTION_MANIFEST.samples],
        "construction sample mismatch",
    )
    expected_fingerprint = _sha(record["bpe_fingerprint"])
    expected_artifact_sha = _sha(record["artifact_sha256"])
    expected_artifact_digest = _sha(record["artifact_digest"])
    _require(
        type(record["vectors"]) is list
        and 1 <= len(record["vectors"]) <= MAX_VECTOR_COUNT,
        "invalid vector count",
    )
    result = train_byte_bpe_candidate(
        CONSTRUCTION_MANIFEST,
        ByteBpeTrainingConfig(
            vocabulary_limit=BENCHMARK_VOCABULARY_LIMIT,
            merge_budget=BENCHMARK_BPE_MERGE_BUDGET,
            max_training_bytes=BENCHMARK_MAX_TRAINING_BYTES,
            source_revision=SOURCE_REVISION,
        ),
    )
    candidate = result.candidate
    _require(
        candidate.descriptor.fingerprint == expected_fingerprint,
        "BPE identity mismatch",
    )
    canonical = serialize_byte_bpe_artifact(result, CONSTRUCTION_MANIFEST)
    _require(
        sha256(canonical).hexdigest() == expected_artifact_sha, "artifact SHA mismatch"
    )
    loaded = load_byte_bpe_artifact(canonical)
    _require(
        loaded.artifact_digest == expected_artifact_digest, "artifact digest mismatch"
    )
    _require(loaded.canonical_bytes == canonical, "artifact round trip mismatch")
    _require(
        loaded.candidate.descriptor.fingerprint == expected_fingerprint,
        "loaded behavior mismatch",
    )
    merges = tuple((merge.left_id, merge.right_id) for merge in candidate.merges)
    seen: set[str] = set()
    covered_domains: set[EvaluationDomain] = set()
    total_bytes = 0
    for item in record["vectors"]:
        vector = _object(
            item,
            {
                "case_id",
                "domain",
                "text",
                "source_ref",
                "license_id",
                "input_sha256",
                "reference_ids",
                "bpe_ids",
                "max_tokens",
                "finish_status",
            },
        )
        case_id = vector["case_id"]
        _require(
            type(case_id) is str
            and 1 <= len(case_id) <= 64
            and case_id.isascii()
            and case_id not in seen
            and all(char.isalnum() or char in "-_" for char in case_id),
            "invalid case ID",
        )
        seen.add(case_id)
        _require(
            type(vector["domain"]) is str
            and vector["domain"] in {domain.value for domain in EvaluationDomain}
            and type(vector["source_ref"]) is str
            and vector["source_ref"] == "generated:cybersecgpt-tokenizer:p6.8"
            and vector["license_id"] == "CC0-1.0",
            "invalid fixture provenance",
        )
        covered_domains.add(EvaluationDomain(vector["domain"]))
        _require(type(vector["text"]) is str, "invalid input type")
        encoded = vector["text"].encode("utf-8")
        total_bytes += len(encoded)
        _require(
            len(encoded) <= MAX_VECTOR_BYTES and total_bytes <= 4096, "input byte limit"
        )
        _require(
            sha256(encoded).hexdigest() == _sha(vector["input_sha256"]),
            "input digest mismatch",
        )
        limit = vector["max_tokens"]
        _require(type(limit) is int and 0 <= limit <= 256, "invalid token limit")
        reference_ids = _ids(vector["reference_ids"], MAX_VECTOR_BYTES)
        bpe_ids = _ids(vector["bpe_ids"], MAX_VECTOR_BYTES)
        _require(
            vector["finish_status"] in ("completed", "truncated"),
            "invalid finish status",
        )
        status = FinishStatus(vector["finish_status"])
        _require(
            reference_ids == tuple(encoded[:limit]),
            f"reference oracle mismatch: {case_id}",
        )
        oracle = _oracle_bpe(encoded, merges)
        _require(bpe_ids == oracle[:limit], f"BPE oracle mismatch: {case_id}")
        _require(
            status
            is (
                FinishStatus.TRUNCATED
                if len(oracle) > limit
                else FinishStatus.COMPLETED
            )
            and (len(encoded) > limit) == (len(reference_ids) < len(encoded)),
            f"completion status mismatch: {case_id}",
        )
        request = EncodeRequest(vector["text"], max_tokens=limit)
        ref_result = Utf8ByteReferenceTokenizer.encode(request)
        bpe_result = candidate.encode(request)
        _require(
            ref_result.token_ids == reference_ids
            and ref_result.finish_status
            is (
                FinishStatus.TRUNCATED
                if len(encoded) > limit
                else FinishStatus.COMPLETED
            )
            and bpe_result.token_ids == bpe_ids
            and bpe_result.finish_status is status
            and bpe_result.tokenizer_fingerprint == expected_fingerprint,
            f"encode mismatch: {case_id}",
        )
        if status is FinishStatus.COMPLETED:
            _require(
                candidate.decode(DecodeRequest(bpe_ids)).text == vector["text"]
                and Utf8ByteReferenceTokenizer.decode(DecodeRequest(reference_ids)).text
                == vector["text"],
                f"round trip mismatch: {case_id}",
            )
        _require(len(encoded) + 1 <= MAX_VECTOR_PARTITIONS, "partition limit")
        for split in range(len(encoded) + 1):
            stream = ByteBpeStreamingEncoder(candidate, max_tokens=limit)
            stream.push(encoded[:split])
            stream.push(encoded[split:])
            _require(stream.finish() == bpe_result, f"stream mismatch: {case_id}")
    _require(covered_domains == set(EvaluationDomain), "domain coverage mismatch")
    return len(seen), sha256(raw).hexdigest()


def verify_negative_boundaries() -> None:
    """Fail closed on invalid input, IDs, stream state, and artifact integrity."""

    result = train_byte_bpe_candidate(
        CONSTRUCTION_MANIFEST,
        ByteBpeTrainingConfig(
            BENCHMARK_VOCABULARY_LIMIT, source_revision=SOURCE_REVISION
        ),
    )
    candidate = result.candidate
    for candidate_impl in (candidate, Utf8ByteReferenceTokenizer):
        for request in (EncodeRequest("<|tool|>", add_special_tokens=True),):
            try:
                candidate_impl.encode(request)
            except TokenizerContractError:
                pass
            else:
                raise ConformanceError("unexpected special-token permission")
        for ids in ((candidate_impl.descriptor.vocabulary_size,), (0xFF,)):
            try:
                candidate_impl.decode(DecodeRequest(ids))
            except TokenizerContractError:
                pass
            else:
                raise ConformanceError("invalid decode promoted to success")
    stream = ByteBpeStreamingEncoder(candidate)
    stream.push(b"\xc3")
    try:
        stream.finish()
    except TokenizerContractError:
        pass
    else:
        raise ConformanceError("invalid UTF-8 promoted to success")
    stream = ByteBpeStreamingEncoder(candidate)
    stream.push(b"test")
    stream.cancel()
    try:
        stream.finish()
    except TokenizerContractError:
        pass
    else:
        raise ConformanceError("cancelled stream promoted to success")
    try:
        ByteBpeStreamingEncoder(candidate, deadline_ns=0)
    except StreamingDeadlineError:
        pass
    else:
        raise ConformanceError("expired stream deadline promoted to success")
    canonical = serialize_byte_bpe_artifact(result, CONSTRUCTION_MANIFEST)
    for bad in (
        canonical[:-1] + bytes((canonical[-1] ^ 1,)),
        canonical[:8] + b"\x00\x02" + canonical[10:],
        canonical + b"\x00",
    ):
        try:
            load_byte_bpe_artifact(bad)
        except TokenizerContractError:
            pass
        else:
            raise ConformanceError("invalid artifact promoted to success")


def main() -> None:
    count, digest = verify_vectors()
    verify_negative_boundaries()
    print(f"P6.8 experimental vectors verified: count={count} fixture_sha256={digest}")


if __name__ == "__main__":
    main()
