# P6.3 — Experimental Byte-Unigram Candidate Gate

## Status

**Accepted for comparison-only implementation**

Project-owner architecture/security acceptance was recorded for PR #8 at exact
head `a8cc1f6a2e6a8f4af184fe7a2ca1711f8b59c8f2`. The gate was squash-merged as
`1a1c9ece79e07df5eeaa607c597ea7002e60b899`; post-merge CI and policy run 16
passed. Acceptance authorizes only the bounded evaluation candidate defined
here, not Tokenizer v1 selection, corpus approval, or persistent artifacts.

This record defines experimental behavior for the Unigram candidate required by
`P6_1_ALGORITHM_EVALUATION.md`. It does not implement Unigram, select Tokenizer
v1, define production tokenizer semantics, approve a corpus or persistent
artifact, or authorize model work.

## Evaluation-only semantic profile

The initial candidate must:

- accept Python Unicode text and encode it as strict UTF-8;
- perform no Unicode normalization or language/syntax pretokenization;
- preserve whitespace and combining characters exactly;
- reserve no special-token IDs and reject requested special-token insertion;
- guarantee byte fallback through fixed IDs `0..255`;
- allocate learned byte-piece IDs from `256` upward;
- decode valid complete candidate output to the exact original text;
- reject invalid IDs and malformed or incomplete UTF-8 without replacement; and
- truncate only at an explicit caller token limit and report `truncated`.

These rules match the byte reference and experimental byte-BPE comparison
profile. They do not approve the production normalization, invalid-input,
pretokenization, offset, special-token, streaming, or truncation contract.

## Deterministic candidate discovery

Experimental construction must:

1. validate the bounded `EvaluationManifest` before reading sample content;
2. consume samples in manifest order and bytes in input order;
3. include the fixed byte alphabet before learned pieces;
4. count every overlapping within-sample byte substring of length `2..16`, never
   crossing a sample boundary;
5. retain only substrings occurring at least twice;
6. stop explicitly with `resource_limit` before inserting a new distinct
   substring after `262,144` distinct substring counters exist;
7. rank learned-piece candidates by descending integer occurrence count, then
   ascending unsigned lexicographic bytes;
8. cap the ranked seed pool at `8,192` learned pieces before model construction;
9. select the first `vocabulary_limit - 256` ranked learned pieces and allocate
   their IDs in that same order;
10. require `vocabulary_limit` in `256..8,192`, including byte fallback;
11. reject configuration outside these limits rather than widening it; and
12. record the manifest identity/version, ordered sample digests, configuration,
    source revision, implementation version, and explicit finish reason.

The fixed seed procedure deliberately avoids random initialization, unordered
container iteration, locale-sensitive ordering, and external tokenizer data.

## Canonical integer scoring

The experimental model is a byte-piece frequency-Unigram candidate: each piece
has one independent frequency-derived integer cost and encoding chooses a
minimum-cost complete segmentation. This bounded proxy is deliberately simpler
than expectation-maximization Unigram training and must be identified by a
distinct experimental algorithm ID.

- Scores use non-negative integers only; runtime floating point, platform math
  libraries, and approximate score comparison are prohibited.
- Let `observed(piece)` be its overlapping construction occurrence count,
  including single-byte occurrences counted by the same manifest traversal.
- Let `effective(piece) = observed(piece) + 1`; the fixed pseudocount gives every
  byte-fallback token a defined cost even when absent from the manifest.
- Let `total` be the sum of effective counts for the final ordered vocabulary.
- With `scale = 2^20`, the canonical cost is the exact positive integer
  `max(1, (total * scale + effective(piece) - 1) // effective(piece))`.
- Conformance vectors must cover absent bytes, exact divisions, values adjacent
  to ceiling boundaries, and maximum supported counts.
- The fingerprint binds each ordered piece and its exact integer cost. A change
  to precision, rounding, discovery, ordering, or tie-breaking changes identity.

Construction is single-pass and frequency-derived; it does not claim
expectation-maximization or negative-log likelihood training. A later EM,
negative-log, or probabilistic-pruning candidate would require a separate
numeric/reproducibility gate and a distinct algorithm identity.

## Deterministic segmentation

Encoding must use bounded dynamic programming over UTF-8 byte offsets. At every
reachable offset it considers matching pieces in ascending token-ID order. A
complete path is preferred by this exact tuple:

1. lower summed integer cost;
2. fewer tokens; then
3. lexicographically smaller token-ID sequence.

Byte fallback guarantees a complete path for bounded valid input. The encoder
must not substitute another candidate, discard bytes, or infer control meaning
from input. Truncation is applied only after the full deterministic token path is
chosen, so increasing the explicit token limit preserves the path prefix.

## Experimental artifact boundary

The first implementation may use immutable in-memory pieces and costs only.
Serialization and loading remain blocked until the canonical non-executable,
bounded artifact schema and fingerprint procedure are separately accepted.
Candidate fingerprints are evaluation identities and do not establish model
compatibility or production approval.

## Resource and security controls

- Construction, encoding, decoding, and evaluation remain local/offline with no
  provider SDK, provider credential, network access, or external tokenizer.
- Training content is bounded to `1 MiB` per run, substring length to `16` bytes,
  distinct substring counters to `262,144`, the learned seed pool to `8,192`,
  and total vocabulary to `8,192`.
- Input, manifests, metadata, pieces, token IDs, and decoded output are untrusted
  data and never authorization.
- Validate counts, lengths, IDs, configuration, and decode output size before
  allocation or lookup.
- Raw text and decoded output are not logged or copied into reports.
- No artifact-supplied code, dynamic import, expression evaluation, callback,
  plugin, subprocess, or external reference may execute.
- Integrity, malformed input, truncation, and resource failures remain explicit
  and cannot grant approval or widen any policy boundary.

## Required implementation evidence

Before implementation may merge, its exact PR head must show:

- deterministic discovery, costs, vocabulary ordering, and fingerprint replay;
- integer-cost conformance at pseudocount, ceiling, and maximum-count boundaries;
- exact segmentation tie-breaking and byte-fallback coverage;
- exact encode reproduction and valid complete round trips;
- explicit invalid-ID, malformed UTF-8, special-token, truncation, and resource
  failures;
- comparison through the accepted candidate-neutral evaluation report;
- unchanged Ruff, Black, strict mypy, repository/security, dependency,
  split-package import, pytest, and 100% source-coverage gates on Python
  3.11–3.13;
- successful package build and exact distribution-boundary verification;
- complete-diff security review and project-owner exact-head acceptance; and
- squash merge followed by successful `main` CI.

Candidate evidence cannot itself select Tokenizer v1.
