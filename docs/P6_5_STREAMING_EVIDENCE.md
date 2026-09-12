# P6.5 — Tokenizer Streaming and Chunk-Equivalence Evidence

## Status

**Implementation evidence proposed — exact-head project-owner acceptance required**

The accepted P6.5 gate was squash-merged to `main` as
`e678f39864a779de890b145eff13cf8e12a74963` after exact-revision acceptance and
successful pull-request and post-merge CI. This record applies only that gate and
does not authorize a later P6 slice or finally select Tokenizer v1.

## Implemented contract

`ByteBpeStreamingEncoder` is a single-consumer, bounded state machine for the
recommended experimental byte-BPE candidate. It accepts immutable ordered byte
chunks while `open`, returns no partial tokens, validates the complete aggregate
as strict UTF-8 at `finish()`, and delegates to the unchanged one-shot
`ByteBpeCandidate.encode()` operation.

Successful finalization returns the exact one-shot token IDs, candidate
fingerprint, and completion/truncation status. It then discards buffered input
and enters `finalized`. Cancellation discards input and enters `cancelled`.
Malformed UTF-8, invalid settings, resource limits, candidate errors, and expired
deadlines discard input and enter `failed`. No terminal state can be reopened.

## Bounds and security controls

- Per chunk: `1 MiB`.
- Aggregate input: existing `MAX_TEXT_BYTES` (`16 MiB`).
- Admission calls, including empty chunks: `1,048,576`.
- Output: caller `max_tokens` within existing `MAX_TOKEN_COUNT`.
- Deadline: optional validated `0..2^63-1` absolute monotonic nanoseconds,
  checked at construction, before admission, before finalization, and before
  publishing the final result.
- Accepted chunk type: exact immutable `bytes`; mutable or coercible inputs are
  rejected rather than copied implicitly.
- Cancellation, deadline, malformed-input, and resource failures return no
  `EncodeResult` and release the buffer reference held by the stream.

The implementation has no runtime dependency, provider SDK, external tokenizer,
network, I/O, subprocess, dynamic loading, callback, persistent artifact, or
raw-content logging path. Input, errors, lifecycle state, and tokens are
untrusted data and never authorization.

## Independent equivalence evidence

The tests use the pre-existing public one-shot BPE encoder as the oracle. They do
not reimplement streaming logic to calculate expected tokens.

Coverage includes:

- empty input and empty admission calls;
- one-chunk, one-byte-per-chunk, and every possible two-way byte split;
- Unicode scalar and combining-sequence splits;
- learned merge boundaries and successive BPE merges;
- source code, logs, structured data, security identifiers, Khasi/English text,
  and defensive security prose;
- exact completed and truncation results for multiple token limits;
- invalid and incomplete UTF-8;
- immutable chunk type, chunk size, aggregate size, and chunk-count failures;
- cancellation before and after input plus every post-terminal operation;
- invalid and expired-at-construction, admission, pre-finalization, and
  result-publication deadlines; and
- candidate special-token rejection with terminal buffer disposal.

On Python 3.12, the focused suite passes 38 tests with 100% statement and branch
coverage for `streaming.py`. The complete repository suite passes 139 tests with
100% statement and branch coverage across all tokenizer source modules.

## Architectural limitation

This is bounded streaming ingestion, not progressive token delivery. The
ordered experimental BPE merge program has no proven finite chunk-local safe
emission frontier, so the implementation buffers until finalization. It claims
neither latency nor memory improvement over one-shot encoding. Instances are
single-consumer and do not promise concurrent method safety.

These constraints prevent chunk-dependent tokenization and premature output.
Any progressive or concurrent streaming design requires a separate reviewed
architecture change and evidence; it is not part of P6.5.

## Required closure evidence

P6.5 is not complete until this implementation revision passes unchanged Ruff,
Black, strict mypy, repository/security validation, dependency consistency,
split-package import, pytest with 100% coverage on Python 3.11–3.13, package build,
exact distribution verification, complete security/diff review, exact-head owner
acceptance, squash merge, and post-merge `main` CI.
