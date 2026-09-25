"""Accepted prospective Tokenizer v1 semantic-profile evidence."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

import cybersecgpt.tokenizer.v1_semantics as v1_module
from cybersecgpt.tokenizer import (
    V1_BOS_ID,
    V1_EOS_ID,
    V1_PAD_ID,
    V1_VOCABULARY_SIZE,
    BpeMerge,
    ByteBpeCandidate,
    FinishStatus,
    StreamingDeadlineError,
    StreamingState,
    StreamingStateError,
    TokenizerContractError,
    TokenizerV1SemanticCandidate,
    TokenizerV1StreamingEncoder,
    V1DecodeRequest,
    V1EncodeRequest,
    V1SpecialDecodeMode,
)


def _candidate(size: int = 512) -> ByteBpeCandidate:
    tokens = [bytes((value,)) for value in range(256)]
    merges = []
    for value in range(size - 256):
        token_id = len(tokens)
        tokens.append(b"\x00" + bytes((value,)))
        merges.append(BpeMerge(0, value, token_id))
    return ByteBpeCandidate(tuple(tokens), tuple(merges))


@pytest.fixture
def tokenizer() -> TokenizerV1SemanticCandidate:
    return TokenizerV1SemanticCandidate(_candidate())


def test_descriptor_binds_candidate_and_fixed_semantics(
    tokenizer: TokenizerV1SemanticCandidate,
) -> None:
    descriptor = tokenizer.descriptor
    assert descriptor.tokenizer_id == "prospective-cybersecgpt-tokenizer-v1"
    assert descriptor.contract_version == "1"
    assert descriptor.algorithm_id == "prospective-byte-bpe-v1"
    assert descriptor.artifact_format_version == "unapproved"
    assert descriptor.normalization_profile == "none"
    assert descriptor.pretokenization_profile == "utf8-whole-sequence"
    assert descriptor.vocabulary_size == V1_VOCABULARY_SIZE
    assert [(item.role, item.token_id) for item in descriptor.special_tokens] == [
        ("bos", V1_BOS_ID),
        ("eos", V1_EOS_ID),
        ("pad", V1_PAD_ID),
    ]
    assert len(descriptor.fingerprint) == 64
    assert descriptor.fingerprint == tokenizer.descriptor.fingerprint
    changed = TokenizerV1SemanticCandidate(
        ByteBpeCandidate(
            _candidate().tokens[:-2] + (b"\x01\x01", b"\x01\x02"),
            _candidate().merges[:-2] + (BpeMerge(1, 1, 510), BpeMerge(1, 2, 511)),
        )
    )
    assert changed.descriptor.fingerprint != descriptor.fingerprint


def test_candidate_requires_exact_ordinary_vocabulary() -> None:
    with pytest.raises(TokenizerContractError, match="exactly 512"):
        TokenizerV1SemanticCandidate(_candidate(511))
    with pytest.raises(TokenizerContractError, match="exactly 512"):
        TokenizerV1SemanticCandidate(object())  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid", (b"text", 1, None))
def test_encode_request_requires_text(invalid: object) -> None:
    with pytest.raises(TokenizerContractError, match="Unicode text"):
        V1EncodeRequest(invalid)  # type: ignore[arg-type]


def test_encode_request_bounds_encoded_text(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(v1_module, "MAX_TEXT_BYTES", 1)
    with pytest.raises(TokenizerContractError, match="encoded byte limit"):
        V1EncodeRequest("é")


def test_encode_request_rejects_unpaired_surrogate() -> None:
    with pytest.raises(TokenizerContractError, match="strict UTF-8"):
        V1EncodeRequest("\ud800")


@pytest.mark.parametrize("invalid", (-1, 4_194_305, True, 1.5, "1"))
def test_encode_request_validates_max_tokens(invalid: object) -> None:
    with pytest.raises(TokenizerContractError, match="max_tokens"):
        V1EncodeRequest("", max_tokens=invalid)  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ("add_bos", "add_eos", "return_offsets"))
def test_encode_request_requires_boolean_flags(field: str) -> None:
    values = {field: 1}
    with pytest.raises(TokenizerContractError, match=field):
        V1EncodeRequest("", **values)  # type: ignore[arg-type]


def test_complete_encode_has_explicit_specials_and_offsets(
    tokenizer: TokenizerV1SemanticCandidate,
) -> None:
    result = tokenizer.encode(
        V1EncodeRequest("Aé", add_bos=True, add_eos=True, return_offsets=True)
    )
    assert result.token_ids == (V1_BOS_ID, 65, 195, 169, V1_EOS_ID)
    assert result.finish_status is FinishStatus.COMPLETED
    assert result.first_omitted_byte is None
    assert [span.special_role for span in result.spans] == [
        "bos",
        None,
        None,
        None,
        "eos",
    ]
    assert [(span.start_byte, span.end_byte) for span in result.spans] == [
        (0, 0),
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 3),
    ]
    assert [(span.start_scalar, span.end_scalar) for span in result.spans] == [
        (0, 0),
        (0, 1),
        (None, None),
        (None, None),
        (2, 2),
    ]
    assert tokenizer.encode(V1EncodeRequest("A")).spans == ()
    assert (
        tokenizer.encode(V1EncodeRequest("A", return_offsets=True)).spans[0].token_id
        == 65
    )


def test_literal_special_rendering_is_ordinary_text(
    tokenizer: TokenizerV1SemanticCandidate,
) -> None:
    encoded = tokenizer.encode(V1EncodeRequest("<|bos|>"))
    assert all(token_id < 512 for token_id in encoded.token_ids)
    assert tokenizer.decode(V1DecodeRequest(encoded.token_ids)).text == "<|bos|>"


@pytest.mark.parametrize(
    ("limit", "expected_ids", "first_omitted"),
    (
        (0, (), 0),
        (1, (V1_BOS_ID,), 0),
        (2, (V1_BOS_ID, 65), 1),
        (3, (V1_BOS_ID, 65), 1),
        (4, (V1_BOS_ID, 65, 195, 169), 3),
    ),
)
def test_truncation_backs_up_to_utf8_boundary_and_omits_eos(
    tokenizer: TokenizerV1SemanticCandidate,
    limit: int,
    expected_ids: tuple[int, ...],
    first_omitted: int,
) -> None:
    result = tokenizer.encode(
        V1EncodeRequest("Aé", max_tokens=limit, add_bos=True, add_eos=True)
    )
    assert result.token_ids == expected_ids
    assert result.finish_status is FinishStatus.TRUNCATED
    assert result.first_omitted_byte == first_omitted
    assert V1_EOS_ID not in result.token_ids


def test_exact_limit_is_complete(tokenizer: TokenizerV1SemanticCandidate) -> None:
    result = tokenizer.encode(
        V1EncodeRequest("A", max_tokens=3, add_bos=True, add_eos=True)
    )
    assert result.finish_status is FinishStatus.COMPLETED
    assert result.token_ids == (V1_BOS_ID, 65, V1_EOS_ID)


def test_unbounded_encode_rejects_global_output_overflow(
    tokenizer: TokenizerV1SemanticCandidate, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(v1_module, "MAX_TOKEN_COUNT", 1)
    with pytest.raises(TokenizerContractError, match="global output limit"):
        tokenizer.encode(V1EncodeRequest("A", add_bos=True))


def test_unbounded_encode_rejects_candidate_resource_truncation(
    tokenizer: TokenizerV1SemanticCandidate, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = ByteBpeCandidate.encode

    def truncated(self: ByteBpeCandidate, request: object):
        result = original(self, request)  # type: ignore[arg-type]
        return type(result)(
            result.token_ids, result.tokenizer_fingerprint, FinishStatus.TRUNCATED
        )

    monkeypatch.setattr(ByteBpeCandidate, "encode", truncated)
    with pytest.raises(TokenizerContractError, match="global output limit"):
        tokenizer.encode(V1EncodeRequest("A"))


def test_explicit_limit_remains_truncated_when_candidate_hits_resource_ceiling(
    tokenizer: TokenizerV1SemanticCandidate, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = ByteBpeCandidate.encode

    def truncated(self: ByteBpeCandidate, request: object):
        result = original(self, request)  # type: ignore[arg-type]
        return type(result)(
            result.token_ids, result.tokenizer_fingerprint, FinishStatus.TRUNCATED
        )

    monkeypatch.setattr(ByteBpeCandidate, "encode", truncated)
    result = tokenizer.encode(V1EncodeRequest("A", max_tokens=1))
    assert result.finish_status is FinishStatus.TRUNCATED


@pytest.mark.parametrize(
    "invalid",
    ([1], (True,), ("1",), (-1,), (V1_VOCABULARY_SIZE,)),
)
def test_decode_request_validates_ids(invalid: object) -> None:
    with pytest.raises(TokenizerContractError):
        V1DecodeRequest(invalid)  # type: ignore[arg-type]


def test_decode_request_bounds_count(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(v1_module, "MAX_TOKEN_COUNT", 1)
    with pytest.raises(TokenizerContractError, match="token-count"):
        V1DecodeRequest((1, 2))


def test_decode_request_requires_enum() -> None:
    with pytest.raises(TokenizerContractError, match="special_mode"):
        V1DecodeRequest((), "reject")  # type: ignore[arg-type]


def test_decode_modes_are_explicit_and_fail_closed(
    tokenizer: TokenizerV1SemanticCandidate,
) -> None:
    ids = (65, V1_BOS_ID, 66, V1_EOS_ID, V1_PAD_ID)
    with pytest.raises(TokenizerContractError, match="special token rejected"):
        tokenizer.decode(V1DecodeRequest(ids))
    preserved = tokenizer.decode(V1DecodeRequest(ids, V1SpecialDecodeMode.PRESERVE))
    assert preserved.text is None
    assert [(item.kind, item.value) for item in preserved.segments] == [
        ("text", "A"),
        ("special", "bos"),
        ("text", "B"),
        ("special", "eos"),
        ("special", "pad"),
    ]
    rendered = tokenizer.decode(V1DecodeRequest(ids, V1SpecialDecodeMode.RENDER))
    assert rendered.text == "A<|bos|>B<|eos|><|pad|>"
    assert all(item.kind == "text" for item in rendered.segments)
    assert rendered.finish_status is FinishStatus.COMPLETED
    assert tokenizer.decode(V1DecodeRequest(())).text == ""


def test_special_boundary_cannot_hide_invalid_utf8(
    tokenizer: TokenizerV1SemanticCandidate,
) -> None:
    with pytest.raises(TokenizerContractError, match="complete valid UTF-8"):
        tokenizer.decode(
            V1DecodeRequest((195, V1_BOS_ID, 169), V1SpecialDecodeMode.RENDER)
        )


def test_exact_fingerprint_compatibility(
    tokenizer: TokenizerV1SemanticCandidate,
) -> None:
    fingerprint = tokenizer.descriptor.fingerprint
    assert tokenizer.require_compatible_fingerprint(fingerprint) is None
    for invalid in (None, 1, "x" * 64, fingerprint.upper(), "0" * 64):
        with pytest.raises(TokenizerContractError, match="incompatible"):
            tokenizer.require_compatible_fingerprint(invalid)  # type: ignore[arg-type]


def test_results_are_immutable(tokenizer: TokenizerV1SemanticCandidate) -> None:
    result = tokenizer.encode(V1EncodeRequest("x"))
    with pytest.raises(FrozenInstanceError):
        result.first_omitted_byte = 0  # type: ignore[misc]


def _stream(
    tokenizer: TokenizerV1SemanticCandidate,
    chunks: tuple[bytes, ...],
    **kwargs: object,
):
    stream = TokenizerV1StreamingEncoder(tokenizer, **kwargs)  # type: ignore[arg-type]
    for chunk in chunks:
        stream.push(chunk)
    return stream, stream.finish()


def test_streaming_is_chunk_equivalent(tokenizer: TokenizerV1SemanticCandidate) -> None:
    text = "Aé<|bos|>"
    expected = tokenizer.encode(
        V1EncodeRequest(
            text, max_tokens=8, add_bos=True, add_eos=True, return_offsets=True
        )
    )
    encoded = text.encode()
    for boundary in range(len(encoded) + 1):
        stream, result = _stream(
            tokenizer,
            (encoded[:boundary], encoded[boundary:]),
            max_tokens=8,
            add_bos=True,
            add_eos=True,
            return_offsets=True,
        )
        assert result == expected
        assert stream.state is StreamingState.FINALIZED
        assert stream.buffered_byte_count == 0
        assert stream.chunk_count == 2


@pytest.mark.parametrize("invalid", (-1, 1 << 63, True, 1.5, "1"))
def test_stream_deadline_validation(
    tokenizer: TokenizerV1SemanticCandidate, invalid: object
) -> None:
    with pytest.raises(TokenizerContractError, match="deadline_ns"):
        TokenizerV1StreamingEncoder(tokenizer, deadline_ns=invalid)  # type: ignore[arg-type]


def test_stream_requires_v1_tokenizer() -> None:
    with pytest.raises(TokenizerContractError, match="implement Tokenizer v1"):
        TokenizerV1StreamingEncoder(object())  # type: ignore[arg-type]


def test_stream_deadline_is_terminal(
    tokenizer: TokenizerV1SemanticCandidate, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = 1
    monkeypatch.setattr(v1_module, "monotonic_ns", lambda: now)
    stream = TokenizerV1StreamingEncoder(tokenizer, deadline_ns=3)
    stream.push(b"A")
    now = 3
    with pytest.raises(StreamingDeadlineError, match="expired"):
        stream.finish()
    assert stream.state is StreamingState.FAILED
    assert stream.buffered_byte_count == 0
    with pytest.raises(StreamingStateError, match="already failed"):
        stream.push(b"")


def test_expired_at_stream_construction(
    tokenizer: TokenizerV1SemanticCandidate, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(v1_module, "monotonic_ns", lambda: 2)
    with pytest.raises(StreamingDeadlineError, match="expired"):
        TokenizerV1StreamingEncoder(tokenizer, deadline_ns=2)


@pytest.mark.parametrize("invalid", (bytearray(b"a"), memoryview(b"a"), "a"))
def test_stream_requires_immutable_bytes(
    tokenizer: TokenizerV1SemanticCandidate, invalid: object
) -> None:
    stream = TokenizerV1StreamingEncoder(tokenizer)
    with pytest.raises(TokenizerContractError, match="immutable bytes"):
        stream.push(invalid)  # type: ignore[arg-type]
    assert stream.state is StreamingState.FAILED


@pytest.mark.parametrize(
    ("constant", "message"),
    (
        ("MAX_STREAM_CHUNK_BYTES", "byte limit"),
        ("MAX_STREAM_CHUNKS", "chunk-count"),
        ("MAX_TEXT_BYTES", "aggregate byte"),
    ),
)
def test_stream_resource_limits_are_terminal(
    tokenizer: TokenizerV1SemanticCandidate,
    monkeypatch: pytest.MonkeyPatch,
    constant: str,
    message: str,
) -> None:
    monkeypatch.setattr(v1_module, constant, 0)
    stream = TokenizerV1StreamingEncoder(tokenizer)
    with pytest.raises(TokenizerContractError, match=message):
        stream.push(b"a")
    assert stream.state is StreamingState.FAILED


def test_stream_chunk_count_limit_after_input(
    tokenizer: TokenizerV1SemanticCandidate, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(v1_module, "MAX_STREAM_CHUNKS", 1)
    stream = TokenizerV1StreamingEncoder(tokenizer)
    stream.push(b"")
    with pytest.raises(TokenizerContractError, match="chunk-count"):
        stream.push(b"")


def test_stream_invalid_utf8_fails_closed(
    tokenizer: TokenizerV1SemanticCandidate,
) -> None:
    stream = TokenizerV1StreamingEncoder(tokenizer)
    stream.push(b"\xf0\x9f")
    with pytest.raises(TokenizerContractError, match="strict UTF-8"):
        stream.finish()
    assert stream.state is StreamingState.FAILED
    assert stream.buffered_byte_count == 0


def test_stream_cancel_and_terminal_states(
    tokenizer: TokenizerV1SemanticCandidate,
) -> None:
    stream = TokenizerV1StreamingEncoder(tokenizer)
    stream.push(b"untrusted")
    stream.cancel()
    assert stream.state is StreamingState.CANCELLED
    assert stream.buffered_byte_count == 0
    for operation in (stream.cancel, stream.finish, lambda: stream.push(b"x")):
        with pytest.raises(StreamingStateError, match="already cancelled"):
            operation()


def test_stream_encode_failure_is_terminal(
    tokenizer: TokenizerV1SemanticCandidate, monkeypatch: pytest.MonkeyPatch
) -> None:
    stream = TokenizerV1StreamingEncoder(tokenizer)
    stream.push(b"x")

    def fail(_: object, __: object) -> None:
        raise RuntimeError("encode failure")

    monkeypatch.setattr(TokenizerV1SemanticCandidate, "encode", fail)
    with pytest.raises(RuntimeError, match="encode failure"):
        stream.finish()
    assert stream.state is StreamingState.FAILED
