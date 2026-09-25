# P6.9 — Tokenizer v1 Production Semantics Implementation Evidence

## Status

**Implementation verified — formal P6.9 closure acceptance required.**

The accepted architecture/security gate is
`P6_9_PRODUCTION_SEMANTICS_GATE.md`. It was accepted at PR #26 head
`bb3557b5b351ae2471b6107ded617eb15a0cee69`, squash-merged as
`e6234f46ad7e9ceb5d53e33f2a7deba174958db4`, and passed exact-head and
post-merge CI and policy runs 56/57. This evidence implements only that fixed
semantic profile over an immutable 512-token byte-BPE candidate.

## Implemented contract

`TokenizerV1SemanticCandidate` adds immutable typed encode/decode results and a
behavior fingerprint bound to candidate identity plus the accepted semantic
profile. Ordinary IDs are `0..511`; typed `bos`, `eos`, and `pad` IDs are
`512..514`. Literal special-looking strings remain ordinary untrusted text.
Decode either rejects specials, preserves typed role segments, or renders fixed
untrusted text; none of these modes interprets or authorizes content.

Encoding preserves strict UTF-8 bytes with no normalization. Optional
truncation includes requested specials in its budget, backs up to a UTF-8 scalar
boundary, never adds `eos` to a truncated result, and records the first omitted
byte. Optional offsets use canonical half-open byte spans; scalar spans exist
only at aligned endpoints. Compatibility accepts exact lowercase behavior
fingerprint equality and fails closed otherwise.

`TokenizerV1StreamingEncoder` retains bounded buffered finalization. Arbitrary
byte partitions produce the exact one-shot result. Invalid/incomplete UTF-8,
invalid requests, cancellation, deadlines, byte/chunk limits, and internal
encoding errors are terminal and discard buffered content.

## Verification scope

The implementation tests cover descriptor and fingerprint sensitivity, all
request validation branches, strict Unicode preservation, ordinary rendering of
special-looking text, typed special insertion and all decode modes, exact and
backtracked truncation, byte/scalar spans, exact compatibility rejection,
immutability, every two-way byte split, and terminal streaming failures.

Local unchanged validation passes Ruff, Black, strict mypy, and 235 tests with
100% statement and branch coverage over all 1,223 tokenizer source statements
and 354 branches. The implementation PR must independently pass the complete
Python 3.11–3.13 CI, repository/security validation, dependency consistency,
split-package imports, build, and exact distribution-boundary checks before
acceptance.

## Security boundary and exclusions

Inputs, token IDs, offsets, descriptors, fingerprints, segments, and decoded
text remain untrusted data. The implementation has no network, provider SDK,
dynamic code, callback, plugin, subprocess, file-loading, training, artifact
promotion, authorization, or execution authority. It does not approve a corpus
or license, train or select an artifact, claim model compatibility, finally
select Tokenizer v1, or begin a later P6 gate.

P6.9 is not closed by this proposal. Closure requires exact-head owner
acceptance, squash merge, successful post-merge `main` checks, a final complete
diff/security review, and separately accepted closure evidence.

## Verified implementation

The project owner explicitly accepted implementation PR #27 at exact head
`39c00f56654e20c998541f1269e61739db247a2a`. Exact-head CI and agent-policy
run 58 succeeded. The PR was squash-merged as
`2b0776824713db0d47905bc2705a8b1d426d4856`; post-merge `main` CI and
agent-policy run 59 succeeded at that commit, including Python 3.11–3.13,
100% source coverage, package build, and exact distribution verification.

The reviewed diff introduced only the accepted typed semantics, bounded
streaming behavior, public/distribution declarations, tests, and synchronized
documentation. It introduced no network or provider dependency, executable
artifact behavior, authorization path, corpus, training data, trained artifact,
or later P6 implementation.

Formal P6.9 closure remains pending exact-head acceptance and verified merge of
this evidence revision. That closure cannot approve a production corpus or
license, train or promote an artifact, finally select Tokenizer v1, or begin a
later P6 gate.
