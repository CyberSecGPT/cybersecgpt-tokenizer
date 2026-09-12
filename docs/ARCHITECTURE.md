# Architecture

## Milestone

P6 — CyberSecGPT Tokenizer v1.

## Ownership

This repository owns first-party tokenizer training, execution, normalization,
vocabulary and special-token management, artifacts, manifests, and conformance
vectors. It does not own model, inference, general training orchestration,
datasets, product surfaces, or authorization.

## Current boundary

The repository provides immutable bounded public contracts, provenance-bearing
evaluation manifests, and a fixed UTF-8 byte reference candidate. The reference
maps strict UTF-8 bytes directly to IDs 0..255, performs no normalization, has no
special-token allocation, fails explicitly on invalid decode sequences, and
records deterministic content-minimizing structural metrics.

The candidate-neutral evaluation layer runs any candidate satisfying the bounded
descriptor/encode/decode protocol against the same validated manifest and token
limit. Its immutable report binds manifest and candidate identity and uses exact
reduced integer ratios rather than floating point or timing measurements.
Compression ratios are omitted for incomplete encodes; decode failures remain
explicit; and encode/decode fingerprint disagreement aborts evaluation. Reports
contain digests and measurements, never raw sample content.

This reference is benchmark infrastructure, not selection of the Tokenizer v1
algorithm or its production invalid-input policy. BPE and Unigram candidates,
normalization, pretokenization, offsets, artifact encoding, special-token
allocation, streaming, corpus approval, and training remain gated by
`P6_ACCEPTANCE.md` and `docs/P6_1_ALGORITHM_EVALUATION.md`.

`docs/P6_2_BYTE_BPE_CANDIDATE.md` defines accepted evaluation-only semantics and
deterministic training rules for byte-BPE. The implementation consumes a
validated evaluation manifest, counts adjacent token pairs using integers,
resolves frequency ties by unsigned learned byte sequences, and applies merges
in a stable order. A hard merge budget and training-byte ceiling bound candidate
construction and the result records why construction stopped. Learned state is
immutable and in-memory only.

Candidate reports are evidence, not a selection mechanism. Persistent artifacts,
algorithm selection, and production Tokenizer v1 behavior remain unresolved.

`docs/P6_3_UNIGRAM_CANDIDATE.md` defines the accepted comparison-only
byte-Unigram profile. Its implementation validates bounded manifest content,
discovers overlapping pieces without crossing sample boundaries, derives exact
integer frequency costs, and uses stable dynamic-programming tie-breaking with
guaranteed byte fallback. Candidate pieces and costs are immutable and in-memory
only; serialization, algorithm selection, and production approval remain gated.

`docs/P6_4_ALGORITHM_BENCHMARK.md` defines the accepted controlled comparison
boundary, and `docs/P6_4_ALGORITHM_BENCHMARK_EVIDENCE.md` records its reproducible
result.
Tokenizer-local fixtures and exact structural decision evidence remain here;
reusable cross-component benchmark suites remain owned by
`cybersecgpt-benchmarks`. The proposed report can recommend which learned
candidate advances. Byte-BPE is recommended by the first fixed comparison, but
final selection remains blocked on streaming, canonical
artifact, performance, conformance, and corpus-review evidence.

`docs/P6_5_STREAMING_CONTRACT.md` defines the accepted gate and
`docs/P6_5_STREAMING_EVIDENCE.md` records its implementation evidence. Ordered
bounded byte chunks are buffered under explicit lifecycle, chunk-count,
aggregate-byte, cancellation, and deadline controls; strict UTF-8 validation and
the unchanged BPE one-shot encode occur only at finalization. Exact token IDs,
fingerprint, and finish status must be independent of chunking. Progressive
emission remains prohibited until a safe merge frontier is separately proven.

All tokenizer data is untrusted. Results may describe tokenization behavior but
cannot grant permissions, change classification, widen target scope, weaken
provider/network or offline policy, extend deadlines or budgets, or reduce
verification requirements.
