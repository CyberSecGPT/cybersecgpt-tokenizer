# P6.8 — Experimental Tokenizer Conformance Vector Gate

## Status and decision

**Proposed — architecture/security acceptance required before implementation.**

P6.7 formally closed the fixed-fixture performance/resource evidence slice. This
gate addresses deterministic conformance of the existing UTF-8 byte reference,
experimental byte-BPE candidate, buffered BPE streaming encoder, and canonical
experimental BPE artifact. It does not select Tokenizer v1, approve a training
corpus, define production normalization/offset/special-token semantics, establish
model compatibility, or authorize another P6 implementation slice. Experimental
Unigram vectors may be included for comparison, but no Unigram artifact or
streaming support may be inferred.

The canonical tokenizer contract requires independently reviewable vectors for
empty, ASCII, Unicode, combining characters, malformed inputs, byte fallback,
round trips, streaming, limits, fingerprints, and artifact migrations. This gate
records the test boundary before implementation; observed output must not be
copied uncritically from the implementation and called an independent oracle.

## Fixed identities and fixture provenance

- Pin the source commit, candidate construction manifest digest and sample
  digests, training configuration, descriptor fingerprint, artifact format and
  digest, and vector-schema version. Record exact expected token IDs and outputs
  only for a reconstructed candidate with those identities; reject identity
  mismatch or incomplete construction before checking vectors.
- Use the already published inert, generated P6.4 construction manifest for
  candidate reconstruction. Keep conformance inputs separate from that training
  manifest; reuse reviewed generated CC0 examples or generate new inert CC0
  examples with explicit provenance. Do not import or approve an external corpus,
  real logs, secrets, personal data, live targets, or executable payloads.
- Store a bounded, versioned, machine-readable vector fixture with canonical
  field ordering/encoding, explicit expected IDs or typed failures, source and
  license identifiers, input digest, expected fingerprint and artifact digest.
  Human-reviewed inert fixture bytes may be committed for exact replay. Runtime
  reports and failure messages contain identity and case labels, not raw input.
  A digest alone is insufficient for an independently replayable known vector.
- Derive expected results with an independently reviewed reference calculation
  or manual byte/merge derivation, then compare to the implementation. Pin a
  fixed known-artifact byte/digest vector and review its structural fields
  independently. Never refresh golden results automatically after a failure.

## Required vector families

1. Empty string, ASCII, spaces/newlines, null byte, and boundary whitespace.
   Establish exact IDs, finish status, fingerprint, and reversible decode where
   promised, including empty input and byte fallback.
2. Non-ASCII Unicode including Khasi, multi-byte scalars, combining marks,
   canonically equivalent but byte-distinct strings, and literal special-looking
   text. Confirm the experimental no-normalization profile preserves byte
   distinctions and treats literal text as data; no special-token insertion is
   permitted for candidates with empty allocations.
3. Inert code, shell/PowerShell, structured data, logs, URL/IP/hash/CVE strings,
   and security-rule examples drawn from the generated domain fixtures. Keep
   domain and provenance visible so a narrow fixture cannot imply coverage of
   untested domains.
4. Strict UTF-8 invalid byte sequences on decode and streaming finalization,
   invalid/unknown token IDs, malformed request types, explicit token/byte
   limits, truncation status, cancelled sessions, and expired deadlines. Assert
   exact failure class or status and absence of partial successful output; do
   not promote truncated or failed cases to reversible successes.
5. BPE one-shot versus buffered streaming for every byte split of short inputs
   and selected multi-chunk partitions, including splits inside UTF-8 scalars
   and across merge boundaries. Compare exact IDs, fingerprint, and status.
   No progressive emission or incremental decode is claimed.
6. Canonical BPE artifact known bytes/digest, byte-identical reserialization,
   descriptor behavior fingerprint, and rejection of altered length, count,
   digest, version, token, merge, or trailing data. Test envelope rejection
   before payload-driven allocation. A changed provenance field may alter the
   artifact digest without changing behavior; a behavior change must alter the
   behavior fingerprint.

For every positive vector, assert the exact output and identity, not only an
encode/decode round trip. Pair positive cases with negative cases that deny
unknown control roles, malformed artifacts, unauthorized substitution, or a
silent fallback. If a vector cannot be independently specified under current
experimental semantics, mark it **unresolved** with a reason; do not encode a
production choice by default.

## Verification and security boundary

- Keep a fixed upper bound on fixture count, bytes per input, total fixture
  bytes, token IDs, partition count, and verification report size. Avoid
  exponential partition enumeration on long inputs.
- Run fully offline with no provider, dynamic loading, subprocess, filesystem
  corpus ingestion, callback execution, or network dependency. Treat fixture
  fields, artifact bytes, and decoded text as untrusted data. Reject unknown
  schema fields and versions and malformed types before allocating from counts.
- Conformance verifies behavior; it grants no authorization, classification
  downgrade, target-scope widening, provider/network access, offline exception,
  deadline or budget relaxation, verification reduction, license approval, or
  production tokenizer/model compatibility.
- The implementation PR must include independent positive/negative tests,
  exact-vector replay and fingerprint/artifact integrity checks, complete
  security and diff review, reproducibility from a pinned revision, unchanged
  Ruff/Black/strict mypy/repository and security checks/dependency consistency/
  split-package imports/pytest at 100% source coverage on Python 3.11–3.13,
  plus build and exact distribution verification. Generated or handwritten
  vector data must respect the wheel/sdist boundary.
- Accept this exact architecture/security gate revision first, with successful
  exact-head CI and agent-policy checks, squash merge, and successful post-merge
  `main` checks. Then separately implement and review the vectors at an exact
  head with the same gates. Formal P6.8 closure needs its own checked evidence.

Remaining Tokenizer v1 decisions include corpus/license review, normalization,
offsets, initial special-token allocation, model compatibility, final algorithm
selection, and production artifact approval. No later P6 work begins through
this proposal.
