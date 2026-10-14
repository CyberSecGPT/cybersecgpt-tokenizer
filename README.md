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

The accepted [P6.9 production semantics gate](docs/P6_9_PRODUCTION_SEMANTICS_GATE.md)
defines the prospective Tokenizer v1 strict-UTF-8, normalization,
pretokenization, offset, truncation, special-token, fingerprint, and exact
compatibility rules. Its [implementation evidence](docs/P6_9_PRODUCTION_SEMANTICS_EVIDENCE.md)
was accepted at PR #27 head `39c00f56654e20c998541f1269e61739db247a2a`,
squash-merged as `2b0776824713db0d47905bc2705a8b1d426d4856`, and passed
pre/post-merge runs 58/59. Closure PR #28 was accepted at exact head
`30b5a78fb1dce5d539c5172efc1f27784b6fd850`, squash-merged as
`23ee8aedaa99b5341919a60aabc0b1191aa9e329`, and passed pre/post-merge runs
60/61. P6.9 is formally closed; this does not approve a corpus, train an
artifact, or finally select Tokenizer v1.

The accepted [P6.10 corpus provenance and license gate](docs/P6_10_CORPUS_PROVENANCE_LICENSE_GATE.md)
defines exact snapshot identity, per-source rights review, deterministic offline
replay, sensitive-content exclusion, and repository boundaries. The gate was
accepted at PR #30 exact head
`bcbfd04b8a3c6439c07567f365ba91010822ce32`, merged as
`f69b22b88a8c053a360cb26c57a9ddd311a7ec43`, and passed runs 64/65. The
accepted [manifest-verifier evidence](docs/P6_10_CORPUS_MANIFEST_EVIDENCE.md)
adds canonical provenance/rights records and exact offline byte admission. Its
implementation was accepted at PR #31 head
`69d202f36010658a473fd99cff2f7186af53ab31`, merged as
`0d3b1bff2328392a5b385b0c5b2bd7d08177b792`, and passed runs 66/67.

The dataset owner then accepted the exact first-party snapshot at datasets PR #8
head `0cadfd93a5d9ac528075fba4d836322630ca5557`, dataset manifest
`374773d05a9aae380ad88f477210da75d40adc90cca1afac9ee8800a93656fef`,
and tokenizer admission manifest
`a2f676b2717e86717d469b9274b91cb3c3bf48daf58e83efe97221e4d5a7151a`.
It was merged as `a8573904fd944e9be26e911d768e7335e4bdf1e0` and passed
pre/post-merge runs 14/15. This closes the P6.10 corpus-admission prerequisite
only; it does not authorize training or artifact promotion.

The proposed [P6.11 deterministic training-run gate](docs/P6_11_TOKENIZER_V1_TRAINING_RUN_GATE.md)
binds the exact accepted snapshot to a fixed 512-ordinary-token byte-BPE run,
separate digest-disjoint holdout evaluation, repeated Python 3.11–3.13 replay,
bounded lifecycle controls, and content-minimized evidence. No training may
begin until that exact gate head is accepted, merged, and verified on `main`.
Training success will not approve persistence, signing, promotion, compatibility,
final Tokenizer v1 selection, model work, or P7.

The proposed [P6.8 experimental conformance-vector gate](docs/P6_8_EXPERIMENTAL_CONFORMANCE_GATE.md)
defines independent known vectors and failure evidence for the existing
candidates, streaming behavior, and BPE artifact. It awaits exact-head
architecture/security acceptance before implementation; it does not approve
production semantics or a training corpus.

The proposed [P6.8 conformance evidence](docs/P6_8_EXPERIMENTAL_CONFORMANCE_EVIDENCE.md)
replays 20 pinned generated vectors with exact IDs, byte-split BPE streaming,
artifact identity, and fail-closed negative cases. The implementation was
accepted at PR #23 head `d4b4b7826ebbeaeecf5a0ffc4303041f50b9a568`,
squash-merged as `980ac53493cbef3ba6fad958e5fa78525682b7ab`, and passed
pre/post-merge CI and policy runs 50/51. Closure PR #24 was accepted at exact
head `5972c304a37a42d3bc68e84cf7ebef73e28d36cd`, squash-merged as
`a15bffed922c8712b8c9ae63869f3561d81ebc21`, and passed pre/post-merge
runs 52/53. P6.8 is formally closed; this evidence does not select Tokenizer v1.
