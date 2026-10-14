# P6.10 — Corpus Manifest and Admission-Verifier Evidence

## Status

**Accepted implementation; exact snapshot admission separately verified.**

The project owner accepted PR #31 implementation head
`69d202f36010658a473fd99cff2f7186af53ab31` in comment `5904865101`.
It was squash-merged as `0d3b1bff2328392a5b385b0c5b2bd7d08177b792`;
exact-head and post-merge CI/policy runs 66/67 passed.

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
binding, limits, cancellation/deadlines and content-minimizing output. The final
implementation head passed the unchanged Python 3.11–3.13 CI, 100% source
coverage, build, exact distribution, and agent-policy matrix in run 66; merged
`main` passed run 67.

## Verified snapshot boundary

The dataset owner later accepted datasets PR #8 head
`0cadfd93a5d9ac528075fba4d836322630ca5557`, dataset manifest
`374773d05a9aae380ad88f477210da75d40adc90cca1afac9ee8800a93656fef`,
and tokenizer admission manifest
`a2f676b2717e86717d469b9274b91cb3c3bf48daf58e83efe97221e4d5a7151a`
in comment `6162064709`. The snapshot was squash-merged as
`a8573904fd944e9be26e911d768e7335e4bdf1e0`; exact-head and post-merge
CI runs 14/15 passed.

This verifies P6.10's exact snapshot-admission prerequisite. It authorizes only
the separately reviewed P6.11 training-run gate. It does not authorize training,
artifact persistence, promotion or signing, final Tokenizer v1 selection, model
work, P7, execution authority, or any policy widening.
