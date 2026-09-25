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
P6.5 is verified complete at merge
`345846ac0e02b3bd0c265b1d2f4649d0774cade9` with successful exact-head and
post-merge validation. This does not close any later Tokenizer v1 gate.

`docs/P6_6_CANONICAL_ARTIFACT.md` defines the accepted fixed big-endian binary envelope for
the experimental P6.4 BPE candidate. It separates behavior fingerprint from the
digest of provenance-bearing canonical bytes, permits bounded in-memory byte
serialization/loading only, and rejects malformed data before controlled
allocation. It does not approve production compatibility or filesystem loading.

The accepted gate is implemented by the bytes-only
`cybersecgpt.tokenizer.artifact` module. It reconstructs and revalidates the
existing immutable BPE candidate, binds content-minimizing provenance, and
requires byte-identical canonical rebuilding; it adds no I/O or execution role.
P6.6 is verified complete at merge
`92776213a1e8003682752a268af5e4bc0664457d` with successful exact-head and
post-merge validation. This does not close a later Tokenizer v1 gate.

All tokenizer data is untrusted. Results may describe tokenization behavior but
cannot grant permissions, change classification, widen target scope, weaken
provider/network or offline policy, extend deadlines or budgets, or reduce
verification requirements.

The accepted `docs/P6_7_PERFORMANCE_RESOURCE_GATE.md` permits observational
encode/decode, BPE streaming, canonical artifact size, and traced Python
allocation measurements on the fixed generated P6.4 manifests. The runner and
`docs/P6_7_PERFORMANCE_EVIDENCE.md` are tokenizer-local evidence only; no
candidate behavior, public contract, deterministic fingerprint, or cross-component
benchmark suite is changed. The accepted implementation merged as
`32b7aef9bdcac29d66bdf2857ef3f84bc0444853` with successful exact-head and
post-merge checks. Closure PR #20 was accepted at exact head
`6cb6095e7c932aea300b4d5419573e61460af72f`, squash-merged as
`8a8d2cfa40b6b790528292cc492dc79597dc66b1`, and passed exact-head and
post-merge CI and agent-policy runs 44 and 45. P6.7 is formally closed. Model
compatibility, corpus approval, and final algorithm selection remain outside
this performance measurement.

`docs/P6_8_EXPERIMENTAL_CONFORMANCE_GATE.md` proposes reproducible,
identity-bound known vectors for the existing byte reference, experimental
BPE/Unigram comparison candidates, buffered BPE streaming, and canonical BPE
artifact. Independent expected outputs and negative failure cases are required
before behavioral conformance can be claimed. The gate is pending exact-head
acceptance; no production semantics, compatibility, or corpus approval follows.

The gate was accepted at exact PR #22 head
`773ef632bf1201d232a99fa100afa144a3828ee6`, merged as
`c863af96bfee43889b8c2be8d98e5d9c55868433`, and passed runs 48/49. The
proposed vector verifier and `docs/P6_8_EXPERIMENTAL_CONFORMANCE_EVIDENCE.md`
exercise existing public candidate APIs and canonical bytes without modifying
candidate behavior, adding production semantics, or changing dependencies.
The implementation was accepted at exact PR #23 head
`d4b4b7826ebbeaeecf5a0ffc4303041f50b9a568`, merged as
`980ac53493cbef3ba6fad958e5fa78525682b7ab`, and passed pre/post-merge
runs 50/51. Formal closure awaits exact-head review of the closure record.
