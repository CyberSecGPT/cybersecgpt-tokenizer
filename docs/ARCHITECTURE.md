# Architecture

## Milestone

P6 — CyberSecGPT Tokenizer v1.

## Ownership

This repository owns first-party tokenizer training, execution, normalization,
vocabulary and special-token management, artifacts, manifests, and conformance
vectors. It does not own model, inference, general training orchestration,
datasets, product surfaces, or authorization.

## Current boundary

The first executable slice provides immutable and bounded public contracts only.
It deliberately does not select or implement a tokenizer algorithm, normalization
or pretokenization behavior, vocabulary, artifact encoding, special-token
allocation, or training corpus. Those decisions remain gated by
`P6_ACCEPTANCE.md`.

All tokenizer data is untrusted. Results may describe tokenization behavior but
cannot grant permissions, change classification, widen target scope, weaken
provider/network or offline policy, extend deadlines or budgets, or reduce
verification requirements.
