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
production tokenizer. Artifact loading, streaming, production training, and final
semantic decisions remain unimplemented.

An experimental deterministic byte-BPE candidate is available for measured
comparison with the byte reference. It uses guaranteed byte fallback, immutable
in-memory learned data, bounded merge construction, explicit stop reasons, and
content-minimizing provenance. It is not an approved persistent artifact or the
selected Tokenizer v1 implementation.

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

The evaluation layer also provides bounded, immutable corpus manifests with
explicit domain, source, license identifier, and canonical UTF-8 content digest.
It records no implicit license approval and exposes no raw-content logging path.
Candidate metrics retain sample identity, domain, digest, counts, exact ratios,
status, and reversibility only; they do not copy sample text into reports.
Incomplete encodes do not receive compression ratios, and candidate identity
mismatches fail evaluation. These reports provide comparison evidence only and
do not select Tokenizer v1.
