# P6.11 — Tokenizer v1 Deterministic Training-Run Gate

## Status and decision boundary

**Proposed — exact-head project-owner architecture/security/training acceptance
is required before implementation or training.**

P6.10 established a bounded manifest verifier and the dataset owner has now
accepted one exact first-party snapshot. This gate proposes the smallest next
P6 increment: deterministically construct and evaluate one in-memory byte-BPE
Tokenizer v1 candidate from that exact admitted snapshot.

This gate does not itself run training, add trainer code, persist or publish an
artifact, approve signing or promotion, claim model compatibility, finally
select Tokenizer v1, train a neural model, or begin P7 or later work. Gate
acceptance may authorize only a separately reviewed implementation-and-evidence
pull request for the fixed run below.

## Accepted baselines and immutable inputs

The proposed run is bound to all of the following evidence:

- tokenizer baseline `0d3b1bff2328392a5b385b0c5b2bd7d08177b792`, the
  squash merge of P6.10 admission-verifier PR #31;
- PR #31 implementation head
  `69d202f36010658a473fd99cff2f7186af53ab31`, owner acceptance comment
  `5904865101`, and successful exact-head/post-merge CI and policy runs 66/67;
- dataset snapshot proposal PR #8 head
  `0cadfd93a5d9ac528075fba4d836322630ca5557` and owner acceptance comment
  `6162064709`;
- dataset snapshot package implementation revision
  `cfda1cea94e0501a2b9c67491d47e04294ce35d8`;
- accepted dataset main commit
  `a8573904fd944e9be26e911d768e7335e4bdf1e0` and successful
  exact-head/post-merge CI runs 14/15;
- corpus ID `csgpt-tokenizer-v1-first-party-pilot-1`;
- exactly 8 accepted sources, 1,024 ordered samples, 8 tokenizer domains, and
  112,467 strict UTF-8/LF bytes;
- dataset manifest SHA-256
  `374773d05a9aae380ad88f477210da75d40adc90cca1afac9ee8800a93656fef`;
- dataset replay SHA-256
  `002ea5b42cd67d94dcc3e03531c272499963a5a9ffa0171ab01adfdb8a554206`;
  and
- tokenizer admission-manifest SHA-256
  `a2f676b2717e86717d469b9274b91cb3c3bf48daf58e83efe97221e4d5a7151a`.

Any changed source, decision, revision, manifest field, sample byte, sample
order, transformation, domain mapping, count, digest, training setting, or
evaluation fixture creates a different proposed run and requires renewed gate
review. A mutable branch, filename, URL, aggregate count, or successful prior
run is not an acceptable substitute for these identities.

## Repository and dependency boundary

`cybersecgpt-tokenizer` owns tokenizer construction, candidate identity,
Tokenizer v1 behavior, training-run evidence, and tokenizer-local evaluation.
`cybersecgpt-datasets` continues to own source governance, exact snapshot
construction, replay, and dataset identity. Neither repository gains ownership
of the other's implementation.

The production tokenizer package must remain dependency-free and must not
import the dataset package. Cross-repository evidence may use credential-free,
exact local checkouts in an isolated CI harness after every repository-local
quality gate has completed. The harness may regenerate the accepted bytes in
memory and pass only the tokenizer-owned admission records and immutable local
bytes into the tokenizer API. This artifact flow is not a runtime source-code
dependency and must not create a circular L0 edge.

No network service, provider SDK, external tokenizer, hosted AI system, model
training implementation, shared mutable storage, or peer private module may
become part of the tokenizer package or training algorithm.

## Fixed training profile

The profile identifier is `cybersecgpt-tokenizer-v1-byte-bpe-training-1`. The
implementation must use the already reviewed deterministic byte-BPE construction
semantics and the accepted P6.9 behavior profile with these exact settings:

| Field | Fixed value |
| --- | --- |
| Algorithm family | byte-level BPE with complete byte fallback |
| Ordinary vocabulary | exactly 512 IDs: bytes `0..255`, learned IDs `256..511` |
| Merge budget | 256 |
| Maximum admitted training bytes | 1,048,576 |
| Actual accepted bytes | 112,467 |
| Sample selection | all 1,024 accepted samples |
| Sample order | exact admission-manifest order |
| Sampling/shuffling | none |
| Random seed | none; randomness is prohibited |
| Numeric ranking | integer occurrence counts only |
| Tie break | unsigned lexical `(left token bytes, right token bytes)` |
| Normalization | none |
| Pretokenization | whole strict UTF-8 byte sequence per sample |
| Sample boundaries | merges never cross samples |
| Special tokens | P6.9 fixed `bos=512`, `eos=513`, `pad=514`; excluded from BPE training |

The expected construction outcome is 512 ordinary tokens, 256 ordered merges,
and `vocabulary_limit` finish status. A different outcome is recorded as
ineligible evidence; the implementation must not silently change the corpus,
settings, limits, ordering, or algorithm to obtain a preferred result.

## Admission-to-training binding

The implementation must preserve this exact order:

1. require the expected corpus ID and all three accepted snapshot identities;
2. require the already sealed tokenizer admission manifest and validate its
   canonical digest;
3. run the existing exact local-byte admission verifier before decoding or
   construction;
4. require 1,024 samples, 112,467 bytes, all eight domains, and ordered sample
   digest equality with the admitted result;
5. require the final projection transformation to bind the accepted dataset
   manifest and exact dataset implementation revision;
6. decode each admitted byte string as strict UTF-8 with no replacement,
   normalization, repair, or control interpretation;
7. construct a private immutable training view in manifest order; and
8. invoke the fixed deterministic BPE constructor.

The private training view may reuse existing immutable tokenizer sample
contracts, but it is not an evaluation split and must not escape into reports.
Source IDs and reviewed licence expressions remain provenance only. Corpus text,
decoded text, learned token bytes, and rendered vocabulary entries must not be
logged, printed, committed, or included in deterministic evidence.

Missing, extra, duplicate, reordered, changed, rights-ineligible, unsafe,
invalid-UTF-8, cancelled, expired, or over-limit input fails before a candidate
can be reported. Admission success is integrity evidence, never authorization
or training approval for any other snapshot.

## Deterministic lifecycle and bounded control

Generation and verification remain separate stages. The proposed coordinator
may sequence them but may not reinterpret a verifier failure:

```text
REQUESTED
  -> ADMITTING
  -> ADMITTED
  -> CONSTRUCTING
  -> CONSTRUCTED
  -> EVALUATING
  -> EVIDENCE_READY
```

Terminal outcomes include `admission_error`, `cancelled`, `deadline_exceeded`,
`resource_limit`, `invalid_utf8`, `construction_error`, and
`verification_error`. A terminal outcome yields no successful candidate report,
no partial output, no fallback algorithm, and no retry under weaker controls.

The implementation must check cancellation and a monotonic deadline before and
after admission, between sample conversions, before and after every merge step,
before evaluation, between evaluation samples, and before evidence finalization.
Only tokenizer-owned trusted state may carry cancellation or time; untrusted
manifest or corpus content cannot supply callbacks or executable behavior. The
1 MiB byte limit, 1,024-sample binding, 512-token vocabulary, 256-merge budget,
existing per-sample and global limits, and evidence-size bounds are monotonic
and cannot be raised by the run.

## Reproducibility requirements

For one fixed implementation head, the implementation-and-evidence proposal
must demonstrate:

- two fresh constructions in each Python 3.11, 3.12, and 3.13 job;
- identical ordered token bytes, ordered merge triples, ordinary-candidate
  fingerprint, P6.9 behavior fingerprint, finish status, and deterministic
  evidence fingerprint across every replay and interpreter;
- no clock, locale, hash-order, host, path, filename, process ID, thread,
  environment secret, network result, or timing value in deterministic identity;
- exact sensitivity to every accepted manifest, configuration, implementation,
  candidate, semantic-profile, and evaluation binding; and
- failure rather than substitution when any expected identity differs.

The candidate is wrapped by `TokenizerV1SemanticCandidate` only after successful
construction. Its behavior fingerprint must therefore bind the trained ordinary
candidate and the already accepted P6.9 semantics. Reproducibility does not
approve compatibility with a model because no model checkpoint exists.

## Separate deterministic evaluation

Training samples must never be presented as independent quality evidence. The
fixed holdout is the existing `p6.4-generated-evaluation@1` manifest in
`benchmarks/p6_4_corpus.py` at the accepted tokenizer baseline. Before evaluation,
the implementation must prove that no holdout content digest occurs in the
accepted training snapshot.

The independent evaluator, not the constructor, must report:

- complete strict-UTF-8 encode/decode and exact reversibility for every holdout
  sample;
- candidate/result fingerprint agreement and P6.9 exact behavior identity;
- no truncation, hidden error, replacement, fallback candidate, or skipped
  domain;
- total and per-domain UTF-8 byte, scalar, and token counts with exact reduced
  ratios;
- comparison with the byte reference and the accepted P6.4 experimental result;
- no domain whose token count exceeds the byte reference, plus a strictly lower
  aggregate token count than the byte reference; and
- explicit eligibility, limitations, and a canonical evaluation digest.

The report must retain all eight domain outcomes so an aggregate cannot hide a
regression. Comparison with the P6.4 experimental candidate is evidence, not a
requirement to outperform a small comparison corpus on every metric. Training
success, compression improvement, reversibility, and conformance are necessary
evidence but are insufficient for artifact promotion or final selection.

The implementation proposal must also exercise the accepted P6.5 streaming,
P6.8 negative-case, and P6.9 special-token/truncation/offset/compatibility rules
against the newly trained candidate. Existing vectors whose expected IDs bind a
different candidate fingerprint must not be misrepresented as unchanged v1
vectors; new identity-bound results require separate review in the same training
evidence proposal.

## Content-minimized training evidence

The canonical training-run evidence must bind at least:

- evidence schema and training-profile identifiers;
- exact tokenizer and dataset source commits;
- owner acceptance comment and the three accepted snapshot identities;
- corpus ID, source/sample/domain counts, total bytes, and ordered sample
  digests;
- algorithm/configuration, construction finish status, vocabulary and merge
  counts;
- ordinary-candidate and P6.9 behavior fingerprints;
- holdout identity, digest-disjointness result, structural metrics, eligibility,
  and evaluation digest;
- repeated-run and Python-version reproducibility result;
- cancellation, deadline, resource, malformed-input, and identity-mismatch
  verification result; and
- explicit status, exclusions, known limitations, and non-promotion boundary.

Canonical identity uses documented length-prefixed fields and SHA-256. Evidence
must not contain raw samples, decoded samples, learned token bytes, rendered
vocabulary text, secrets, credentials, paths, host identity, nondeterministic
timing, or implicit rights and release decisions. Observational performance, if
repeated, remains separate from the deterministic evidence digest.

## Security and authority invariants

- Corpus records, bytes, learned state, tokens, metrics, reports, and errors are
  untrusted data and never authorization or executable instructions.
- Routing, admission, training, evaluation, or verifier output cannot grant
  permission, lower classification, widen target scope or provider/network
  policy, relax offline requirements, extend deadlines or resource budgets, or
  reduce verification requirements.
- The trainer performs no filesystem or network I/O, subprocess, dynamic import,
  plugin, callback, unsafe deserialization, environment lookup, provider call,
  content execution, or automatic fallback.
- Contradictory, unsupported, insufficient-evidence, cancelled, deadline,
  resource-limit, malformed-input, or verification-error outcomes remain
  ineligible and can never be promoted to supported.
- Raw corpus bytes remain in process memory only and must not enter Git,
  distributions, caches, logs, exceptions, test reports, CI artifacts, or
  committed evidence.
- A valid run produces a candidate and evidence only. It cannot persist, sign,
  publish, promote, install, load from a path, or declare a production artifact.

## Required implementation and merge evidence

Before implementation or training begins, this exact gate revision must receive
project-owner architecture/security/training `ACCEPT`, pass the unchanged
Python 3.11–3.13 CI and package matrix, be squash-merged, and pass post-merge
`main` CI.

The later implementation-and-evidence pull request must independently provide:

1. typed immutable training request, lifecycle, result, and evidence contracts;
2. fail-closed exact-snapshot admission and strict-UTF-8 projection;
3. cancellation, monotonic deadline, and all resource-bound tests;
4. deterministic byte-BPE construction and repeated cross-version identities;
5. separate digest-disjoint holdout evaluation and P6.5/P6.8/P6.9 conformance;
6. content-minimized canonical evidence with no raw corpus or vocabulary text;
7. proof of no runtime peer/provider dependency, network requirement, execution
   path, persistence, or distribution drift;
8. unchanged Ruff, Black, strict mypy, repository/security validation,
   dependency consistency, split-package import, pytest with 100% source and
   branch coverage on Python 3.11–3.13, package build, and exact distribution
   verification;
9. complete architecture, security, licence-boundary, and diff review; and
10. explicit project-owner acceptance bound to the exact implementation head,
    accepted corpus/admission digests, candidate fingerprints, and canonical
    training/evaluation evidence digests.

Only after that exact implementation is accepted, squash-merged, and verified
on `main` may a separate artifact-promotion/signing gate be proposed. No artifact
promotion, final Tokenizer v1 selection, model work, or P7 work is authorized by
this gate.
