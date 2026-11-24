# P6.12 — Tokenizer v1 Artifact Packaging, Signing, and Promotion Gate

## Proposed amendment — ADR-0012 alignment

This amendment does not take effect until separately reviewed, accepted at its
exact head, squash-merged, and verified on main. The original approval did not
accept this amendment.

[ADR-0012](https://github.com/CyberSecGPT/cybersecgpt-docs/blob/8faa2f801eb87b6b8fb62e81976f33a5c6974b98/docs/decisions/ADR-0012-artifact-signing-and-promotion-trust.md)
is accepted and merged. It resolves the architecture prerequisite; older
statements below calling the signing profile and trust-root ownership unresolved
are retained as historical context, not current authority. Operational readiness
is still unverified and all release gates remain fail closed.

The following sequence supersedes the ordered proposal sequence below:

1. Governance approves the documented source-rights basis and policy for
   constructing and independently evaluating an inert unsigned candidate. This
   grants no distribution permission.
2. A separately reviewed tokenizer implementation constructs and validates the
   candidate under that policy. Freeze the exact payload and manifest digests,
   byte counts, source revision, and pre-construction policy identity.
3. Independent evaluation produces detached evidence bound to that exact unsigned
   candidate. Governance then separately approves distribution of the exact
   unsigned candidate and evaluation evidence, including licence, notices,
   audience, restrictions, expiry, and revocation. Missing or conflicting
   evidence blocks progression. A changed candidate requires renewed evaluation
   and approval.
4. DevOps may sign only after current approval and all ADR-0012 trust-root,
   provenance, and operational controls are independently verified. The signed
   release identity first exists after signing and references the frozen unsigned
   identity. Publication and promotion records reference the signed release,
   never the reverse. Verify offline admission, revocation and rollback before
   recording P6 closure.

For the unsigned manifest requirements below, bind only pre-existing evidence,
including the P6.11 evaluation identity and pre-construction rights/policy
identity. Do not embed a self-digest, the later independent evaluation of the
packaged candidate, exact-candidate distribution approval, detached signature,
or publication/promotion records. These are separate downstream records. An
unsigned candidate is not authorized for distribution or promotion.

No candidate construction, release, key material, signing, network access,
dependency, or implementation change is authorized by this amendment alone.
Every later gate still requires its own separate review and approval.

## Status and decision boundary

**Proposed — exact-head project-owner architecture/security/release/licence
acceptance is required before any implementation.**

P6.11 produced and independently verified one deterministic in-memory candidate
from the exact accepted corpus snapshot. This gate defines the next boundary:
how those already reviewed bytes and identities may become an inert unsigned
release candidate, and which separate authorities must act before any artifact
can be signed, published, promoted, installed, or declared Tokenizer v1.

This gate does not write an artifact, select a signing technology or trust root,
create or use a key, publish to a registry, approve a licence, issue a promotion
decision, install or load a package, finally select Tokenizer v1, begin model
work, or begin P7. Acceptance may authorize only the ordered, separately
reviewed proposals described below.

## Verified P6.11 baseline

The proposed boundary is fixed to:

- accepted P6.11 implementation PR #33 head
  `c0c4b52703b8df176af725b9c9446a0808cbe5e9`;
- project-owner acceptance comment `7037061085`;
- squash merge `9c2dd75e21c6eae0cfe3cc090963666f219cba19`;
- successful exact-head CI and agent-policy run 70 and post-merge `main` CI and
  agent-policy run 71;
- published tokenizer implementation commit
  `1b1519233b54f55326709b198ad7e95e9834219f`;
- accepted dataset snapshot
  `a8573904fd944e9be26e911d768e7335e4bdf1e0` and dataset implementation
  `cfda1cea94e0501a2b9c67491d47e04294ce35d8`;
- dataset manifest
  `374773d05a9aae380ad88f477210da75d40adc90cca1afac9ee8800a93656fef`,
  dataset replay
  `002ea5b42cd67d94dcc3e03531c272499963a5a9ffa0171ab01adfdb8a554206`,
  and tokenizer admission manifest
  `a2f676b2717e86717d469b9274b91cb3c3bf48daf58e83efe97221e4d5a7151a`;
- ordinary-candidate fingerprint
  `072d8850d68f5c16b152c87d15eb01bd2e86100a6012be9fea05fbfa36410e5d`;
- P6.9 behavior fingerprint
  `ef23540517cb696d57f722c43663e8bc52dac9d9a5e2f7ff9d72ab6e8d0bd347`;
- evaluation digest
  `4833fb4b840297a553127630d9555cfcc8653db501b844735d40a8900e320172`;
- identity-bound conformance digest
  `0d30e646dfc9c1d658b0931b50dd0a5e1616a800a997108cdfe822dcd0732581`;
  and
- canonical training-evidence digest
  `279d62e1c7617ed8d873509cfc8947ef8ae816827495166335d187a61ec00ab0`.

Any different source revision, corpus byte or order, manifest, construction
setting, candidate, behavior profile, evaluation result, conformance result, or
evidence identity is a different release-candidate proposal and requires renewed
review. A branch, tag, filename, URL, registry channel, semantic version, or
successful prior run is never a substitute for these immutable identities.

No artifact was persisted, signed, published, promoted, installed, or selected
by P6.11.

## Canonical ownership and authority split

The artifact flow must preserve the accepted repository map, ADR-0010, and the
acyclic dependency graph.

| Responsibility | Authoritative owner | P6.12 boundary |
| --- | --- | --- |
| Tokenizer payload, domain manifest, behavior identity, compatibility, and conformance fixtures | `cybersecgpt-tokenizer` | May deterministically construct and validate inert bytes; cannot approve or promote them |
| Common artifact references, content-digest types, and compatibility-result primitives | `cybersecgpt-foundation` | Must not be duplicated by a tokenizer-private cross-platform envelope |
| Independent quality, safety, security, and compatibility report | `cybersecgpt-evaluation` | Supplies promotion evidence; cannot promote the artifact it evaluates |
| Licence, risk, exception, and approval policy | `cybersecgpt-governance` | Supplies an immutable approval/policy artifact; does not execute promotion |
| Reproducible build, SBOM, provenance, signing integration, publication, promotion, and rollback | `cybersecgpt-devops` | Owns operational release actions; production code never imports DevOps code |
| Registry, secret, identity, storage, and recovery resources | `cybersecgpt-infrastructure` | Supplies protected resources through public operational interfaces, not tokenizer code |
| Artifact consumer | later runtime/inference owner | Verifies identity, policy, compatibility, and signature requirements before loading |

Tokenizer output, evaluation output, a signature, CI success, or a registry
upload cannot grant authorization or create its own approval. Separation of
duties is mandatory: construction, independent evaluation, governance approval,
signing/promotion, and consumption remain distinct decisions and evidence.

## Ordered proposal sequence

Gate acceptance authorizes proposals only in this order:

1. a canonical architecture decision in `cybersecgpt-docs` resolves the signing
   authority, trust-root ownership, approved signature/attestation profile,
   verification and revocation semantics, and promotion-state contract;
2. an applicable governance decision records the tokenizer artifact licence,
   notices, distribution restrictions, approval roles, and exception policy;
3. a tokenizer implementation proposal constructs and validates an unsigned,
   inert release candidate bound to every accepted identity in this gate;
4. an independent evaluation proposal verifies that exact unsigned candidate
   and emits a promotion recommendation or an explicit fail-closed result;
5. a DevOps proposal builds, attests, signs, publishes, promotes, and tests
   rollback for only the exact accepted bytes under the accepted policy; and
6. a final P6 closure proposal binds every exact head, digest, decision,
   signature/attestation, publication identity, promotion record, and
   post-promotion verification result.

No later item may begin merely because an earlier proposal exists. Each item
requires its own exact-head review, unchanged required checks, acceptance,
squash merge, and post-merge verification. An unavailable owner implementation
or unresolved policy is a blocker, not permission for the tokenizer repository
to absorb that authority.

## Unsigned release-candidate boundary

The tokenizer-owned implementation proposal may expose only deterministic,
bounded, standard-library, bytes-oriented construction and validation. It must:

- reconstruct the exact P6.11 candidate from the accepted snapshot or consume a
  successful immutable P6.11 result in the same process;
- serialize the ordinary BPE payload with the already accepted P6.6 canonical
  non-executable envelope without changing or relabelling its byte schema;
- bind the P6.9 semantic profile and exact behavior fingerprint outside the
  ordinary-candidate payload so special-token, truncation, offset, streaming,
  strict-UTF-8, and compatibility behavior cannot be omitted;
- bind the accepted corpus, training, evaluation, conformance, provenance,
  licence-status, source-revision, and implementation identities;
- bind exact payload and manifest byte counts and SHA-256 digests;
- state that the lifecycle is `unsigned_release_candidate` and that promotion
  is not authorized;
- emit no raw corpus, decoded sample, learned-token rendering, credential,
  secret, host, path, clock, process, environment, or network data; and
- reproduce byte-identical payload, manifest, identities, and validation results
  on Python 3.11, 3.12, and 3.13.

The P6.6 identifier `csgpt-experimental-bpe-artifact-v1` remains an exact payload
format identity. The later implementation must not call it a different format or
claim that a mutable filename or wrapper changed its meaning. Any new portable
container or incompatible payload format requires its own canonical architecture
decision before implementation.

The tokenizer package must retain zero runtime dependencies and must not gain a
filesystem path, URL, registry, archive extraction, key, signature, network,
subprocess, plugin, callback, dynamic-import, environment-discovery, installer,
or automatic-loading API. A caller may receive immutable canonical bytes; the
operational release plane owns where accepted bytes are written.

## Minimum domain-manifest facts

The tokenizer-owned unsigned record must bind, at minimum:

- manifest schema identifier and version, artifact kind, tokenizer contract
  version, payload format identifier, and semantic-profile identifier;
- immutable artifact/payload digest and byte count;
- ordinary-candidate and P6.9 behavior fingerprints;
- ordinary vocabulary, merge count, complete byte fallback, and exact
  `bos=512`, `eos=513`, `pad=514` allocation;
- tokenizer source revision and the exact P6.11 implementation, dataset,
  admission, evaluation, conformance, and evidence identities above;
- provenance and licence-status identity, distribution restriction state, and
  required-notice digest without embedding raw legal or corpus content;
- reproducibility profile, supported Python matrix, validation result identity,
  and known limitations;
- explicit unsigned state and the accepted signature-policy identifier only
  after that policy exists; and
- rollback target or an explicit statement that no prior promoted Tokenizer v1
  exists.

The domain manifest must not invent foundation-owned generic envelope types. The
P6.12 tokenizer implementation retains the current zero-runtime-dependency
boundary. If accepted foundation primitives become available first, adding that
dependency requires renewed architecture/dependency review and an updated gate;
it must not be introduced implicitly. Until then the tokenizer record remains
domain-specific and is not advertised as a platform-wide artifact envelope.

## Licence and distribution admission

The accepted dataset snapshot records per-source permission for acquisition,
processing, training, derived statistics, and tokenizer-artifact distribution.
That evidence is necessary but does not by itself choose a licence for the
tokenizer artifact, source package, documentation, or release bundle.

Before publication or promotion, governance evidence must bind:

- the exact artifact bytes and both tokenizer fingerprints;
- an approved SPDX expression or other explicit rights basis for the artifact;
- every required notice, attribution, restriction, and distribution term by
  digest;
- compatibility of the source, dataset, generated artifact, documentation, and
  packaging terms;
- the approved audience/channel and whether redistribution and modification are
  allowed;
- reviewer/approver identity, decision revision, time/expiry if applicable,
  revocation behavior, and exception references; and
- a fail-closed decision when any source right, notice, approval, or policy
  identity is missing, stale, contradictory, revoked, or unverifiable.

Repository visibility, source availability, training permission, an artifact
digest, or a signature is not distribution permission.

## Signing and promotion boundary

The canonical architecture currently leaves signing technology and trust-root
ownership unresolved. Therefore this gate deliberately selects neither. No
private key, certificate, identity token, signing library, transparency service,
timestamp service, registry, or hosted provider becomes a tokenizer runtime
dependency or is configured by this proposal.

The required canonical decision must define at least:

- signer identity and separation from artifact construction and approval;
- protected trust-root ownership, key generation/storage/rotation/revocation,
  emergency response, and recovery;
- approved cryptographic algorithms, signature/attestation encoding, timestamp
  and expiry policy, and offline-verification requirements;
- exactly which canonical bytes and identities are signed;
- reproducible-build provenance, dependency inventory/SBOM, CI identity, source
  revision, and validation bindings;
- verification order before parsing or loading artifact-controlled data;
- promotion states, authorized transitions, approvals, idempotency, audit,
  cancellation, deadlines, rollback, and partial-publication cleanup;
- registry immutability, digest addressing, retention, revocation, and channel
  alias rules; and
- consumer behavior for absent, malformed, unsupported, expired, revoked,
  mismatched, or unverifiable signatures and policy artifacts.

All such failures remain ineligible. They cannot fall back to unsigned use,
another artifact, another trust root, a mutable tag, weaker verification, or a
remote provider.

## Security and authority invariants

- Artifact bytes, manifests, signatures, attestations, evaluation reports,
  policy records, registry metadata, and promotion output are untrusted data and
  never authorization or executable instructions.
- Routing, training, evaluation, verification, signing, or promotion output
  cannot lower classification, widen target scope or provider/network policy,
  relax offline operation, extend deadlines or resource budgets, or reduce
  verification requirements.
- Generation remains separate from verification; verification remains separate
  from approval; approval remains separate from promotion; promotion remains
  separate from consumer admission.
- Contradictory, unsupported, insufficient-evidence, cancelled, deadline,
  resource-limit, integrity, compatibility, licence, signature, revocation,
  publication, rollback, or verification-error outcomes cannot become supported
  or promoted.
- Artifact contents remain non-executable. No pickle/marshal, object graph,
  supplied code, plugin, callback, script, external reference, or automatic
  dependency installation is permitted.
- Signing keys and credentials never enter source, tests, fixtures,
  distributions, artifact contents, logs, exceptions, or general CI output.
- Core tokenizer construction, encoding, decoding, validation, and conformance
  remain fully offline and independent of proprietary remote AI providers.
- Mutable channels such as `latest` may resolve only to an immutable accepted
  digest and are never sole provenance or compatibility evidence.

## Required tokenizer implementation evidence

After the canonical architecture and governance prerequisites are separately
accepted and verified, the tokenizer implementation proposal must provide:

1. immutable typed unsigned-manifest and result contracts with strict bounds;
2. deterministic construction of the exact accepted P6.11 candidate and P6.6
   payload with independent digest verification;
3. exact binding of P6.9 semantics, corpus rights, P6.11 evaluation,
   conformance, provenance, implementation, and evidence identities;
4. repeated cross-version byte identity and sensitivity to every bound field;
5. rejection of malformed, missing, changed, reordered, oversized, truncated,
   trailing, non-canonical, incompatible, unapproved, cancelled, expired, or
   resource-exhausted inputs;
6. proof that no path/network/provider/key/signing/publication/promotion/
   installation/execution API or dependency entered the package;
7. content-minimized evidence containing identities, counts, sizes, booleans,
   limitations, and digests only;
8. unchanged Ruff, Black, strict mypy, repository/security validation,
   dependency consistency, split-package import, pytest with 100% source and
   branch coverage on Python 3.11–3.13, package build, and exact distribution
   verification;
9. complete architecture, security, licence-boundary, supply-chain, and diff
   review; and
10. explicit project-owner acceptance bound to the exact implementation head
    and every produced deterministic identity.

No committed generated artifact, signing material, temporary workflow
diagnostic, proprietary-provider dependency, authorization widening, execution
authority, model work, P7 work, or unrelated drift is permitted.

## Required gate and final evidence

Before any P6.12 follow-on proposal begins, this exact gate revision must pass
the unchanged Python 3.11–3.13 CI, build, distribution, and agent-policy matrix,
receive explicit project-owner architecture/security/release/licence `ACCEPT`,
be squash-merged without head movement, and pass post-merge `main` checks.

P6 remains incomplete after gate acceptance. Final Tokenizer v1 selection may be
proposed only after the exact unsigned artifact, independent evaluation,
governance approval, signing/promotion implementation, published immutable
identity, rollback evidence, and post-promotion verification are all separately
accepted and verified. P7 and model work remain blocked until that final P6
closure evidence is accepted and merged.
