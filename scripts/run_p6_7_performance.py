"""Measure fixed P6.4 fixtures without changing deterministic benchmark identity."""

from __future__ import annotations

import json
import platform
import sys
import tracemalloc
from collections.abc import Callable
from functools import partial
from hashlib import sha256
from statistics import median
from threading import Event
from time import monotonic_ns, perf_counter_ns
from typing import cast

from benchmarks.p6_4_corpus import CONSTRUCTION_MANIFEST, EVALUATION_MANIFEST

from cybersecgpt.tokenizer import (
    ByteBpeStreamingEncoder,
    DecodeRequest,
    EncodeRequest,
    FinishStatus,
    Utf8ByteReferenceTokenizer,
    load_byte_bpe_artifact,
    serialize_byte_bpe_artifact,
)
from cybersecgpt.tokenizer.benchmark import (
    BENCHMARK_BPE_MERGE_BUDGET,
    BENCHMARK_MAX_TRAINING_BYTES,
    BENCHMARK_VOCABULARY_LIMIT,
    run_algorithm_benchmark,
)
from cybersecgpt.tokenizer.byte_bpe import (
    ByteBpeTrainingConfig,
    train_byte_bpe_candidate,
)
from cybersecgpt.tokenizer.contracts import EncodeResult
from cybersecgpt.tokenizer.evaluation import EvaluationManifest
from cybersecgpt.tokenizer.unigram import (
    ByteUnigramTrainingConfig,
    train_byte_unigram_candidate,
)

SOURCE_REVISION = "p6.4-gate-dd063926"
STRUCTURAL_FINGERPRINT = (
    "f979122b76acffb434a536fd8e834fa9a1ce5d92bc1bb8cceda737e42a638b32"
)
MAX_SAMPLES = 128
MAX_FIXTURE_BYTES = 1024 * 1024
MAX_REPETITIONS = 8
MAX_REPORT_BYTES = 1024 * 1024
DEFAULT_REPETITIONS = 3
CHUNK_BYTES = 31
MAX_RUN_NS = 120 * 1_000_000_000


class PerformanceEvidenceError(RuntimeError):
    """A bounded or correctness measurement failed without exposing content."""


def _check_stop(cancelled: Event, deadline_ns: int) -> None:
    if cancelled.is_set() or monotonic_ns() >= deadline_ns:
        raise PerformanceEvidenceError("incomplete: cancelled or deadline reached")


def measure(
    operation: Callable[[], object],
    expected: object,
    *,
    repetitions: int,
    cancelled: Event,
    deadline_ns: int,
) -> dict[str, object]:
    """Observe success and traced allocations separately from timing trials."""

    if type(repetitions) is not int or not 1 <= repetitions <= MAX_REPETITIONS:
        raise PerformanceEvidenceError("invalid repetition limit")
    _check_stop(cancelled, deadline_ns)
    try:
        warmup = operation()
    except Exception:
        raise PerformanceEvidenceError("incomplete: operation error") from None
    if warmup != expected:
        raise PerformanceEvidenceError("incomplete: warmup result mismatch")
    _check_stop(cancelled, deadline_ns)
    trials: list[int] = []
    for _ in range(repetitions):
        _check_stop(cancelled, deadline_ns)
        start = perf_counter_ns()
        try:
            result = operation()
        except Exception:
            raise PerformanceEvidenceError("incomplete: operation error") from None
        elapsed = perf_counter_ns() - start
        _check_stop(cancelled, deadline_ns)
        if result != expected or elapsed < 0:
            raise PerformanceEvidenceError("incomplete: trial result mismatch")
        trials.append(elapsed)
    _check_stop(cancelled, deadline_ns)
    tracemalloc.start()
    try:
        tracemalloc.reset_peak()
        try:
            measured = operation()
        except Exception:
            raise PerformanceEvidenceError("incomplete: operation error") from None
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    _check_stop(cancelled, deadline_ns)
    if measured != expected:
        raise PerformanceEvidenceError("incomplete: allocation result mismatch")
    return {"trials_ns": trials, "median_ns": median(trials), "traced_peak_bytes": peak}


def _stream_ingest(
    candidate: object, data: bytes
) -> tuple[ByteBpeStreamingEncoder, int]:
    # The timer for ingestion excludes finalization; the encoder is single-use.
    from cybersecgpt.tokenizer.byte_bpe import ByteBpeCandidate

    if not isinstance(candidate, ByteBpeCandidate):
        raise PerformanceEvidenceError("candidate binding mismatch")
    encoder = ByteBpeStreamingEncoder(candidate)
    for offset in range(0, len(data), CHUNK_BYTES):
        encoder.push(data[offset : offset + CHUNK_BYTES])
    return encoder, encoder.buffered_byte_count


def _stream_finalize(candidate: object, data: bytes) -> EncodeResult:
    encoder, count = _stream_ingest(candidate, data)
    if count != len(data):
        raise PerformanceEvidenceError("incomplete: streaming byte mismatch")
    return encoder.finish()


def _stream_measurements(
    candidate: object,
    data: bytes,
    expected: EncodeResult,
    repetitions: int,
    cancelled: Event,
    deadline_ns: int,
) -> dict[str, object]:
    if _stream_finalize(candidate, data) != expected:
        raise PerformanceEvidenceError("incomplete: chunk equivalence mismatch")
    ingestion = measure(
        lambda: _stream_ingest(candidate, data)[1],
        len(data),
        repetitions=repetitions,
        cancelled=cancelled,
        deadline_ns=deadline_ns,
    )
    _check_stop(cancelled, deadline_ns)
    warm, _ = _stream_ingest(candidate, data)
    if warm.finish() != expected:
        raise PerformanceEvidenceError("incomplete: streaming finalization mismatch")
    finalize_trials: list[int] = []
    for _ in range(repetitions):
        _check_stop(cancelled, deadline_ns)
        encoder, _ = _stream_ingest(candidate, data)
        start = perf_counter_ns()
        result = encoder.finish()
        elapsed = perf_counter_ns() - start
        _check_stop(cancelled, deadline_ns)
        if result != expected or elapsed < 0:
            raise PerformanceEvidenceError(
                "incomplete: streaming finalization mismatch"
            )
        finalize_trials.append(elapsed)
    encoder, _ = _stream_ingest(candidate, data)
    tracemalloc.start()
    try:
        tracemalloc.reset_peak()
        result = encoder.finish()
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    _check_stop(cancelled, deadline_ns)
    if result != expected:
        raise PerformanceEvidenceError("incomplete: streaming finalization mismatch")
    finalization = {
        "trials_ns": finalize_trials,
        "median_ns": median(finalize_trials),
        "traced_peak_bytes": peak,
    }
    complete = measure(
        lambda: _stream_finalize(candidate, data),
        expected,
        repetitions=repetitions,
        cancelled=cancelled,
        deadline_ns=deadline_ns,
    )
    return {
        "ingestion": ingestion,
        "finalization": finalization,
        "ingestion_and_finalize": complete,
    }


def throughput(count: int, duration_ns: int | float) -> int | None:
    """Report floored units per second; zero-nanosecond samples are undefined."""

    if count < 0 or duration_ns < 0:
        raise PerformanceEvidenceError("invalid throughput observation")
    return int(count * 1_000_000_000 // duration_ns) if duration_ns else None


def domain_totals(observations: list[dict[str, object]]) -> list[dict[str, object]]:
    """Keep every candidate/domain visible, with no hidden aggregate regression."""

    totals: dict[tuple[str, str], dict[str, object]] = {}
    for item in observations:
        algorithm, domain = str(item["algorithm_id"]), str(item["domain"])
        key = algorithm, domain
        entry = totals.setdefault(
            key,
            {
                "algorithm_id": algorithm,
                "domain": domain,
                "input_bytes": 0,
                "tokens": 0,
                "encode_median_ns_sum": 0,
                "decode_median_ns_sum": 0,
            },
        )
        encoding = item["encode"]
        decoding = item["decode"]
        if not isinstance(encoding, dict) or not isinstance(decoding, dict):
            raise PerformanceEvidenceError("incomplete: observation mismatch")
        entry["input_bytes"] = cast(int, entry["input_bytes"]) + cast(
            int, item["input_bytes"]
        )
        entry["tokens"] = cast(int, entry["tokens"]) + cast(int, item["tokens"])
        entry["encode_median_ns_sum"] = cast(
            int | float, entry["encode_median_ns_sum"]
        ) + cast(int | float, encoding["median_ns"])
        entry["decode_median_ns_sum"] = cast(
            int | float, entry["decode_median_ns_sum"]
        ) + cast(int | float, decoding["median_ns"])
    result: list[dict[str, object]] = []
    for entry in totals.values():
        entry["encode_input_bytes_per_second_floor"] = throughput(
            cast(int, entry["input_bytes"]),
            cast(int | float, entry["encode_median_ns_sum"]),
        )
        entry["encode_tokens_per_second_floor"] = throughput(
            cast(int, entry["tokens"]), cast(int | float, entry["encode_median_ns_sum"])
        )
        entry["decode_tokens_per_second_floor"] = throughput(
            cast(int, entry["tokens"]), cast(int | float, entry["decode_median_ns_sum"])
        )
        result.append(entry)
    return result


def _bounded_manifest(manifest: EvaluationManifest) -> None:
    if (
        len(manifest.samples) > MAX_SAMPLES
        or sum(len(sample.text.encode("utf-8")) for sample in manifest.samples)
        > MAX_FIXTURE_BYTES
    ):
        raise PerformanceEvidenceError("fixture limit exceeded")


def run(
    *,
    source_commit: str,
    repetitions: int = DEFAULT_REPETITIONS,
    cancelled: Event | None = None,
) -> dict[str, object]:
    """Produce bounded observations for the fixed, disjoint P6.4 manifests."""

    if len(source_commit) != 40 or any(
        c not in "0123456789abcdef" for c in source_commit
    ):
        raise PerformanceEvidenceError("invalid source commit")
    if type(repetitions) is not int or not 1 <= repetitions <= MAX_REPETITIONS:
        raise PerformanceEvidenceError("invalid repetition limit")
    stop = cancelled if cancelled is not None else Event()
    deadline_ns = monotonic_ns() + MAX_RUN_NS
    _bounded_manifest(CONSTRUCTION_MANIFEST)
    _bounded_manifest(EVALUATION_MANIFEST)
    if {s.content_sha256 for s in CONSTRUCTION_MANIFEST.samples} & {
        s.content_sha256 for s in EVALUATION_MANIFEST.samples
    }:
        raise PerformanceEvidenceError("manifest overlap")
    _check_stop(stop, deadline_ns)
    structural = run_algorithm_benchmark(
        CONSTRUCTION_MANIFEST, EVALUATION_MANIFEST, source_revision=SOURCE_REVISION
    )
    if structural.report_fingerprint != STRUCTURAL_FINGERPRINT or any(
        s.finish_status is not FinishStatus.COMPLETED or not s.reversible
        for candidate in structural.candidates
        for s in candidate.samples
    ):
        raise PerformanceEvidenceError("structural evidence mismatch")
    bpe = train_byte_bpe_candidate(
        CONSTRUCTION_MANIFEST,
        ByteBpeTrainingConfig(
            BENCHMARK_VOCABULARY_LIMIT,
            merge_budget=BENCHMARK_BPE_MERGE_BUDGET,
            max_training_bytes=BENCHMARK_MAX_TRAINING_BYTES,
            source_revision=SOURCE_REVISION,
        ),
    )
    unigram = train_byte_unigram_candidate(
        CONSTRUCTION_MANIFEST,
        ByteUnigramTrainingConfig(
            BENCHMARK_VOCABULARY_LIMIT,
            max_training_bytes=BENCHMARK_MAX_TRAINING_BYTES,
            source_revision=SOURCE_REVISION,
        ),
    )
    artifact = serialize_byte_bpe_artifact(bpe, CONSTRUCTION_MANIFEST)
    loaded = load_byte_bpe_artifact(artifact)
    if loaded.candidate != bpe.candidate:
        raise PerformanceEvidenceError("artifact round-trip mismatch")
    candidates = (Utf8ByteReferenceTokenizer(), bpe.candidate, unigram.candidate)
    if tuple(c.descriptor.fingerprint for c in candidates) != tuple(
        c.tokenizer_fingerprint for c in structural.candidates
    ):
        raise PerformanceEvidenceError("candidate fingerprint mismatch")
    observations: list[dict[str, object]] = []
    for candidate in candidates:
        for sample in EVALUATION_MANIFEST.samples:
            _check_stop(stop, deadline_ns)
            request = EncodeRequest(sample.text)
            encoded = candidate.encode(request)
            if (
                encoded.finish_status is not FinishStatus.COMPLETED
                or encoded.tokenizer_fingerprint != candidate.descriptor.fingerprint
            ):
                raise PerformanceEvidenceError("incomplete: encode mismatch")
            decode_request = DecodeRequest(encoded.token_ids)
            decoded = candidate.decode(decode_request)
            if (
                decoded.finish_status is not FinishStatus.COMPLETED
                or decoded.text != sample.text
                or decoded.tokenizer_fingerprint != candidate.descriptor.fingerprint
            ):
                raise PerformanceEvidenceError("incomplete: decode mismatch")
            encode_measure = measure(
                partial(candidate.encode, request),
                encoded,
                repetitions=repetitions,
                cancelled=stop,
                deadline_ns=deadline_ns,
            )
            decode_measure = measure(
                partial(candidate.decode, decode_request),
                decoded,
                repetitions=repetitions,
                cancelled=stop,
                deadline_ns=deadline_ns,
            )
            data = sample.text.encode("utf-8")
            entry: dict[str, object] = {
                "algorithm_id": candidate.descriptor.algorithm_id,
                "fingerprint": candidate.descriptor.fingerprint,
                "sample_id": sample.sample_id,
                "domain": sample.domain.value,
                "content_sha256": sample.content_sha256,
                "input_bytes": len(data),
                "tokens": len(encoded.token_ids),
                "encode": encode_measure,
                "decode": decode_measure,
            }
            if candidate is bpe.candidate:
                entry["streaming"] = _stream_measurements(
                    candidate, data, encoded, repetitions, stop, deadline_ns
                )
            observations.append(entry)
    report: dict[str, object] = {
        "schema": "p6.7-observational-performance-v1",
        "source_commit": source_commit,
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.system(),
        "architecture": platform.machine(),
        "processor": platform.processor() or "unavailable",
        "construction_manifest": CONSTRUCTION_MANIFEST.manifest_id,
        "construction_manifest_version": CONSTRUCTION_MANIFEST.version,
        "construction_digests": [
            s.content_sha256 for s in CONSTRUCTION_MANIFEST.samples
        ],
        "evaluation_manifest": EVALUATION_MANIFEST.manifest_id,
        "evaluation_manifest_version": EVALUATION_MANIFEST.version,
        "evaluation_digests": [s.content_sha256 for s in EVALUATION_MANIFEST.samples],
        "structural_fingerprint": structural.report_fingerprint,
        "vocabulary_limit": BENCHMARK_VOCABULARY_LIMIT,
        "bpe_merge_budget": BENCHMARK_BPE_MERGE_BUDGET,
        "max_training_bytes": BENCHMARK_MAX_TRAINING_BYTES,
        "max_samples": MAX_SAMPLES,
        "max_fixture_bytes": MAX_FIXTURE_BYTES,
        "max_run_ns": MAX_RUN_NS,
        "max_report_bytes": MAX_REPORT_BYTES,
        "repetitions": repetitions,
        "chunk_bytes": CHUNK_BYTES,
        "artifact_bytes": len(artifact),
        "artifact_sha256": sha256(artifact).hexdigest(),
        "observations": observations,
        "domains": domain_totals(observations),
    }
    if len(json.dumps(report, sort_keys=True).encode("utf-8")) > MAX_REPORT_BYTES:
        raise PerformanceEvidenceError("report size limit exceeded")
    return report


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "usage: python -m scripts.run_p6_7_performance <40-hex-source-commit>"
        )
    try:
        result = run(source_commit=sys.argv[1])
    except PerformanceEvidenceError as error:
        raise SystemExit(str(error)) from None
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
