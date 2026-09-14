# P6.6 — Canonical Artifact Implementation Evidence

## Status

**Implementation candidate — closure pending exact-head acceptance and merge**

The architecture/security gate was accepted at head
`77deb523f8410653e139bb50fd4fba8ee78814d5`, squash-merged as
`97c09999249214641a8ac79312cef5920f7551cf`, and verified by successful
post-merge `main` CI and policy runs 30 and 31.

## Implemented boundary

`cybersecgpt.tokenizer.artifact` provides only bounded in-memory byte
serialization and loading for the experimental P6.4 byte-BPE candidate. The
format uses the accepted magic, version, big-endian lengths, canonical payload,
and trailing SHA-256 digest. The loader verifies the envelope before parsing any
payload-controlled count or length, reconstructs the immutable candidate,
recomputes behavior identity, validates provenance and training configuration,
and requires an exact canonical-byte rebuild.

The artifact contains ordered sample metadata and content digests but no sample
text. It has no path, URL, archive, environment, callback, import, subprocess,
network, provider, or executable deserialization surface.

## Deterministic known vector

The independently asserted test vector has:

- artifact length: `1744` bytes;
- candidate fingerprint:
  `858fada45bcd428a9198e29da156f2c1b11f3922ecf985606b574eb6b293e71b`;
- artifact digest:
  `7e5f465535fc69b7f260369c1044ac569aca468c14b1b41215837c1c9d3edb25`;
- complete-byte SHA-256:
  `8206b62e3349e1cacf36b8451e199224717d1fa875494b1cf6098291ef844853`.

Tests verify repeated byte identity, load/rebuild identity, encode/decode
equivalence, behavior-fingerprint stability across provenance-only changes, and
artifact-digest sensitivity to those changes.

## Fail-closed conformance

Independent mutations cover wrong types; empty, short, oversized, truncated, and
trailing input; magic, version, declared length, and digest failures; invalid or
empty UTF-8 fields; invalid identifiers and digests; sample count, duplicate ID,
domain, provenance, finish status, vocabulary, token length, merge count,
merge-reference, descriptor, and canonical-rebuild disagreements. All failures
return no candidate and expose only a content-minimizing contract error.

The implementation does not grant authorization, approve a corpus, establish
model compatibility, add a proprietary provider, or begin a later P6 slice.

## Closure gate

P6.6 remains open until the exact implementation head passes unchanged Python
3.11–3.13 CI, build and exact distribution verification, final security/diff
review, project-owner exact-head `ACCEPT`, squash merge, and successful
post-merge `main` CI.
