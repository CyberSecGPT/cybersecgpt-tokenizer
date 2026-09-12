# P6.4 — Controlled Algorithm Benchmark and Recommendation Gate

## Status

**Accepted — gate merged as `dd063926d8a5a2026b1c69dc6926c840038a9345`**

This gate defines the first controlled comparison of the fixed UTF-8 byte
reference, experimental byte-BPE, and experimental byte-frequency Unigram
candidates. It may produce a reproducible recommendation. It does not select or
approve Tokenizer v1, a production vocabulary, a training corpus, streaming
semantics, special tokens, or a persistent artifact.

## Repository boundary

This repository owns the candidate implementations, tokenizer-local evaluation,
and the algorithm decision record. A future reusable or cross-component benchmark
suite belongs in `cybersecgpt-benchmarks`. No production component may depend on
benchmark fixtures or reports.

## Corpus and provenance

The initial comparison uses two distinct immutable manifests:

- a construction manifest used only to build BPE and Unigram candidates; and
- an evaluation manifest used only to measure the already-built candidates.

Every sample must be newly generated for this repository, inert, non-personal,
free of credentials and weaponized payloads, identified as `CC0-1.0`, and bound
to a canonical UTF-8 SHA-256 digest. The evaluation manifest must cover every
required P6.1 category through stable sample identifiers and the existing domain
taxonomy: English and Khasi prose; Python, C, assembly, PowerShell, and POSIX
shell; Windows and Linux logs; JSON, YAML, XML, HTTP, and DNS; URLs, IPv4/IPv6,
hashes, and CVEs; Sigma and YARA; SIEM, firewall, and IDS rules;
infrastructure-as-code and telemetry; and defensive malware-analysis and
threat-intelligence prose.

Samples must not cross manifest boundaries during candidate construction.
Changing text, order, identity, domain, provenance, license metadata, or split
creates a new manifest version and new evidence identity.

## Fixed comparison configuration

- Candidate order: UTF-8 byte reference, byte-BPE, byte-frequency Unigram.
- Shared vocabulary limit: `512`, including the fixed 256-byte fallback.
- BPE merge budget: `256`.
- Unigram substring, seed-pool, and cost limits remain exactly those accepted in
  P6.3.
- Candidate construction input limit: `1 MiB`.
- Evaluation encode limit: the existing `MAX_TOKEN_COUNT`; truncation is
  ineligible for recommendation.
- Normalization: none.
- Pretokenization: strict UTF-8 bytes.
- Special-token allocation: none; requested insertion remains an error.
- Randomness, locale-dependent ordering, network access, external tokenizers,
  and provider credentials are prohibited.

## Deterministic report

The report is immutable and content-minimizing. It binds:

- report schema version and evaluation-policy identifier;
- construction and evaluation manifest IDs, versions, and ordered sample
  digests;
- candidate algorithm IDs and fingerprints;
- exact configuration values;
- per-sample structural metrics from the accepted candidate-neutral evaluator;
- per-domain sums of UTF-8 bytes, Unicode scalars, and candidate tokens;
- exact reduced per-domain token/byte ratios; and
- explicit eligibility, recommendation, and reason.

It contains no raw sample text, decoded output, nondeterministic timing, process
metadata, host identity, environment secrets, or implicit license approval.
Canonical report identity is SHA-256 over a documented length-prefixed UTF-8
encoding of every behavior- and evidence-defining field.

## Eligibility and recommendation

A learned candidate is eligible only when:

1. repeated construction produces the same candidate fingerprint;
2. repeated evaluation produces the same structural report;
3. every evaluation sample completes, decodes successfully, and is reversible;
4. candidate and result fingerprints agree throughout;
5. no resource, integrity, malformed-input, or contract failure is hidden; and
6. its configuration and manifest bindings exactly match this gate.

The byte reference is reported as a baseline and cannot be recommended by this
first learned-candidate comparison. If exactly one learned candidate is eligible,
it is the recommendation. If both are eligible, compare the ordered tuple:

1. number of evaluation domains in which the candidate has a strictly lower
   token count than the other learned candidate;
2. total token count across the evaluation manifest; then
3. algorithm ID in ascending bytewise lexical order.

More domain wins is preferred; lower total token count is preferred. The final
algorithm-ID tie-break makes replay deterministic but must be disclosed as a
tie, not represented as measured superiority. Per-domain metrics remain visible;
the aggregate cannot hide a regression.

If neither learned candidate is eligible, or evidence bindings disagree, the
outcome is `no_recommendation`. Failures never cause substitution of different
settings or promotion of incomplete evidence.

## Observational performance boundary

P6.1 also requires throughput, peak memory, artifact size, and streaming
equivalence. Wall-clock and process-memory observations are environment-dependent
and must remain outside the deterministic report. Canonical artifact size cannot
be measured before the artifact-format gate, and streaming equivalence cannot be
claimed before the streaming contract is implemented.

Therefore this slice may recommend which experimental learned algorithm should
advance to those gates, but it cannot formally select Tokenizer v1. Final
selection remains blocked until those dimensions, conformance vectors, corpus
review, and all unresolved P6.1 semantic decisions have accepted evidence.

## Security controls

- All fixtures and outputs are untrusted data and never authorization.
- The benchmark performs no file loading, network access, dynamic import,
  subprocess execution, callback execution, or persistent artifact loading.
- Construction, vocabulary, sample, input, output, and report sizes remain
  bounded by existing contracts and candidate gates.
- Reports retain hashes and counts only; raw or decoded content is excluded.
- Recommendation cannot grant artifact approval, model compatibility, release
  status, access, execution authority, or any policy change.
- Contradictory, incomplete, truncated, non-reversible, or error evidence remains
  ineligible and cannot be promoted.

## Required merge evidence

Before the benchmark implementation or evidence may merge:

- this exact gate revision has project-owner architecture/security acceptance;
- fixtures and license/provenance metadata receive complete-diff review;
- deterministic replay, fingerprint sensitivity, per-domain aggregation,
  eligibility, tie, and fail-closed outcomes have tests;
- unchanged Ruff, Black, strict mypy, repository/security, dependency,
  split-package import, pytest, and 100% source-coverage gates pass on Python
  3.11–3.13;
- package build and exact distribution-boundary verification pass;
- the implementation PR receives exact-head project-owner acceptance; and
- squash merge and post-merge `main` CI pass.

Benchmark evidence is a recommendation input, not authorization or final
Tokenizer v1 selection.

The implementation and exact controlled result are recorded in
`docs/P6_4_ALGORITHM_BENCHMARK_EVIDENCE.md`. That evidence remains subject to its
own exact-head project-owner acceptance and merge gate.
