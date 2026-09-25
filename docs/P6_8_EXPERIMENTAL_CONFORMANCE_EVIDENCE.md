# P6.8 — Experimental Conformance Vector Evidence

## Status

**P6.8 formally closed — exact-head acceptance, merge, and main checks verified.**

The architecture/security gate in `P6_8_EXPERIMENTAL_CONFORMANCE_GATE.md`
was accepted at PR #22 head `773ef632bf1201d232a99fa100afa144a3828ee6`,
squash-merged as `c863af96bfee43889b8c2be8d98e5d9c55868433`, and passed
exact-head and post-merge Python 3.11–3.13 CI/build/distribution and agent-policy
runs 48 and 49. This evidence is an implementation proposal built from that
verified main revision.

The project owner accepted implementation PR #23 at exact head
`d4b4b7826ebbeaeecf5a0ffc4303041f50b9a568`. Exact-head CI and
agent-policy run 50 succeeded. PR #23 was squash-merged as
`980ac53493cbef3ba6fad958e5fa78525682b7ab`, and post-merge `main` CI and
agent-policy run 51 succeeded at that commit, including Python 3.11–3.13,
100% source coverage, package build, and exact distribution verification.

## Fixed replay

[`evidence/P6_8_vectors.json`](evidence/P6_8_vectors.json) is an 18,023-byte
versioned UTF-8 JSON fixture with 20 bounded inert generated CC0-1.0 examples.
Its SHA-256 is
`481d0c11c6a51a9b7cd63133c34b51194fa69e87744e91ca87c619d64d2ade74`.
It binds the P6.4 construction manifest identity and ten sample digests, the
gate merge source revision, source/license identifier on every vector, input
digest, exact byte reference IDs, exact experimental BPE IDs, maximum token
count, and finish status. Case IDs cover empty input, whitespace, a null byte,
English/Khasi/Unicode/combining/precomposed input, literal special-looking
text, code, shell/PowerShell, generated logs, JSON/network/identifiers/rules,
security prose, and truncation/zero-token limits. All eight fixed evaluation
domains are represented. They are conformance examples, not an approved training
corpus or an exhaustive language/security-domain benchmark.

The BPE candidate uses the fixed P6.4 construction manifest with vocabulary
limit 512, merge budget 256, training byte limit 1 MiB, and source revision
`c863af96bfee43889b8c2be8d98e5d9c55868433`. Its behavior fingerprint is
`fe32ae1b111956debd74643c1273a47c1b4e542514b7b25a570d57b9bdbedd80`.
The canonical BPE artifact SHA-256 is
`782e64df973f9037103ee2f6cac29171fdc2342cead5c464595289c6f45f75b5`.
The script checks the separate payload artifact digest in the fixture, loaded
candidate identity, and canonical bytes.

Run `PYTHONPATH=src:. python scripts/verify_p6_8_vectors.py` from the repository
root to replay the vectors fully offline. The verifier checks fixture schema,
size, types, digests, provenance and exact construction identities before
comparing its independently implemented ordered-merge calculation, exact known
IDs, one-shot candidate encodes/decodes, and every two-chunk byte partition of
each short input. It then rejects invalid special-token insertion, invalid IDs
and UTF-8, cancelled/expired streams, and corrupted artifacts. The verifier
prints only the case count and fixture digest. The frozen fixture digest in the
test prevents a silent golden-vector refresh; changes require review.

## Security and limitations

The test fixtures are inert data and may not grant authorization or be parsed as
control instructions. No network, provider, external corpus, dynamic artifact
loading, executable data, raw-content logging, or production artifact release is
involved. The existing buffered stream emits no partial tokens. A 20-case fixed
fixture and an independent reference calculation do not prove all possible
inputs, portable resource ceilings, accepted corpus licensing, normalization or
offset policy, special-token allocation, model compatibility, or the final
Tokenizer v1 algorithm. Any change to experimental candidate behavior or
artifact schema needs renewed review and new fingerprint/vector evidence.

## Verified closure

The accepted gate, exact-head accepted implementation, pinned fixture and
identities, independent oracle, fail-closed negative evidence, complete diff and
security review, and successful pre/post-merge checks are recorded. The project
owner accepted closure PR #24 at exact head
`5972c304a37a42d3bc68e84cf7ebef73e28d36cd`; CI and policy run 52 passed.
It squash-merged as `a15bffed922c8712b8c9ae63869f3561d81ebc21`, and
post-merge `main` CI and policy run 53 passed at that exact commit. P6.8 is
formally closed only for the experimental conformance-vector slice and cannot
approve a production
tokenizer, corpus, model compatibility, final algorithm selection, or later P6
work.
