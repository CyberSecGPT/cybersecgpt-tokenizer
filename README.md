# CyberSecGPT Tokenizer

Authoritative repository for first-party CyberSecGPT tokenizer training,
execution, vocabulary and special-token management, artifacts, manifests, and
conformance vectors.

This repository is entering roadmap milestone **P6 — CyberSecGPT Tokenizer v1**.
No tokenizer algorithm, vocabulary, trained artifact, or production-ready
implementation is claimed by this bootstrap commit.

Canonical architecture and contract:
[CyberSecGPT tokenizer contract](https://github.com/CyberSecGPT/cybersecgpt-docs/blob/main/docs/specifications/tokenizer-contract.md).

Core operation must remain local/offline and must not depend on proprietary remote
AI APIs or external-provider tokenizers.

## Current implementation

P6 is in progress. Immutable, bounded contracts now include a fixed 256-token
UTF-8 byte reference candidate and candidate-neutral deterministic structural
evaluation reports. Reports bind the manifest identity, candidate algorithm and
fingerprint, token limit, sample digests, exact reduced count ratios, completion
status, decode success, and reversibility without retaining raw sample text or
recording nondeterministic timing.
The reference exists only to establish a reproducible comparison baseline; it is
not the selected Tokenizer v1 algorithm, vocabulary, invalid-input policy, or
production tokenizer. Canonical artifact loading, production training, and final
semantic decisions remain unimplemented.

An experimental deterministic byte-BPE candidate is available for measured
comparison with the byte reference. It uses guaranteed byte fallback, immutable
in-memory learned data, bounded merge construction, explicit stop reasons, and
content-minimizing provenance. It is not an approved persistent artifact or the
selected Tokenizer v1 implementation.

An experimental deterministic byte-frequency Unigram candidate is also
available for candidate-neutral comparison. It discovers overlapping byte
pieces within fixed resource ceilings, derives exact integer costs, uses stable
dynamic-programming segmentation with byte fallback, and retains only immutable
in-memory state and content-minimizing provenance. It does not select Tokenizer
v1 or approve a persistent artifact.

Tokenizer input, artifacts, metadata, and output are untrusted data. Tokenizer
behavior and output never create an authorization grant, lower classification,
widen target scope or provider/network access, relax offline operation, extend a
deadline or budget, or reduce verification requirements.

See [P6 acceptance gates](P6_ACCEPTANCE.md) and
[architecture](docs/ARCHITECTURE.md).

The accepted [experimental byte-BPE candidate gate](docs/P6_2_BYTE_BPE_CANDIDATE.md)
defines its fair, deterministic comparison profile. Neither the gate nor the
candidate selects the production tokenizer or constrains the later Unigram
candidate.

The accepted [experimental byte-Unigram gate](docs/P6_3_UNIGRAM_CANDIDATE.md)
defines bounded candidate discovery, integer-only scoring, deterministic
segmentation, byte fallback, and security limits. Its comparison-only
implementation does not approve production semantics, algorithm selection,
training data, or artifact serialization.

The accepted [controlled algorithm benchmark gate](docs/P6_4_ALGORITHM_BENCHMARK.md)
and [reproducible evidence](docs/P6_4_ALGORITHM_BENCHMARK_EVIDENCE.md) use
separate generated construction/evaluation manifests, equal candidate settings,
deterministic domain-level structural evidence, and a fail-closed recommendation
rule. The controlled result recommends experimental byte-BPE for the remaining
gates; it does not select Tokenizer v1.

The accepted [streaming contract gate](docs/P6_5_STREAMING_CONTRACT.md) and
[implementation evidence](docs/P6_5_STREAMING_EVIDENCE.md) define bounded
byte-chunk ingestion, strict UTF-8 finalization, deterministic lifecycle failures,
and exact one-shot BPE equivalence. Because no safe progressive BPE emission
frontier has been proven, the implementation permits output only after successful
finalization and does not claim incremental token delivery.
P6.5 is verified complete at merge
`345846ac0e02b3bd0c265b1d2f4649d0774cade9`; later Tokenizer v1 gates remain
unimplemented.

The accepted [canonical artifact gate](docs/P6_6_CANONICAL_ARTIFACT.md) and
[implementation evidence](docs/P6_6_CANONICAL_ARTIFACT_EVIDENCE.md) define and
exercise a bounded, non-executable binary envelope. The implementation separates
behavior fingerprint from artifact digest, binds content-minimizing provenance,
and validates the envelope before payload-controlled allocation. P6.6 is verified
complete at implementation merge
`92776213a1e8003682752a268af5e4bc0664457d`; later P6 gates remain unimplemented.

The evaluation layer also provides bounded, immutable corpus manifests with
explicit domain, source, license identifier, and canonical UTF-8 content digest.
It records no implicit license approval and exposes no raw-content logging path.
Candidate metrics retain sample identity, domain, digest, counts, exact ratios,
status, and reversibility only; they do not copy sample text into reports.
Incomplete encodes do not receive compression ratios, and candidate identity
mismatches fail evaluation. These reports provide comparison evidence only and
do not select Tokenizer v1.

The [accepted P6.7 performance gate](docs/P6_7_PERFORMANCE_RESOURCE_GATE.md)
and [verified implementation evidence](docs/P6_7_PERFORMANCE_EVIDENCE.md)
measure the fixed generated candidate comparison. Trial times and traced Python
allocations remain separate from deterministic structural reports and are not
portable hard limits. They grant no authorization, artifact/corpus approval, or
production tokenizer selection. The implementation merged as
`32b7aef9bdcac29d66bdf2857ef3f84bc0444853` with successful exact-head and
post-merge checks. P6.7 closure PR #20 was accepted at exact head
`6cb6095e7c932aea300b4d5419573e61460af72f`, squash-merged as
`8a8d2cfa40b6b790528292cc492dc79597dc66b1`, and passed exact-head and
post-merge CI and agent-policy runs 44 and 45. P6.7 is formally closed; later
Tokenizer v1 gates remain open.
