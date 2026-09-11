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
UTF-8 byte reference candidate and deterministic structural evaluation metrics.
The reference exists only to establish a reproducible comparison baseline; it is
not the selected Tokenizer v1 algorithm, vocabulary, invalid-input policy, or
production tokenizer. Artifact loading, streaming, training, and final semantic
decisions remain unimplemented.

Tokenizer input, artifacts, metadata, and output are untrusted data. Tokenizer
behavior and output never create an authorization grant, lower classification,
widen target scope or provider/network access, relax offline operation, extend a
deadline or budget, or reduce verification requirements.

See [P6 acceptance gates](P6_ACCEPTANCE.md) and
[architecture](docs/ARCHITECTURE.md).

The proposed [experimental byte-BPE candidate gate](docs/P6_2_BYTE_BPE_CANDIDATE.md)
defines a fair, deterministic comparison profile for the next candidate. It must
be accepted before BPE is implemented and does not select the production
tokenizer or constrain the later Unigram candidate.

The evaluation layer also provides bounded, immutable corpus manifests with
explicit domain, source, license identifier, and canonical UTF-8 content digest.
It records no implicit license approval and exposes no raw-content logging path.
Reference metrics retain sample identity, domain, digest, counts, status, and
reversibility only; they do not copy sample text into reports.
