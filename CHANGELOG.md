# Changelog

## Unreleased

### Added

- P6 Tokenizer v1 acceptance plan and canonical policy controls.
- Immutable, bounded tokenizer descriptor, special-token, encode, and decode
  contracts.
- Deterministic, provenance-bearing and content-minimizing evaluation manifests.
- Fixed deterministic UTF-8 byte reference candidate and content-minimizing
  structural metrics for reproducible algorithm comparison.
- Proposed experimental semantics, deterministic training rules, and security
  boundaries for byte-BPE candidate evaluation.
- Deterministic, bounded, in-memory experimental byte-BPE construction, encoding,
  decoding, fingerprinting, provenance evidence, and explicit stop outcomes.
- Candidate-neutral deterministic structural evaluation reports with exact
  reduced ratios, manifest/candidate identity binding, explicit truncation and
  decode outcomes, and no raw-text or timing fields.
- Accepted deterministic experimental byte-Unigram candidate semantics plus
  bounded in-memory construction, exact integer scoring, stable segmentation,
  byte fallback, provenance evidence, and explicit resource failures.
- Proposed controlled BPE-versus-Unigram benchmark and deterministic
  recommendation gate with separate generated construction/evaluation manifests,
  per-domain evidence, and explicit production-selection blockers.
- Implemented that accepted comparison with disjoint generated CC0 manifests,
  deterministic replay and report identity, fail-closed selection, and evidence
  recommending byte-BPE for the remaining Tokenizer v1 gates.
- Proposed the P6.5 bounded byte-stream ingestion, lifecycle, cancellation,
  deadline, strict UTF-8 finalization, and exact BPE chunk-equivalence gate while
  prohibiting unproven progressive token emission.
- Implemented the accepted P6.5 single-consumer byte-stream state machine with
  fail-closed limits, cancellation/deadline propagation, strict finalization,
  exact one-shot equivalence evidence, and no partial token output.
- Verified P6.5 exact-head acceptance, squash merge, and post-merge validation.
- Proposed the P6.6 canonical non-executable experimental BPE artifact,
  provenance binding, strict loading bounds, and behavior/artifact identity gate.
- Added the P6.6 bytes-only canonical BPE serializer/loader, fixed known-vector
  identities, fail-closed malformed-input coverage, and implementation evidence.
- Verified P6.6 exact-head acceptance, squash merge, post-merge validation, and
  bounded canonical-artifact closure evidence.
- Accepted the P6.7 performance/resource architecture gate and proposed
  content-minimizing fixed-fixture timing, traced-allocation, streaming, artifact
  size, and fail-closed implementation evidence.
- Verified P6.7 implementation exact-head owner acceptance, squash merge, and
  post-merge validation; recorded measured evidence for formal closure review.
- Verified formal P6.7 closure at accepted PR #20 head
  `6cb6095e7c932aea300b4d5419573e61460af72f`, squash merge
  `8a8d2cfa40b6b790528292cc492dc79597dc66b1`, and successful exact-head
  and post-merge CI and agent-policy runs 44/45; later P6 gates remain open.
- Proposed the P6.8 experimental conformance-vector architecture/security gate
  with independent known-output and negative-case review; implementation awaits
  exact-head gate acceptance and verified merge.
- Python 3.11–3.13 validation, strict typing, 100% source coverage, and exact
  distribution-boundary gates.
