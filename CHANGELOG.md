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
- Python 3.11–3.13 validation, strict typing, 100% source coverage, and exact
  distribution-boundary gates.
