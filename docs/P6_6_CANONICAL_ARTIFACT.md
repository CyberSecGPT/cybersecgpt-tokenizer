# P6.6 — Canonical Non-Executable BPE Artifact and Fingerprint Gate

## Status

**Accepted and implemented — verified P6.6 closure**

The gate was accepted at exact head
`77deb523f8410653e139bb50fd4fba8ee78814d5` and merged as
`97c09999249214641a8ac79312cef5920f7551cf`. Its implementation was accepted at
exact head `b4f857687f3e838fcae7b1a7f27f62e52440ea50`, merged as
`92776213a1e8003682752a268af5e4bc0664457d`, and verified by pre- and post-merge
CI and policy runs 32 and 33.

This gate defines the first persistent encoding for the experimental byte-BPE
candidate recommended by P6.4. It does not approve a production Tokenizer v1
artifact, model compatibility, a training corpus, special tokens, offsets,
performance claims, or any later P6 work.

## Scope and repository boundary

This repository owns the tokenizer artifact byte schema, canonical serializer,
bounded in-memory loader, identity validation, and conformance evidence. It does
not own model packages, filesystem distribution, signing infrastructure, dataset
approval, or release promotion.

The first implementation serializes and loads bytes only. It provides no path,
URL, archive, plugin, callback, dynamic import, or executable-code loading API.
Filesystem placement and signed model bundles remain separate reviewed concerns.

## Identity decision

Two identities remain distinct:

- `candidate_fingerprint` is the existing SHA-256 behavior identity derived from
  the ordered BPE merges and learned token bytes. Any behavior change must change
  it.
- `artifact_digest` is SHA-256 over the complete canonical envelope before its
  trailing digest. It also binds provenance and serialization metadata.

A provenance-only change alters `artifact_digest` but not
`candidate_fingerprint`. Matching vocabulary size, path, filename, repository
revision, mutable label, or artifact digest alone never establishes model
compatibility. This evaluation artifact must not be advertised as an approved
production model/tokenizer compatibility relation.

## Canonical binary envelope

The format identifier is `csgpt-experimental-bpe-artifact-v1`. The byte order is
network order (unsigned big-endian), with no padding, locale, platform-native
integer, floating-point value, timestamp, host data, or nondeterministic field.

The envelope is exactly:

1. eight-byte magic `CSGPTB1\0`;
2. unsigned 16-bit format version `1`;
3. unsigned 32-bit payload length;
4. the canonical payload of exactly that length; and
5. a 32-byte SHA-256 digest of fields 1–4.

The payload uses unsigned 16-bit length-prefixed strict UTF-8 strings and
unsigned 32-bit integers. Its fixed field order is:

1. format identifier;
2. tokenizer ID, contract version, algorithm ID, artifact-format profile,
   normalization profile, pretokenization profile, and candidate fingerprint;
3. manifest ID and version;
4. ordered sample count, then for each sample: ID, domain, source reference,
   license identifier, and content SHA-256;
5. requested vocabulary limit, merge budget, maximum training bytes, source
   revision, implementation version, and construction finish status;
6. vocabulary count, then every token in token-ID order as an unsigned 32-bit
   byte length followed by exact bytes; and
7. merge count, then every merge in order as left, right, and output unsigned
   32-bit token IDs.

No field is optional. Unknown versions, missing fields, duplicate or reordered
sample identities, invalid UTF-8 metadata, trailing payload data, or trailing
envelope data are rejected. Serialization of the loaded record must reproduce
the original bytes exactly.

## Provenance binding

Serialization consumes both a `ByteBpeTrainingResult` and its exact validated
`EvaluationManifest`. It verifies manifest identity, version, ordered sample
digests, construction settings, candidate identity, and implementation version
before encoding. It stores sample metadata but never sample text.

License identifiers are provenance data, not license approval. Training success,
serialization success, or a valid digest cannot approve a corpus or artifact.

## Bounds and validation order

- Maximum complete artifact: `16 MiB`.
- Format identifier and descriptor identifiers retain existing identifier bounds.
- Sample count: existing `MAX_EVALUATION_SAMPLES`.
- Vocabulary: `256..512` for this fixed P6.4 candidate artifact.
- Merge count: `0..256` and exactly `vocabulary_count - 256`.
- Each learned token: `1..1 MiB`; total token bytes must fit the artifact limit.
- Sample IDs, sources, and license identifiers retain the manifest's 256-character
  limit; every digest is exact lowercase SHA-256.
- Every merge output ID is consecutive from `256`; inputs reference only earlier
  IDs; learned bytes equal the concatenation of their referenced token bytes.

The loader validates, in order: immutable `bytes` type, total envelope size,
minimum length, magic, version, declared payload length, exact envelope length,
and digest. Only then may it parse payload counts and lengths. Before every slice,
decode, loop, tuple construction, or token allocation it validates the controlling
length/count and remaining bytes. It rejects rather than clamps, repairs,
substitutes, ignores, or partially loads malformed input.

After parsing, the loader reconstructs the existing immutable
`ByteBpeCandidate`, recomputes its descriptor fingerprint, compares every stored
descriptor field, validates all provenance/configuration fields, and reserializes
for exact canonical-byte equality. Any disagreement is an integrity failure.

## Security invariants

- Artifact bytes and all metadata are untrusted data and never authorization,
  executable instructions, corpus approval, or model compatibility.
- Loading performs no code execution, deserialization by `pickle`/marshal,
  expression evaluation, import, plugin/callback invocation, subprocess, file or
  network access, provider call, environment lookup, or external reference.
- Validation precedes attacker-controlled allocation and iteration.
- Failures return no candidate, never fall back to another artifact/candidate,
  and cannot widen classification, target scope, provider/network policy,
  offline requirements, deadlines, budgets, or verification.
- Raw sample text, decoded output, secrets, paths, host identity, and timing do
  not enter the artifact or validation evidence.
- Core serialization and loading remain deterministic, standard-library-only,
  local/offline, and independent of proprietary providers.

## Required conformance evidence

The implementation PR must demonstrate:

- byte-identical repeated serialization and load/serialize round trips;
- stable known-vector bytes and both identity digests;
- candidate encode/decode equivalence before and after loading;
- artifact-digest sensitivity to every serialized provenance field;
- candidate-fingerprint sensitivity to every behavior-defining merge/token field;
- behavior identity stability under provenance-only changes;
- rejection of wrong type, empty/truncated/oversized input, magic, version,
  length, digest, UTF-8, identifier, count, token-length, token-byte, merge-order,
  merge-reference, descriptor, provenance, canonical-order, and trailing-data
  mutations;
- explicit boundary tests for every accepted maximum and minimum; and
- content-minimizing errors and evidence with no raw sample text.

Tests must construct malformed bytes independently rather than using only the
serializer as their generator. A successful round trip alone is insufficient.

## Required merge evidence

Before implementation begins, this exact gate revision requires explicit
project-owner architecture/security `ACCEPT`, successful exact-head CI, squash
merge, and successful post-merge `main` CI.

Before implementation merges, its exact PR head requires unchanged Ruff, Black,
strict mypy, repository/security validation, dependency consistency,
split-package import, pytest with 100% source coverage on Python 3.11–3.13,
package build, exact distribution verification, complete security/diff review,
project-owner exact-head acceptance, squash merge, and post-merge `main` CI.

P6.6 completion supplies canonical experimental artifact and size evidence only.
It does not authorize performance, broader conformance, corpus review, final
Tokenizer v1 selection, or a later P6 gate.
