# P6.10 — Corpus Manifest and Admission-Verifier Evidence

## Status

**Proposed implementation — exact-head owner acceptance required.**

This evidence implements only the manifest/admission-verifier permission granted
by the accepted P6.10 gate. It does not contain or approve a corpus snapshot,
acquire data, make a legal determination, train a tokenizer, promote an artifact,
finally select Tokenizer v1, or authorize later P6 work.

## Implemented boundary

`cybersecgpt.tokenizer.corpus_manifest` provides immutable, bounded contracts for:

- per-source origin, acquisition, revision and digest provenance;
- explicit reviewed rights, safety, contamination and purpose permissions;
- versioned deterministic transformations and configuration digests;
- ordered sample identities, domains, byte counts and content digests;
- bounded exclusion-reason counts;
- canonical length-prefixed manifest bytes and SHA-256 identity; and
- exact offline admission of locally supplied inert `bytes`.

The admission result contains only corpus/manifest identity, source IDs, sample
digests, domains and counts. It never retains or returns raw content. The module
performs no filesystem, archive, environment, credential, network, subprocess,
dynamic-loading, callback, plugin, deserialization or execution operation.

## Fail-closed behavior

Admission rejects:

- an unsealed or mutated manifest;
- unsupported schema, malformed identifiers/dates/digests or invalid bounds;
- duplicate source, sample, content-digest, transformation or exclusion IDs;
- samples referring to unknown sources or exceeding aggregate limits;
- rejected, unknown or revoked rights;
- rejected or unknown sensitive-data/contamination review;
- any missing acquisition, processing, training, derived-statistics or artifact-
  distribution permission;
- missing, extra, reordered, renamed, resized or digest-mismatched local content;
- cancellation, expired deadlines or incomplete clock inputs.

All failures use one content-minimizing error. Successful admission is integrity
evidence only and cannot grant authorization or widen classification, target,
provider/network, offline, deadline, budget or verification policy.

## Verification

The focused implementation suite covers canonical replay, identity sensitivity,
immutability, every rights/safety state, permissions, ordering, count/digest
binding, limits, cancellation/deadlines and content-minimizing output. The full
unchanged Python 3.11–3.13 CI, build and exact distribution matrix remains
required on the final review head.

## Remaining blockers

P6.10 remains open after this implementation. A real corpus snapshot must be
produced in the owning dataset-governance boundary and independently accepted at
its exact manifest digest with provenance, license, safety, contamination and
offline replay evidence. Only then may a separate production-training gate be
proposed. Training success will still not approve artifact promotion or final
Tokenizer v1 selection.
