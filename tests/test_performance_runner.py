"""Exercise the observational runner's limits and failure exclusion."""

from __future__ import annotations

import json
from threading import Event
from time import monotonic_ns

import pytest
from scripts import run_p6_7_performance as performance


def test_measurement_order_units_and_separate_tracing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = iter((100, 105, 200, 207))
    monkeypatch.setattr(performance, "perf_counter_ns", lambda: next(clock))
    calls: list[bool] = []

    def operation() -> str:
        calls.append(performance.tracemalloc.is_tracing())
        return "complete"

    measured = performance.measure(
        operation,
        "complete",
        repetitions=2,
        cancelled=Event(),
        deadline_ns=monotonic_ns() + 10**9,
    )
    assert measured["trials_ns"] == [5, 7]
    assert measured["median_ns"] == 6
    assert isinstance(measured["traced_peak_bytes"], int)
    assert calls == [False, False, False, True]
    assert not performance.tracemalloc.is_tracing()


def test_failed_observations_never_become_success() -> None:
    deadline = monotonic_ns() + 10**9
    stop = Event()
    with pytest.raises(performance.PerformanceEvidenceError, match="repetition"):
        performance.measure(
            lambda: 1, 1, repetitions=True, cancelled=stop, deadline_ns=deadline
        )
    with pytest.raises(performance.PerformanceEvidenceError, match="warmup"):
        performance.measure(
            lambda: 0, 1, repetitions=1, cancelled=stop, deadline_ns=deadline
        )
    values = iter((1, 0))
    with pytest.raises(performance.PerformanceEvidenceError, match="trial"):
        performance.measure(
            lambda: next(values), 1, repetitions=1, cancelled=stop, deadline_ns=deadline
        )
    stop.set()
    with pytest.raises(performance.PerformanceEvidenceError, match="cancelled"):
        performance.measure(
            lambda: 1, 1, repetitions=1, cancelled=stop, deadline_ns=deadline
        )
    with pytest.raises(performance.PerformanceEvidenceError, match="deadline"):
        performance.measure(
            lambda: 1, 1, repetitions=1, cancelled=Event(), deadline_ns=0
        )
    mid_trial_stop = Event()

    def cancel_after_warmup() -> int:
        if mid_trial_stop.is_set():
            return 1
        mid_trial_stop.set()
        return 1

    with pytest.raises(performance.PerformanceEvidenceError, match="cancelled"):
        performance.measure(
            cancel_after_warmup,
            1,
            repetitions=1,
            cancelled=mid_trial_stop,
            deadline_ns=deadline,
        )


def test_manifest_source_and_report_bounds(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(performance.PerformanceEvidenceError, match="source commit"):
        performance.run(source_commit="invalid")
    with pytest.raises(performance.PerformanceEvidenceError, match="repetition"):
        performance.run(source_commit="0" * 40, repetitions=0)
    stop = Event()
    stop.set()
    with pytest.raises(performance.PerformanceEvidenceError, match="cancelled"):
        performance.run(source_commit="0" * 40, cancelled=stop)
    monkeypatch.setattr(performance, "MAX_SAMPLES", 1)
    with pytest.raises(performance.PerformanceEvidenceError, match="fixture limit"):
        performance.run(source_commit="0" * 40)


def test_streaming_equivalence_failure_is_explicit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        performance, "_stream_finalize", lambda candidate, data: object()
    )
    with pytest.raises(performance.PerformanceEvidenceError, match="chunk equivalence"):
        performance._stream_measurements(
            object(), b"a", object(), 1, Event(), monotonic_ns() + 10**9
        )


def test_throughput_and_domain_units() -> None:
    assert performance.throughput(100, 500_000_000) == 200
    assert performance.throughput(1, 0) is None
    with pytest.raises(performance.PerformanceEvidenceError, match="throughput"):
        performance.throughput(-1, 1)
    observation: dict[str, object] = {
        "algorithm_id": "fixed",
        "domain": "code",
        "input_bytes": 100,
        "tokens": 20,
        "encode": {"median_ns": 500_000_000},
        "decode": {"median_ns": 250_000_000},
    }
    totals = performance.domain_totals([observation])
    assert totals[0]["encode_input_bytes_per_second_floor"] == 200
    assert totals[0]["encode_tokens_per_second_floor"] == 40
    assert totals[0]["decode_tokens_per_second_floor"] == 80
    with pytest.raises(performance.PerformanceEvidenceError, match="observation"):
        performance.domain_totals([{**observation, "encode": "invalid"}])


def test_fixed_fixture_runner_is_complete_and_content_minimizing() -> None:
    report = performance.run(source_commit="0" * 40, repetitions=1)
    assert report["structural_fingerprint"] == performance.STRUCTURAL_FINGERPRINT
    assert report["artifact_bytes"] == 10101
    assert len(report["observations"]) == 51
    assert len(report["domains"]) == 24
    serialized = json.dumps(report)
    assert "def verify(record)" not in serialized
    assert "The defensive analyst" not in serialized
    bpe = [
        item
        for item in report["observations"]
        if item["algorithm_id"] == "experimental-byte-bpe-v1"
    ]
    assert len(bpe) == 17
    assert all("finalization" in item["streaming"] for item in bpe)


def test_structural_identity_and_report_limit_are_binding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(performance, "STRUCTURAL_FINGERPRINT", "0" * 64)
    with pytest.raises(performance.PerformanceEvidenceError, match="structural"):
        performance.run(source_commit="0" * 40, repetitions=1)
    monkeypatch.setattr(
        performance,
        "STRUCTURAL_FINGERPRINT",
        "f979122b76acffb434a536fd8e834fa9a1ce5d92bc1bb8cceda737e42a638b32",
    )
    monkeypatch.setattr(performance, "MAX_REPORT_BYTES", 1)
    with pytest.raises(performance.PerformanceEvidenceError, match="report size"):
        performance.run(source_commit="0" * 40, repetitions=1)
