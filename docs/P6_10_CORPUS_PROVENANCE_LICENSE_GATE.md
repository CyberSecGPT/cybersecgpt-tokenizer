# P6.10 — Tokenizer v1 Corpus Provenance and License Gate

## Status and decision boundary

**Proposed — exact-head architecture/security acceptance required.**

P6.9 closed the prospective Tokenizer v1 semantic profile. This gate defines
the evidence that an exact, immutable tokenizer-training corpus snapshot must
carry before production tokenizer training may begin. It does not acquire or
curate datasets, approve a corpus, train a tokenizer, promote an artifact,
finally select Tokenizer v1, or authorize later P6 work.

Dataset acquisition, source governance, processing, and reusable corpus
publication belong to `cybersecgpt-datasets`. This repository owns only the
tokenizer-specific admission manifest and deterministic consumption of a
separately approved snapshot.

## Exact snapshot and manifest

Training input must have a canonical versioned manifest whose digest binds:

- schema/version and immutable corpus ID;
- each source's stable ID, origin, acquisition method/date, revision, and digest;
- SPDX expression or explicit rights record, obligations, restrictions, review
  decision, reviewer, and date;
- deterministic inclusion, sampling, ordering, deduplication, filtering,
  decoding, normalization, and redaction rules and tool identities;
- per-domain/source counts before and after processing, exclusion-reason counts,
  and canonical ordered sample digests; and
- approved purpose, artifact distribution terms, limitations, and manifest
  digest.

URLs, filenames, branches, aggregate counts, unsubstantiated license labels, or
repository revisions alone are not identity. Any content, provenance, rights,
transformation, order, or sampling change creates a new identity.

## Admission and licensing policy

- Every sample traces to a reviewed source. Unknown, missing, ambiguous,
  contradictory, expired, revoked, or incompatible rights fail the snapshot
  closed; they are never inferred to be permissive.
- Approval separately covers acquisition, processing, training, derived
  statistics, and artifact distribution. Training permission does not imply
  redistribution permission.
- Combined-snapshot compatibility and notices are reviewed. Required notices
  remain outside the behavior fingerprint but inside provenance identity.
- Public availability, robots access, an API response, or no copyright notice is
  not permission. Proprietary-provider terms, credentials, hosted tokenizer
  output, or remotely generated intelligence cannot be mandatory inputs.
- Synthetic samples require generator identity/policy, input provenance, rights
  basis, and contamination review.

## Content and security policy

- Exclude secrets, credentials, authentication material, private keys, personal
  or regulated data, private communications, and confidential data. Quarantined
  content is never committed here or emitted in CI.
- Malware, exploit, shell, detection-rule, telemetry, and threat-intelligence
  text may enter only as authorized inert data with provenance and a defensive
  tokenizer purpose. Corpus text is never executed, imported, interpreted as
  instructions, or allowed to grant authority.
- Apply byte/sample ceilings, decompression/nesting limits, strict decoding,
  path-traversal rejection, duplicate controls, and bounded processing. Reject
  executable loaders, pickle/marshal, callbacks, plugins, external references,
  and implicit network fetches.
- Raw samples and sensitive values are not logged or reported. Evidence uses
  stable IDs, digests, counts, decisions, and content-minimized failures.
- Admission cannot widen authorization, classification, target scope,
  provider/network policy, offline requirements, deadlines, resource budgets,
  or verification requirements.

## Reproducibility and repository boundary

- Pinned authorized inputs and versioned deterministic transformations must
  reproduce the manifest and ordered sample digests offline.
- Acquisition, credentials, legal review, quarantine, and raw storage stay
  outside tokenizer runtime and this repository. No samples or credentials enter
  the source distribution.
- A later trainer may accept only the approved manifest digest and local bounded
  content whose digests match. Missing, extra, reordered, changed, or unreadable
  samples fail before training.
- Rights or integrity changes invalidate the snapshot for new training and block
  promotion; no source or corpus may be silently substituted.

## Required acceptance evidence

Before this gate can close, a separately reviewed proposal must provide:

1. the canonical manifest schema and digest construction;
2. a content-minimized proposed-snapshot manifest with every rights decision;
3. deterministic construction/replay verification and domain coverage;
4. secret, personal-data, contamination, duplication, malformed-input, and
   license-policy negative-case evidence;
5. confirmation that no raw corpus, credentials, proprietary-provider
   dependency, executable input, or network requirement entered the package;
6. an owner architecture/security/license `ACCEPT` decision bound to the exact
   reviewed head and manifest digest; and
7. unchanged Python 3.11–3.13 Ruff, Black, strict mypy, repository/security,
   dependency, split-import, pytest with 100% source coverage, build, and exact
   distribution-boundary checks.

Gate acceptance authorizes only a separately reviewed manifest/admission
verifier. The snapshot must then be accepted at its own exact digest before
production training. Training success remains insufficient for artifact
promotion or final Tokenizer v1 selection.
