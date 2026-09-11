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

This reference is benchmark infrastructure, not selection of the Tokenizer v1
algorithm or its production invalid-input policy. BPE and Unigram candidates,
normalization, pretokenization, offsets, artifact encoding, special-token
allocation, streaming, corpus approval, and training remain gated by
`P6_ACCEPTANCE.md` and `docs/P6_1_ALGORITHM_EVALUATION.md`.

`docs/P6_2_BYTE_BPE_CANDIDATE.md` proposes evaluation-only semantics and
deterministic training rules for byte-BPE. It deliberately blocks BPE code until
exact-revision architecture/security acceptance and leaves Unigram numeric
behavior, persistent artifacts, and production Tokenizer v1 behavior unresolved.

All tokenizer data is untrusted. Results may describe tokenization behavior but
cannot grant permissions, change classification, widen target scope, weaken
provider/network or offline policy, extend deadlines or budgets, or reduce
verification requirements.
