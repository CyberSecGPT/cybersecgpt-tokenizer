# P6.2 — Experimental Byte-BPE Candidate Gate

## Status

**Proposed — candidate implementation blocked pending exact-revision acceptance**

This record defines experimental behavior for the byte-level Byte Pair Encoding
(BPE) candidate required by `P6_1_ALGORITHM_EVALUATION.md`. It does not select
BPE, constrain the later Unigram candidate, define the production Tokenizer v1
contract, approve a corpus or artifact, or authorize model work.

## Evaluation-only semantic profile

The initial byte-BPE candidate must use the following fixed profile:

- accept Python Unicode text and encode it as strict UTF-8;
- perform no Unicode normalization;
- preserve whitespace and combining characters exactly;
- apply no language-specific or syntax-specific pretokenization;
- reserve no special-token IDs and reject requested special-token insertion;
- guarantee fallback for every byte value through IDs `0..255`;
- allocate learned tokens from ID `256` upward in deterministic order;
- decode valid candidate output to the exact original text;
- reject invalid IDs and malformed or incomplete UTF-8 explicitly, without
  replacement; and
- truncate only when the caller supplies an explicit output-token limit, while
  reporting `truncated` rather than `completed`.

These choices make the byte reference and BPE measurements comparable. They are
not approval of the eventual production normalization, invalid-input,
pretokenization, offset, special-token, streaming, or truncation policy.

## Deterministic training profile

Experimental training must:

1. validate the bounded `EvaluationManifest` before processing sample content;
2. consume samples in manifest order and UTF-8 bytes in input order;
3. use integer occurrence counts only;
4. rank equal-frequency adjacent pairs by ascending `(left token bytes, right
   token bytes)` using unsigned lexicographic byte order;
5. apply exactly one merge at a time and recompute adjacent-pair counts;
6. stop at the explicit vocabulary limit or when no eligible update remains;
7. reject vocabulary limits outside `256..MAX_VOCABULARY_SIZE`;
8. record the exact manifest identity, version, sample digests, configuration,
   source revision, and implementation version; and
9. produce a candidate report only—training success never grants approval.

No random seed or floating-point ranking is permitted for this BPE candidate.
Unigram numeric behavior and reproducibility require a separate reviewed gate.

## Experimental artifact boundary

The first BPE candidate may use immutable in-memory data structures only.
Persistent artifact serialization and loading remain blocked until a canonical,
non-executable, bounded artifact schema and fingerprint procedure are separately
reviewed and accepted.

Candidate identity must bind all behavior-defining configuration and learned
token data. A repository revision, filename, vocabulary size, or mutable label is
not sufficient identity. Until the canonical persistent format is accepted,
candidate fingerprints are evaluation identities and must not be asserted as
production model compatibility.

## Resource and security controls

- Core BPE construction, encoding, decoding, and evaluation are local/offline and
  have no provider credentials, network behavior, or proprietary tokenizer.
- Input text, manifests, metadata, learned sequences, tokens, and decoded output
  remain untrusted data and never authorization.
- Counts, byte lengths, token IDs, vocabulary sizes, and output sizes are bounded
  before allocation or iteration.
- Raw text and decoded output are not logged or copied into metric reports.
- No artifact-supplied code, dynamic import, expression evaluation, subprocess,
  plugin, callback, or external reference is loaded or executed.
- Failure never substitutes another candidate, widens a resource limit, changes
  policy, or promotes incomplete evidence to a successful result.

## Required implementation evidence

Before the experimental BPE candidate can be merged, its exact PR head must show:

- deterministic construction and fingerprint reproduction;
- exact encode reproduction and round trips for every valid conformance vector;
- explicit invalid-ID, malformed UTF-8, special-token, truncation, and resource
  failures;
- unchanged Ruff, Black, strict mypy, repository/security, dependency,
  split-package import, pytest, and 100% source-coverage gates on Python
  3.11–3.13;
- successful package build and exact distribution-boundary verification;
- complete-diff security review and project-owner exact-head acceptance; and
- squash merge followed by successful `main` CI.

Candidate results remain evidence for later selection. They do not themselves
select Tokenizer v1.
