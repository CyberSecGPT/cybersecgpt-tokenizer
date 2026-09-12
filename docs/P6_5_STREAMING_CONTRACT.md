# P6.5 — Tokenizer Streaming Contract and Chunk-Equivalence Gate

## Status

**Proposed — implementation blocked pending exact-revision project-owner acceptance**

This gate defines streaming semantics for the experimental byte-BPE candidate
recommended by the accepted P6.4 comparison. It does not finally select
Tokenizer v1, approve a persistent artifact or corpus, define production special
tokens or offsets, or authorize later P6 work.

## Scope and decision boundary

This repository owns the tokenizer-local streaming contract, implementation, and
chunk-equivalence evidence. Reusable cross-component streaming benchmarks remain
owned by `cybersecgpt-benchmarks`.

P6.5 evaluates `experimental-byte-bpe-v1` without changing its descriptor,
fingerprint, learned merges, normalization, pretokenization, special-token, or
truncation semantics. Streaming output must bind the same candidate fingerprint
as one-shot output. A passing streaming result is evidence only and cannot grant
artifact approval, model compatibility, release status, authorization, or final
algorithm selection.

## Architecture decision

The public streaming encoder accepts ordered immutable `bytes` chunks. This
permits conformance tests to split strict UTF-8 at every byte boundary, including
inside multibyte scalar values. It maintains one private bounded aggregate buffer
and exposes an explicit lifecycle:

```text
OPEN -> FINALIZED
  +-> CANCELLED
  +-> FAILED
```

- A new stream begins in `OPEN`.
- Non-empty and empty chunks are admitted only while `OPEN`; every call counts
  against the chunk limit.
- `finish()` is accepted exactly once while `OPEN`. It validates the complete
  aggregate as strict UTF-8, constructs the existing bounded `EncodeRequest`, and
  delegates to the unchanged BPE one-shot encoder.
- `cancel()` is accepted while `OPEN`, discards buffered content, and enters
  `CANCELLED` without producing tokens.
- A contract, UTF-8, resource-limit, or deadline failure discards buffered
  content and enters `FAILED` without producing tokens.
- Push, finish, or cancellation after a terminal state fails explicitly and
  never reopens or substitutes a stream.

The initial implementation buffers at most `MAX_TEXT_BYTES` and emits no tokens
before successful finalization. The ordered BPE merge program can create tokens
across arbitrary chunk boundaries, and this gate establishes no proof of a
finite safe progressive-emission frontier. Progressive token emission is
therefore prohibited rather than approximated. This is streaming ingestion with
bounded memory, not a claim of incremental token delivery or latency improvement.

## Resource and termination contract

- Each chunk is at most `1 MiB`.
- Aggregate input is at most the existing `MAX_TEXT_BYTES` (`16 MiB`).
- At most `1,048,576` chunk-admission calls are allowed, including empty chunks.
- The existing `MAX_TOKEN_COUNT` and caller `max_tokens` bounds remain unchanged.
- Bounds are checked before extending the aggregate buffer or invoking BPE.
- The caller may cancel explicitly. An optional absolute monotonic deadline is
  checked at construction, before every chunk admission, and before finalization.
- Cancellation and deadline expiry are terminal failures, produce no partial
  tokens, and cannot be converted to `completed` or `truncated`.
- The implementation uses the standard library only and performs no I/O,
  networking, subprocess execution, dynamic loading, callback execution, raw
  input logging, or persistent artifact access.

The deadline clock is operational input, not part of the candidate fingerprint
or deterministic equivalence evidence. Tests use a controlled clock value; no
wall-clock or timing measurement enters canonical evidence.

## Exact chunk-equivalence rule

For any byte sequence `B` that is the strict UTF-8 encoding of text `T`, any
ordered chunk partition whose concatenation is exactly `B`, and identical
`max_tokens` and special-token settings:

```text
stream.finish() == candidate.encode(EncodeRequest(T, ...))
```

Equality covers the exact token-ID tuple, candidate fingerprint, and finish
status. It applies to completed and explicitly truncated results. Chunk shape,
including empty chunks, cannot affect output.

Invalid or incomplete UTF-8 is accepted only as non-final chunk data and fails
at finalization. Over-limit chunks, aggregate bytes, chunk counts, invalid
special-token requests, cancellation, and expired deadlines fail explicitly.
No failure may return or retain a partial `EncodeResult`.

## Required conformance evidence

The implementation PR must demonstrate:

- empty input and empty-chunk behavior;
- one chunk, every single byte as a chunk, and every two-way byte split;
- splits inside every multibyte UTF-8 scalar and combining sequence fixture;
- splits across every learned BPE merge boundary represented by fixtures;
- code, logs, structured data, security identifiers, and defensive prose;
- exact equivalence for completed output and each tested truncation limit;
- repeated replay with identical results and fingerprint;
- incomplete and malformed UTF-8 failure at finalization;
- per-chunk, aggregate-byte, chunk-count, and output-token boundaries;
- cancellation before input, after partial input, and after terminal states;
- deadline expiry at construction, chunk admission, and finalization; and
- fail-closed state transitions with buffer disposal and no token output.

Tests must independently construct expected one-shot results through the existing
public BPE encoder. They must not reproduce the streaming implementation's logic
as the oracle.

## Security invariants

- Stream chunks, decoded text, state, errors, and token output are untrusted data
  and never authorization or executable instructions.
- Streaming cannot lower classification, widen target or provider/network scope,
  disable offline operation, extend deadlines or budgets, reduce verification,
  or change the candidate selected by the caller.
- Invalid, incomplete, cancelled, deadline, resource-limit, or internal-error
  outcomes cannot be promoted to completed or truncated results.
- Buffer contents are not logged or copied into evidence. Terminal cancellation
  and failure release the implementation's reference to buffered content.
- Core behavior remains deterministic, local/offline, dependency-free, and
  independent of proprietary providers and external tokenizers.

## Required merge evidence

Before implementation may begin, this exact gate revision requires an explicit
project-owner architecture/security `ACCEPT` decision and successful exact-head
CI, squash merge, and post-merge `main` CI.

Before the implementation may merge, its exact PR head must have:

- all conformance and failure evidence above with 100% source coverage;
- unchanged Ruff, Black, strict mypy, repository/security validation,
  dependency consistency, split-package import, and pytest gates on Python
  3.11–3.13;
- successful package build and exact distribution-boundary verification;
- complete architecture, security, and PR-diff review;
- explicit project-owner `ACCEPT` for the exact head; and
- squash merge followed by successful post-merge `main` CI.

P6.5 completion does not authorize the canonical artifact, performance, broader
conformance, corpus-review, or other later P6 gates.
