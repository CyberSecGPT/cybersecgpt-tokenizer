"""Accepted prospective Tokenizer v1 semantics over a fixed byte-BPE candidate."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from hmac import compare_digest
from time import monotonic_ns
from typing import Final, NoReturn

from cybersecgpt.tokenizer.byte_bpe import ByteBpeCandidate
from cybersecgpt.tokenizer.contracts import (
    MAX_TEXT_BYTES,
    MAX_TOKEN_COUNT,
    DecodeRequest,
    EncodeRequest,
    FinishStatus,
    SpecialToken,
    TokenizerContractError,
    TokenizerDescriptor,
)
from cybersecgpt.tokenizer.streaming import (
    MAX_DEADLINE_NS,
    MAX_STREAM_CHUNK_BYTES,
    MAX_STREAM_CHUNKS,
    StreamingDeadlineError,
    StreamingState,
    StreamingStateError,
)

V1_SEMANTIC_PROFILE: Final = "cybersecgpt-tokenizer-v1-semantics-1"
V1_ORDINARY_VOCABULARY_SIZE: Final = 512
V1_BOS_ID: Final = 512
V1_EOS_ID: Final = 513
V1_PAD_ID: Final = 514
V1_VOCABULARY_SIZE: Final = 515
_SPECIALS: Final = (
    SpecialToken("bos", V1_BOS_ID),
    SpecialToken("eos", V1_EOS_ID),
    SpecialToken("pad", V1_PAD_ID),
)
_ROLES: Final = {token.token_id: token.role for token in _SPECIALS}
_RENDERINGS: Final = {
    V1_BOS_ID: "<|bos|>",
    V1_EOS_ID: "<|eos|>",
    V1_PAD_ID: "<|pad|>",
}


class V1SpecialDecodeMode(StrEnum):
    """Explicit handling for non-authorizing special IDs during decode."""

    REJECT = "reject"
    PRESERVE = "preserve"
    RENDER = "render"


@dataclass(frozen=True, slots=True)
class V1EncodeRequest:
    """Typed prospective v1 encoding request with explicit optional truncation."""

    text: str
    max_tokens: int | None = None
    add_bos: bool = False
    add_eos: bool = False
    return_offsets: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TokenizerContractError("text must be Unicode text")
        try:
            encoded = self.text.encode("utf-8", errors="strict")
        except UnicodeEncodeError as error:
            raise TokenizerContractError("text must be valid strict UTF-8") from error
        if len(encoded) > MAX_TEXT_BYTES:
            raise TokenizerContractError("text exceeds the encoded byte limit")
        if self.max_tokens is not None and (
            isinstance(self.max_tokens, bool)
            or not isinstance(self.max_tokens, int)
            or not 0 <= self.max_tokens <= MAX_TOKEN_COUNT
        ):
            raise TokenizerContractError("max_tokens is outside the supported range")
        for value, name in (
            (self.add_bos, "add_bos"),
            (self.add_eos, "add_eos"),
            (self.return_offsets, "return_offsets"),
        ):
            if not isinstance(value, bool):
                raise TokenizerContractError(f"{name} must be boolean")


@dataclass(frozen=True, slots=True)
class V1TokenSpan:
    """One emitted ID and its optional canonical source span."""

    token_id: int
    start_byte: int | None
    end_byte: int | None
    start_scalar: int | None
    end_scalar: int | None
    special_role: str | None = None


@dataclass(frozen=True, slots=True)
class V1EncodeResult:
    """Prospective v1 IDs, identity, completion, and optional offsets."""

    token_ids: tuple[int, ...]
    tokenizer_fingerprint: str
    finish_status: FinishStatus
    spans: tuple[V1TokenSpan, ...]
    first_omitted_byte: int | None


@dataclass(frozen=True, slots=True)
class V1DecodeRequest:
    """Typed decode request with explicit special-token behavior."""

    token_ids: tuple[int, ...]
    special_mode: V1SpecialDecodeMode = V1SpecialDecodeMode.REJECT

    def __post_init__(self) -> None:
        if not isinstance(self.token_ids, tuple) or any(
            isinstance(item, bool) or not isinstance(item, int)
            for item in self.token_ids
        ):
            raise TokenizerContractError("token_ids must be an integer tuple")
        if len(self.token_ids) > MAX_TOKEN_COUNT:
            raise TokenizerContractError("token_ids exceeds the token-count limit")
        if any(item < 0 or item >= V1_VOCABULARY_SIZE for item in self.token_ids):
            raise TokenizerContractError("token_ids contains an invalid v1 ID")
        if not isinstance(self.special_mode, V1SpecialDecodeMode):
            raise TokenizerContractError("special_mode is invalid")


@dataclass(frozen=True, slots=True)
class V1DecodedSegment:
    """Decoded untrusted text or a preserved non-authorizing special role."""

    kind: str
    value: str


@dataclass(frozen=True, slots=True)
class V1DecodeResult:
    """Decoded result; preserve mode exposes typed segments instead of text."""

    text: str | None
    segments: tuple[V1DecodedSegment, ...]
    tokenizer_fingerprint: str
    finish_status: FinishStatus = FinishStatus.COMPLETED


def _behavior_fingerprint(candidate_fingerprint: str) -> str:
    canonical = "\n".join(
        (
            V1_SEMANTIC_PROFILE,
            candidate_fingerprint,
            "algorithm:prospective-byte-bpe-v1",
            "artifact-format:unapproved",
            "strict-utf8-no-replacement",
            "normalization:none",
            "pretokenization:utf8-whole-sequence",
            "ordinary-ids:0-511",
            "special:bos:512:<|bos|>:explicit",
            "special:eos:513:<|eos|>:complete-explicit",
            "special:pad:514:<|pad|>:never-encode",
            "truncation:utf8-scalar-boundary-no-eos",
            "offsets:utf8-byte-half-open",
            "compatibility:exact-fingerprint",
        )
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


def _scalar_boundaries(text: str) -> dict[int, int]:
    boundaries = {0: 0}
    byte_offset = 0
    for scalar_offset, character in enumerate(text, 1):
        byte_offset += len(character.encode("utf-8"))
        boundaries[byte_offset] = scalar_offset
    return boundaries


@dataclass(frozen=True, slots=True)
class TokenizerV1SemanticCandidate:
    """Immutable prospective v1 behavior; not a trained or approved artifact."""

    candidate: ByteBpeCandidate

    def __post_init__(self) -> None:
        if (
            not isinstance(self.candidate, ByteBpeCandidate)
            or len(self.candidate.tokens) != V1_ORDINARY_VOCABULARY_SIZE
        ):
            raise TokenizerContractError(
                "Tokenizer v1 semantic candidate requires exactly 512 ordinary IDs"
            )

    @property
    def descriptor(self) -> TokenizerDescriptor:
        return TokenizerDescriptor(
            tokenizer_id="prospective-cybersecgpt-tokenizer-v1",
            contract_version="1",
            algorithm_id="prospective-byte-bpe-v1",
            artifact_format_version="unapproved",
            normalization_profile="none",
            pretokenization_profile="utf8-whole-sequence",
            vocabulary_size=V1_VOCABULARY_SIZE,
            fingerprint=_behavior_fingerprint(self.candidate.descriptor.fingerprint),
            special_tokens=_SPECIALS,
        )

    def encode(self, request: V1EncodeRequest) -> V1EncodeResult:
        ordinary_result = self.candidate.encode(EncodeRequest(request.text))
        ordinary = ordinary_result.token_ids
        encoded = request.text.encode("utf-8")
        boundaries = _scalar_boundaries(request.text)
        full_size = len(ordinary) + int(request.add_bos) + int(request.add_eos)
        if request.max_tokens is None and (
            ordinary_result.finish_status is FinishStatus.TRUNCATED
            or full_size > MAX_TOKEN_COUNT
        ):
            raise TokenizerContractError(
                "encoded token count exceeds the global output limit"
            )
        limit = full_size if request.max_tokens is None else request.max_tokens
        completed = (
            ordinary_result.finish_status is FinishStatus.COMPLETED
            and full_size <= limit
        )
        include_bos = request.add_bos and limit > 0
        ordinary_budget = max(0, limit - int(include_bos))
        ordinary_count = (
            len(ordinary) if completed else min(len(ordinary), ordinary_budget)
        )
        byte_ends: list[int] = []
        byte_offset = 0
        for token_id in ordinary:
            byte_offset += len(self.candidate.tokens[token_id])
            byte_ends.append(byte_offset)
        if not completed:
            while ordinary_count and byte_ends[ordinary_count - 1] not in boundaries:
                ordinary_count -= 1
        selected = ordinary[:ordinary_count]
        ids = ((V1_BOS_ID,) if include_bos else ()) + selected
        include_eos = completed and request.add_eos
        if include_eos:
            ids += (V1_EOS_ID,)
        status = FinishStatus.COMPLETED if completed else FinishStatus.TRUNCATED
        first_omitted = (
            None
            if completed
            else (byte_ends[ordinary_count - 1] if ordinary_count else 0)
        )
        spans: list[V1TokenSpan] = []
        if request.return_offsets:
            if include_bos:
                spans.append(V1TokenSpan(V1_BOS_ID, 0, 0, 0, 0, "bos"))
            start = 0
            for token_id, end in zip(selected, byte_ends, strict=False):
                start_scalar = boundaries.get(start)
                end_scalar = boundaries.get(end)
                if start_scalar is None or end_scalar is None:
                    start_scalar = None
                    end_scalar = None
                spans.append(
                    V1TokenSpan(
                        token_id,
                        start,
                        end,
                        start_scalar,
                        end_scalar,
                    )
                )
                start = end
            if include_eos:
                scalar_end = len(request.text)
                spans.append(
                    V1TokenSpan(
                        V1_EOS_ID,
                        len(encoded),
                        len(encoded),
                        scalar_end,
                        scalar_end,
                        "eos",
                    )
                )
        return V1EncodeResult(
            ids,
            self.descriptor.fingerprint,
            status,
            tuple(spans),
            first_omitted,
        )

    def decode(self, request: V1DecodeRequest) -> V1DecodeResult:
        segments: list[V1DecodedSegment] = []
        ordinary: list[int] = []

        def flush() -> None:
            if not ordinary:
                return
            decoded = self.candidate.decode(DecodeRequest(tuple(ordinary))).text
            segments.append(V1DecodedSegment("text", decoded))
            ordinary.clear()

        for token_id in request.token_ids:
            if token_id < V1_ORDINARY_VOCABULARY_SIZE:
                ordinary.append(token_id)
                continue
            if request.special_mode is V1SpecialDecodeMode.REJECT:
                raise TokenizerContractError("special token rejected by decode mode")
            flush()
            value = (
                _ROLES[token_id]
                if request.special_mode is V1SpecialDecodeMode.PRESERVE
                else _RENDERINGS[token_id]
            )
            kind = (
                "special"
                if request.special_mode is V1SpecialDecodeMode.PRESERVE
                else "text"
            )
            segments.append(V1DecodedSegment(kind, value))
        flush()
        text = (
            None
            if request.special_mode is V1SpecialDecodeMode.PRESERVE
            else "".join(segment.value for segment in segments)
        )
        return V1DecodeResult(text, tuple(segments), self.descriptor.fingerprint)

    def require_compatible_fingerprint(self, fingerprint: str) -> None:
        if (
            not isinstance(fingerprint, str)
            or len(fingerprint) != 64
            or any(character not in "0123456789abcdef" for character in fingerprint)
            or not compare_digest(fingerprint, self.descriptor.fingerprint)
        ):
            raise TokenizerContractError("incompatible Tokenizer v1 fingerprint")


class TokenizerV1StreamingEncoder:
    """Bounded buffered streaming with exact prospective v1 finalization."""

    __slots__ = (
        "_buffer",
        "_chunk_count",
        "_deadline_ns",
        "_request",
        "_state",
        "_tokenizer",
    )

    def __init__(
        self,
        tokenizer: TokenizerV1SemanticCandidate,
        *,
        max_tokens: int | None = None,
        add_bos: bool = False,
        add_eos: bool = False,
        return_offsets: bool = False,
        deadline_ns: int | None = None,
    ) -> None:
        if not isinstance(tokenizer, TokenizerV1SemanticCandidate):
            raise TokenizerContractError(
                "tokenizer must implement Tokenizer v1 semantics"
            )
        self._request = V1EncodeRequest(
            "",
            max_tokens=max_tokens,
            add_bos=add_bos,
            add_eos=add_eos,
            return_offsets=return_offsets,
        )
        if deadline_ns is not None and (
            isinstance(deadline_ns, bool)
            or not isinstance(deadline_ns, int)
            or not 0 <= deadline_ns <= MAX_DEADLINE_NS
        ):
            raise TokenizerContractError("deadline_ns is outside the supported range")
        self._tokenizer = tokenizer
        self._deadline_ns = deadline_ns
        self._buffer = bytearray()
        self._chunk_count = 0
        self._state = StreamingState.OPEN
        self._check_deadline()

    @property
    def state(self) -> StreamingState:
        return self._state

    @property
    def buffered_byte_count(self) -> int:
        return len(self._buffer)

    @property
    def chunk_count(self) -> int:
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
        self._require_open()
        self._buffer.clear()
        self._state = StreamingState.CANCELLED

    def finish(self) -> V1EncodeResult:
        self._require_open()
        self._check_deadline()
        try:
            text = bytes(self._buffer).decode("utf-8", errors="strict")
            request = V1EncodeRequest(
                text,
                max_tokens=self._request.max_tokens,
                add_bos=self._request.add_bos,
                add_eos=self._request.add_eos,
                return_offsets=self._request.return_offsets,
            )
            result = self._tokenizer.encode(request)
        except UnicodeDecodeError:
            self._fail(TokenizerContractError("stream is not complete strict UTF-8"))
        except Exception as error:
            self._fail(error)
        self._check_deadline()
        self._buffer.clear()
        self._state = StreamingState.FINALIZED
        return result
