# P6.7 — Experimental BPE Performance and Resource Evidence Gate

## Status

**Accepted — exact-head PR #18 merged; implementation verified**

The project owner accepted exact PR #18 head
`057dc3c9e22c6a126f7a5f38fa8d2895b5958ad7`. It was squash-merged as
`d935664415b690f526832a04e437e5c5be3e34bf`; pre- and post-merge CI and
agent-policy runs 36 and 37 passed. Observational implementation evidence is
recorded separately in `P6_7_PERFORMANCE_EVIDENCE.md`.

The implementation was accepted at PR #19 head
`b40be6923ac7af1dd8b9f385de97f3afca9c3b9b`, squash-merged as
`32b7aef9bdcac29d66bdf2857ef3f84bc0444853`, and passed exact-head and
post-merge CI and agent-policy runs 41 and 42. Formal closure evidence requires
its own exact-head review and merge.

This gate measures the fixed P6.4 experimental byte-BPE candidate after the
verified P6.5 streaming and P6.6 canonical artifact gates. It does not select
Tokenizer v1, approve a corpus or artifact, establish model compatibility, or
authorize any later P6 slice.

## Ownership and scope

`cybersecgpt-tokenizer` owns tokenizer-local measurement fixtures, a reproducible
runner, and evidence. Cross-component benchmark suites belong to
`cybersecgpt-benchmarks`. The measurement runner must not change candidate
encoding, decoding, streaming, artifact bytes, fingerprints, or public contracts.

The runner measures the existing byte reference, experimental BPE, and
experimental Unigram with the P6.4 generated construction/evaluation manifests.
It reports BPE against both controls using identical inputs and token ceilings.
Artifact size is measured from P6.6 canonical bytes. Streaming ingestion is
measured with a declared fixed chunk schedule and exact one-shot equivalence;
buffered finalization must not be described as progressive token delivery.

## Measurement protocol

- Pin the source commit, Python minor version, platform, architecture, CPU,
  interpreter implementation, candidate fingerprints, manifest digests,
  settings, and fixture version in a separate observational report. Host names,
  usernames, paths, environment variables, and raw sample contents are excluded.
- Use only the already published inert, generated, provenance-bearing P6.4
  fixtures. Keep construction and evaluation manifests separate; do not train
  on evaluation samples or substitute a different corpus for a favorable result.
- Construct each candidate once outside timed trials. Warm up each measured
  operation, then run a fixed number of repetitions and report every raw elapsed
  integer nanosecond sample and the documented median. Measure encode, decode,
  streaming ingestion and finalization separately, using `perf_counter_ns` or
  an explicitly equivalent monotonic timer. Do not include fixture construction,
  candidate training, report formatting, or interpreter startup in timings.
- Repeat the same operation and input order for all candidates; disclose the
  sample size, byte count, token count, repetition count, and ordering. The
  report must distinguish input bytes per second from tokens per second and
  preserve per-domain results so an aggregate cannot hide a regression.
- Measure peak *traced Python allocations* separately with `tracemalloc` after
  resetting its peak immediately before each operation. Do not label this as
  process RSS, total native memory, or a hard runtime ceiling. Report canonical
  artifact byte length and SHA-256 independently of the timing trials.
- Run correctness checks outside timed trials: complete status, exact candidate
  fingerprint, encode/decode reversibility, exact streaming chunk equivalence,
  and canonical artifact round trip. Exclude any failed or truncated observation
  from comparative conclusions; never treat an error as a fast successful run.
- Preserve raw timing observations and measurement environment in evidence, but
  keep them out of deterministic P6.4 structural report fingerprints. Repeated
  trials are observational, not bit-for-bit reproducible across hosts.

Performance is descriptive evidence. No universal throughput or peak-memory
threshold is inferred from one host. Any eventual acceptance target must be
defined against a stated deployment profile and reviewed separately. A faster
candidate must not override correctness, safety, license, or provenance gates.

## Security and failure boundaries

- Candidate text, decoded output, fixtures, artifact bytes, metadata, and reports
  are untrusted data and never authorization or control instructions.
- The runner must perform no networking, provider calls, dynamic artifact
  loading, subprocess execution, plugin/callback invocation, or secret/raw-text
  logging. It must not silently load arbitrary user-provided corpora or artifacts.
- Bound sample count, input bytes, repetitions, output tokens, and report size.
  Check cancellation/deadline before each operation and again after it; stop
  scheduling work with an explicit incomplete outcome if a limit is reached.
  Python-level deadline checks do not forcibly interrupt an active operation.
  Record the measured range; do not extrapolate a hard upper bound from samples.
- Preserve offline requirements, classification, target scope, provider/network
  policy, deadlines, budgets, and verification requirements. Neither performance
  nor memory results authorize any relaxation or fallback.
- Keep timing and allocation evidence free of raw user data, sample text,
  decoded output, secrets, full paths, and host identity. A benchmark result
  cannot approve an artifact, a dataset license, or a production release.

## Required implementation and review evidence

The implementation PR must include independent tests for trial ordering,
measurement arithmetic and units, output minimization, fixture binding,
failure exclusion, limits, deadlines/cancellation, and deterministic structural
report separation. Provide measured encode, decode, streaming, artifact-size,
and traced-allocation results for the fixed manifest. Disclose hardware and
interpreter metadata within the privacy boundary above, observed variability,
limitations, and any measured regression. Do not assert performance results
until the runner has actually been executed on a pinned revision.

Before implementation begins, this exact gate revision requires project-owner
architecture/security `ACCEPT`, successful exact-head CI and agent-policy checks,
squash merge, and successful post-merge `main` checks. The implementation PR
requires unchanged Ruff, Black, strict mypy, repository/security validation,
dependency consistency, split-package imports, pytest with 100% source coverage
on Python 3.11–3.13, build and exact distribution verification, complete
security/diff review, exact-head owner acceptance, squash merge, and verified
post-merge `main` checks. P6.7 closes only when that evidence is recorded.
