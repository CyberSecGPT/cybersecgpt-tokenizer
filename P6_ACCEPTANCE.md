# P6 — CyberSecGPT Tokenizer v1 Acceptance Plan

## Status

**In progress — architecture and repository bootstrap**

This plan begins P6 after verified P5 closure. It does not select a tokenizer
algorithm, vocabulary, normalization profile, artifact encoding, or training
corpus, and it does not claim a trained or production-ready tokenizer.

## Governing scope

- Canonical owner: `CyberSecGPT/cybersecgpt-tokenizer`
- Roadmap milestone: P6 — CyberSecGPT Tokenizer v1
- Contract: `cybersecgpt-docs/docs/specifications/tokenizer-contract.md`
- Allowed dependencies: Foundation and approved normalization/data interfaces
- Forbidden core dependencies: proprietary remote AI APIs, external-provider
  tokenizers, model/inference/training implementations, and product surfaces

## Required implementation slices

1. Repository, security, contribution, validation, and package boundaries.
2. Versioned immutable tokenizer descriptor and bounded request/result contracts.
3. Explicit Unicode, invalid-input, normalization, pretokenization, and offset
   semantics.
4. Deterministic encode, decode, streaming, truncation, and special-token behavior.
5. Non-executable, self-describing artifact schema with strict bounds and
   canonical content fingerprinting.
6. Exact model/tokenizer compatibility checks based on fingerprints rather than
   vocabulary size.
7. First-party candidate training interface with dataset-manifest provenance;
   training success must not grant artifact approval.
8. Canonical conformance vectors for empty, ASCII, Unicode, combining characters,
   malformed inputs, code, logs, structured data, security identifiers, streaming,
   truncation, and every special-token/escape rule.
9. Benchmarks covering natural language, source code, assembly, shell and
   PowerShell, logs, JSON/YAML/XML, HTTP/DNS, URLs/IPs/hashes/CVEs, Sigma/YARA,
   SIEM queries, firewall/IDS rules, infrastructure-as-code, telemetry, malware
   analysis, and threat intelligence.
10. Reproducible build, dependency consistency, exact distribution-boundary
    checks, strict static analysis, and 100% source coverage across supported
    Python versions.

## Security invariants

- Tokenizer input, artifacts, manifests, metadata, and decoded output are
  untrusted data and never authorization.
- Artifacts contain data only and never load or execute supplied code.
- Schema, hashes, sizes, counts, IDs, and integer bounds are validated before
  allocation or use.
- Unknown special-token roles are not interpreted as control instructions.
- Raw input and decoded output are not logged by default.
- Core startup, training, encoding, decoding, validation, and tests work with the
  network disabled and without provider credentials.
- Resource limits, deadlines, truncation, errors, and integrity failures fail
  explicitly; they cannot silently widen scope or substitute another tokenizer.

## Decision gates

Before algorithm implementation, record and review:

- algorithm candidate and benchmark rationale;
- normalization and invalid-input policy;
- pretokenization and offset semantics;
- canonical artifact and fingerprint encoding;
- initial special-token role/ID allocation;
- reproducibility and training-data provenance requirements; and
- licensing status for code, artifacts, and training data.

Any change to repository ownership, dependency direction, public contract
compatibility, trust boundaries, or persistent artifact format follows the
architecture change gate and requires the applicable ADR/review.

The accepted experimental behavior for the required byte-BPE candidate is
recorded in `docs/P6_2_BYTE_BPE_CANDIDATE.md`. Its implementation remains an
evaluation-only candidate and does not select Tokenizer v1. Candidate-neutral
structural reports compare bounded implementations using exact count ratios and
explicit integrity/outcome evidence without timing data. The accepted Unigram
numeric, discovery, segmentation, and reproducibility rules are recorded in
`docs/P6_3_UNIGRAM_CANDIDATE.md`. Its implementation remains evaluation-only and
does not select Tokenizer v1 or approve a persistent artifact.

The accepted controlled comparison and recommendation policy is recorded in
`docs/P6_4_ALGORITHM_BENCHMARK.md`. It keeps tokenizer-local decision evidence in
this repository while reserving reusable suites for `cybersecgpt-benchmarks`.
Its reproducible implementation evidence recommends byte-BPE under the fixed
generated manifests and equal settings. The recommendation remains insufficient
for final Tokenizer v1 selection.

The accepted streaming architecture and security decision is recorded in
`docs/P6_5_STREAMING_CONTRACT.md`, with implementation evidence in
`docs/P6_5_STREAMING_EVIDENCE.md`. It requires exact one-shot equivalence across
arbitrary valid UTF-8 byte partitions, bounded buffering, explicit terminal
cancellation/deadline/resource failures, and no progressive emission without a
separately proven safe BPE frontier. The implementation remains evidence for
final selection rather than Tokenizer v1 approval.

P6.5 closure is verified at implementation head
`e40c22969f7c1f81394ae7948aed23d9b05c3b82`, squash merge
`345846ac0e02b3bd0c265b1d2f4649d0774cade9`, and successful exact-head and
post-merge runs 25 and 26. This closes only the streaming and chunk-equivalence
slice; the remaining Tokenizer v1 acceptance requirements stay open.

The accepted canonical experimental BPE artifact and fingerprint decision is
recorded in `docs/P6_6_CANONICAL_ARTIFACT.md`. It defines a fixed bounded binary
encoding, strict pre-allocation validation, exact provenance binding, canonical
round trips, and distinct behavior/artifact identities.

The implementation candidate and its known-vector, identity, round-trip,
malformed-input, allocation-bound, and content-minimization evidence are recorded
in `docs/P6_6_CANONICAL_ARTIFACT_EVIDENCE.md`. P6.6 closure is verified at
implementation head `b4f857687f3e838fcae7b1a7f27f62e52440ea50`, squash merge
`92776213a1e8003682752a268af5e4bc0664457d`, and successful exact-head and
post-merge runs 32 and 33. This closes only the canonical experimental artifact
slice; the remaining Tokenizer v1 acceptance requirements stay open.

The accepted P6.7 performance/resource gate is specified in
`docs/P6_7_PERFORMANCE_RESOURCE_GATE.md`. It requires controlled observational
timing and traced-allocation evidence for the fixed experimental candidate and
controls, separate from deterministic structural report identity. The gate was
accepted at head `057dc3c9e22c6a126f7a5f38fa8d2895b5958ad7`, merged as
`d935664415b690f526832a04e437e5c5be3e34bf`, and passed pre- and post-merge
runs 36 and 37. The measured implementation was accepted at exact head
`b40be6923ac7af1dd8b9f385de97f3afca9c3b9b`, merged as
`32b7aef9bdcac29d66bdf2857ef3f84bc0444853`, and passed exact-head and
post-merge runs 41 and 42. `docs/P6_7_PERFORMANCE_EVIDENCE.md` records the
observations. Formal P6.7 closure PR #20 was accepted at exact head
`6cb6095e7c932aea300b4d5419573e61460af72f`, squash-merged as
`8a8d2cfa40b6b790528292cc492dc79597dc66b1`, and passed exact-head and
post-merge CI and agent-policy runs 44 and 45. This closes the experimental
performance/resource evidence slice only. No production selection follows from
measured throughput or allocation.

The proposed experimental conformance-vector architecture/security gate is
recorded in `docs/P6_8_EXPERIMENTAL_CONFORMANCE_GATE.md`. It requires independent,
identity-bound known vectors for existing candidate behavior, streaming,
failures, and canonical BPE artifacts. P6.8 implementation is blocked pending
exact-head acceptance, merge, and post-merge checks of that gate. Corpus/license
approval, production semantics, and Tokenizer v1 selection remain open.

The P6.8 architecture gate was accepted at PR #22 head
`773ef632bf1201d232a99fa100afa144a3828ee6`, merged as
`c863af96bfee43889b8c2be8d98e5d9c55868433`, and passed pre- and
post-merge runs 48 and 49. `docs/P6_8_EXPERIMENTAL_CONFORMANCE_EVIDENCE.md`
records the fixed-vector implementation. The implementation was accepted at PR
#23 head `d4b4b7826ebbeaeecf5a0ffc4303041f50b9a568`, squash-merged as
`980ac53493cbef3ba6fad958e5fa78525682b7ab`, and passed pre- and
post-merge CI and policy runs 50 and 51. Formal closure PR #24 was accepted at
exact head `5972c304a37a42d3bc68e84cf7ebef73e28d36cd`, squash-merged as
`a15bffed922c8712b8c9ae63869f3561d81ebc21`, and passed exact-head and
post-merge CI and policy runs 52 and 53. This closes only the experimental
conformance-vector slice; remaining Tokenizer v1 acceptance requirements stay open.

The accepted Tokenizer v1 semantic and compatibility profile is recorded in
`docs/P6_9_PRODUCTION_SEMANTICS_GATE.md`. It resolves strict UTF-8, no
normalization, whole-byte-sequence pretokenization, initial `bos`/`eos`/`pad`
allocation, byte/scalar offset rules, safe truncation, and exact-fingerprint
compatibility. Gate PR #26 was accepted at exact head
`bb3557b5b351ae2471b6107ded617eb15a0cee69`, squash-merged as
`e6234f46ad7e9ceb5d53e33f2a7deba174958db4`, and passed exact-head and
post-merge runs 56/57. `docs/P6_9_PRODUCTION_SEMANTICS_EVIDENCE.md` records the
implementation accepted at PR #27 exact head
`39c00f56654e20c998541f1269e61739db247a2a`, squash-merged as
`2b0776824713db0d47905bc2705a8b1d426d4856`, and verified by exact-head and
post-merge runs 58/59. Formal P6.9 closure and production training remain
blocked pending their separate gates.

## Initial completion evidence

P6 is complete only when the selected Tokenizer v1 implementation, artifacts,
conformance vectors, benchmarks, packaging boundary, security review, exact-head
CI, merge, and post-merge CI are all independently verified and recorded. A
repository scaffold, passing unit tests, or successful tokenizer-training run is
not sufficient by itself.
