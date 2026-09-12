"""P6.5 streaming lifecycle and independent chunk-equivalence evidence."""

from __future__ import annotations

from collections.abc import Iterable

import pytest

import cybersecgpt.tokenizer.streaming as streaming_module
from cybersecgpt.tokenizer import (
    MAX_STREAM_CHUNK_BYTES,
    MAX_STREAM_CHUNKS,
    BpeMerge,
    ByteBpeCandidate,
    ByteBpeStreamingEncoder,
    EncodeRequest,
    FinishStatus,
    StreamingDeadlineError,
    StreamingState,
    StreamingStateError,
    TokenizerContractError,
)


def _candidate() -> ByteBpeCandidate:
    tokens = tuple(bytes((value,)) for value in range(256)) + (
        b"ab",
        b"abc",
        b" j",
    )
    return ByteBpeCandidate(
        tokens,
        (
            BpeMerge(ord("a"), ord("b"), 256),
            BpeMerge(256, ord("c"), 257),
            BpeMerge(ord(" "), 106, 258),
        ),
    )


def _stream_result(chunks: Iterable[bytes], *, max_tokens: int = 4 * 1024 * 1024):
    stream = ByteBpeStreamingEncoder(_candidate(), max_tokens=max_tokens)
    for chunk in chunks:
        assert stream.push(chunk) is None
    result = stream.finish()
    assert stream.state is StreamingState.FINALIZED
    assert stream.buffered_byte_count == 0
    return result


@pytest.mark.parametrize(
    "text",
    (
        "",
        "abc abc",
        "Ka jingïada e\u0301",
        "if alert: quarantine(host)",
        "event=blocked src=192.0.2.7",
        '{"cve":"CVE-2026-1234"}',
        "sha256=0123456789abcdef",
        "Defensive analysis found no executable payload.",
    ),
)
def test_every_two_way_split_and_single_byte_chunks_match_one_shot(text: str) -> None:
    candidate = _candidate()
    encoded = text.encode()
    expected = candidate.encode(EncodeRequest(text))
    assert _stream_result((encoded,)) == expected
    assert _stream_result(bytes((value,)) for value in encoded) == expected
    for boundary in range(len(encoded) + 1):
        assert _stream_result((encoded[:boundary], encoded[boundary:])) == expected


def test_empty_chunks_count_and_do_not_change_output() -> None:
    stream = ByteBpeStreamingEncoder(_candidate())
    stream.push(b"")
    stream.push(b"abc")
    stream.push(b"")
    assert stream.chunk_count == 3
    assert stream.buffered_byte_count == 3
    assert stream.finish() == _candidate().encode(EncodeRequest("abc"))


@pytest.mark.parametrize("limit", (0, 1, 2, 3, 4))
def test_truncated_results_are_chunk_equivalent(limit: int) -> None:
    text = "abc abc"
    expected = _candidate().encode(EncodeRequest(text, max_tokens=limit))
    assert _stream_result((b"a", b"bc ", b"abc"), max_tokens=limit) == expected
    assert expected.finish_status is (
        FinishStatus.COMPLETED if limit >= 3 else FinishStatus.TRUNCATED
    )


@pytest.mark.parametrize("invalid", (b"\x80", b"\xf0\x9f", b"\xc0\xaf"))
def test_invalid_or_incomplete_utf8_fails_and_discards_buffer(invalid: bytes) -> None:
    stream = ByteBpeStreamingEncoder(_candidate())
    stream.push(invalid)
    with pytest.raises(TokenizerContractError, match="complete valid UTF-8"):
        stream.finish()
    assert stream.state is StreamingState.FAILED
    assert stream.buffered_byte_count == 0
    with pytest.raises(StreamingStateError, match="already failed"):
        stream.finish()


@pytest.mark.parametrize("invalid", (bytearray(b"a"), memoryview(b"a"), "a"))
def test_only_immutable_bytes_chunks_are_accepted(invalid: object) -> None:
    stream = ByteBpeStreamingEncoder(_candidate())
    with pytest.raises(TokenizerContractError, match="immutable bytes"):
        stream.push(invalid)  # type: ignore[arg-type]
    assert stream.state is StreamingState.FAILED


def test_chunk_size_failure_is_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(streaming_module, "MAX_STREAM_CHUNK_BYTES", 2)
    stream = ByteBpeStreamingEncoder(_candidate())
    with pytest.raises(TokenizerContractError, match="chunk exceeds"):
        stream.push(b"abc")
    assert stream.state is StreamingState.FAILED
    assert stream.chunk_count == 0


def test_aggregate_size_failure_is_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(streaming_module, "MAX_TEXT_BYTES", 2)
    stream = ByteBpeStreamingEncoder(_candidate())
    stream.push(b"ab")
    with pytest.raises(TokenizerContractError, match="aggregate"):
        stream.push(b"c")
    assert stream.state is StreamingState.FAILED
    assert stream.buffered_byte_count == 0


def test_chunk_count_failure_counts_empty_chunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(streaming_module, "MAX_STREAM_CHUNKS", 2)
    stream = ByteBpeStreamingEncoder(_candidate())
    stream.push(b"")
    stream.push(b"a")
    with pytest.raises(TokenizerContractError, match="chunk-count"):
        stream.push(b"")
    assert stream.state is StreamingState.FAILED
    assert stream.chunk_count == 2


def test_cancel_discards_content_and_all_terminal_operations_fail() -> None:
    stream = ByteBpeStreamingEncoder(_candidate())
    stream.push(b"secret-like untrusted content")
    stream.cancel()
    assert stream.state is StreamingState.CANCELLED
    assert stream.buffered_byte_count == 0
    for operation in (lambda: stream.push(b"x"), stream.finish, stream.cancel):
        with pytest.raises(StreamingStateError, match="already cancelled"):
            operation()


def test_cancel_before_input() -> None:
    stream = ByteBpeStreamingEncoder(_candidate())
    stream.cancel()
    assert stream.state is StreamingState.CANCELLED
    assert stream.chunk_count == 0


@pytest.mark.parametrize("deadline", (-1, 1 << 63, True, 1.5, "1"))
def test_deadline_validation(deadline: object) -> None:
    with pytest.raises(TokenizerContractError, match="deadline_ns"):
        ByteBpeStreamingEncoder(_candidate(), deadline_ns=deadline)  # type: ignore[arg-type]


@pytest.mark.parametrize("max_tokens", (-1, 4 * 1024 * 1024 + 1))
def test_max_tokens_validation(max_tokens: int) -> None:
    with pytest.raises(TokenizerContractError, match="max_tokens"):
        ByteBpeStreamingEncoder(_candidate(), max_tokens=max_tokens)


def test_deadline_expiry_at_construction(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(streaming_module, "monotonic_ns", lambda: 10)
    with pytest.raises(StreamingDeadlineError, match="expired"):
        ByteBpeStreamingEncoder(_candidate(), deadline_ns=10)


def test_deadline_expiry_before_chunk_discards_buffer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = 1
    monkeypatch.setattr(streaming_module, "monotonic_ns", lambda: now)
    stream = ByteBpeStreamingEncoder(_candidate(), deadline_ns=3)
    stream.push(b"a")
    now = 3
    with pytest.raises(StreamingDeadlineError, match="expired"):
        stream.push(b"b")
    assert stream.state is StreamingState.FAILED
    assert stream.buffered_byte_count == 0


def test_deadline_expiry_before_finish_discards_buffer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = 1
    monkeypatch.setattr(streaming_module, "monotonic_ns", lambda: now)
    stream = ByteBpeStreamingEncoder(_candidate(), deadline_ns=3)
    stream.push(b"abc")
    now = 4
    with pytest.raises(StreamingDeadlineError, match="expired"):
        stream.finish()
    assert stream.state is StreamingState.FAILED
    assert stream.buffered_byte_count == 0


def test_deadline_expiry_during_finish_cannot_publish_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    readings = iter((1, 1, 1, 4))
    monkeypatch.setattr(streaming_module, "monotonic_ns", lambda: next(readings))
    stream = ByteBpeStreamingEncoder(_candidate(), deadline_ns=3)
    stream.push(b"abc")
    with pytest.raises(StreamingDeadlineError, match="expired"):
        stream.finish()
    assert stream.state is StreamingState.FAILED
    assert stream.buffered_byte_count == 0


def test_special_token_failure_is_terminal() -> None:
    stream = ByteBpeStreamingEncoder(_candidate(), add_special_tokens=True)
    stream.push(b"abc")
    with pytest.raises(TokenizerContractError, match="no special-token allocation"):
        stream.finish()
    assert stream.state is StreamingState.FAILED
    assert stream.buffered_byte_count == 0


def test_public_limits_match_the_accepted_gate() -> None:
    assert MAX_STREAM_CHUNK_BYTES == 1024 * 1024
    assert MAX_STREAM_CHUNKS == 1024 * 1024
