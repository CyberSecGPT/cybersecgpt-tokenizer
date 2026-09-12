"""Bounded streaming ingestion with exact byte-BPE chunk equivalence."""

from __future__ import annotations

from enum import StrEnum
from time import monotonic_ns
from typing import Final, NoReturn

from cybersecgpt.tokenizer.byte_bpe import ByteBpeCandidate
from cybersecgpt.tokenizer.contracts import (
    MAX_TEXT_BYTES,
    MAX_TOKEN_COUNT,
    EncodeRequest,
    EncodeResult,
    TokenizerContractError,
)

MAX_STREAM_CHUNK_BYTES: Final = 1024 * 1024
MAX_STREAM_CHUNKS: Final = 1024 * 1024
MAX_DEADLINE_NS: Final = (1 << 63) - 1


class StreamingState(StrEnum):
    """Stable lifecycle states for one streaming encoder."""

    OPEN = "open"
    FINALIZED = "finalized"
    CANCELLED = "cancelled"
    FAILED = "failed"


class StreamingStateError(TokenizerContractError):
    """Raised when an operation is invalid for the current stream state."""


class StreamingDeadlineError(TokenizerContractError):
    """Raised when the stream's monotonic deadline has expired."""


class ByteBpeStreamingEncoder:
    """Collect bounded byte chunks and encode exactly once at finalization.

    The experimental ordered BPE merge program has no proven finite safe
    progressive-emission frontier. This class therefore emits no partial tokens.
    Instances are single-consumer state machines and must not be used concurrently.
    """

    __slots__ = (
        "_add_special_tokens",
        "_buffer",
        "_candidate",
        "_chunk_count",
        "_deadline_ns",
        "_max_tokens",
        "_state",
    )

    def __init__(
        self,
        candidate: ByteBpeCandidate,
        *,
        max_tokens: int = MAX_TOKEN_COUNT,
        add_special_tokens: bool = False,
        deadline_ns: int | None = None,
    ) -> None:
        if not 0 <= max_tokens <= MAX_TOKEN_COUNT:
            raise TokenizerContractError("max_tokens is outside the supported range")
        if deadline_ns is not None and (
            isinstance(deadline_ns, bool)
            or not isinstance(deadline_ns, int)
            or not 0 <= deadline_ns <= MAX_DEADLINE_NS
        ):
            raise TokenizerContractError("deadline_ns is outside the supported range")
        self._candidate = candidate
        self._max_tokens = max_tokens
        self._add_special_tokens = add_special_tokens
        self._deadline_ns = deadline_ns
        self._buffer = bytearray()
        self._chunk_count = 0
        self._state = StreamingState.OPEN
        self._check_deadline()

    @property
    def state(self) -> StreamingState:
        """Return the current lifecycle state without exposing buffered content."""

        return self._state

    @property
    def buffered_byte_count(self) -> int:
        """Return the retained byte count, never the untrusted content itself."""

        return len(self._buffer)

    @property
    def chunk_count(self) -> int:
        """Return the number of admitted chunk calls."""

        return self._chunk_count

    def _require_open(self) -> None:
        if self._state is not StreamingState.OPEN:
            raise StreamingStateError(f"stream is already {self._state.value}")

    def _fail(self, error: Exception) -> NoReturn:
        self._buffer.clear()
        self._state = StreamingState.FAILED
        raise error

    def _check_deadline(self) -> None:
        if self._deadline_ns is not None and monotonic_ns() >= self._deadline_ns:
            self._fail(StreamingDeadlineError("stream deadline expired"))

    def push(self, chunk: bytes) -> None:
        """Admit one immutable byte chunk without emitting tokens."""

        self._require_open()
        self._check_deadline()
        if type(chunk) is not bytes:
            self._fail(TokenizerContractError("stream chunk must be immutable bytes"))
        if len(chunk) > MAX_STREAM_CHUNK_BYTES:
            self._fail(TokenizerContractError("stream chunk exceeds the byte limit"))
        if self._chunk_count >= MAX_STREAM_CHUNKS:
            self._fail(TokenizerContractError("stream exceeds the chunk-count limit"))
        if len(self._buffer) + len(chunk) > MAX_TEXT_BYTES:
            self._fail(
                TokenizerContractError("stream exceeds the aggregate byte limit")
            )
        self._buffer.extend(chunk)
        self._chunk_count += 1

    def cancel(self) -> None:
        """Discard buffered input and enter the terminal cancelled state."""

        self._require_open()
        self._buffer.clear()
        self._state = StreamingState.CANCELLED

    def finish(self) -> EncodeResult:
        """Validate strict UTF-8 and return the exact one-shot BPE result."""

        self._require_open()
        self._check_deadline()
        try:
            text = bytes(self._buffer).decode("utf-8", errors="strict")
            request = EncodeRequest(
                text=text,
                max_tokens=self._max_tokens,
                add_special_tokens=self._add_special_tokens,
            )
            result = self._candidate.encode(request)
        except UnicodeDecodeError:
            self._fail(
                TokenizerContractError(
                    "stream is not a complete valid UTF-8 byte sequence"
                )
            )
        except Exception as error:
            self._fail(error)
        self._check_deadline()
        self._buffer.clear()
        self._state = StreamingState.FINALIZED
        return result
