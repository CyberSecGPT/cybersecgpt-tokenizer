# P6.7 — Experimental Performance and Resource Evidence

## Status

**Implementation accepted and merged — closure review pending**

The architecture/security gate was accepted at PR #18 head
`057dc3c9e22c6a126f7a5f38fa8d2895b5958ad7` and squash-merged as
`d935664415b690f526832a04e437e5c5be3e34bf`. Its exact-head and post-merge
CI and agent-policy runs 36 and 37 succeeded on Python 3.11–3.13, including the
build and exact distribution checks.

The project owner accepted the implementation at exact PR #19 head
`b40be6923ac7af1dd8b9f385de97f3afca9c3b9b`. It was squash-merged as
`32b7aef9bdcac29d66bdf2857ef3f84bc0444853`. Exact-head CI and agent-policy
run 41 and post-merge `main` CI and agent-policy run 42 succeeded. Both CI runs
validated Python 3.11–3.13 with unchanged Ruff, Black, strict mypy, repository
and security validation, dependency consistency, split-package imports, 164
tests at 100% tokenizer source and branch coverage, package build, and exact
distribution verification.

The implementation adds only a tokenizer-local observational runner, its tests,
and this evidence. Experimental candidate code, fingerprints, streaming behavior,
canonical artifact schema, public contracts, dependencies, and CI remain
unchanged. The accepted deterministic P6.4 report fingerprint stays
`f979122b76acffb434a536fd8e834fa9a1ce5d92bc1bb8cceda737e42a638b32`.

## Fixed measurement

The complete raw timing observations and per-domain totals are preserved in
[`evidence/P6_7_performance_observations.json`](evidence/P6_7_performance_observations.json)
(SHA-256 `b8e4ef5f95e1348a7e54d940a600b55540ed4a1f96936c7e7c436262ea2304db`).
They were observed from runner code commit
`58156fef95ccfba43ce758302b6a45ab1c9db0c7`, using CPython 3.12.14,
Linux x86_64, processor identifier `x86_64`, three repetitions per operation,
and fixed 31-byte streaming chunks. The host's specific CPU model was not
available to this standard-library-only runner. Trial timings are elapsed
nanoseconds; allocation peaks are traced Python bytes, not process RSS.

The disjoint P6.4 construction/evaluation manifests contain 10/17 inert CC0
samples. All 17 evaluation samples completed reversible encode/decode for each of
the byte reference, experimental BPE, and experimental Unigram (51 observations,
24 candidate/domain aggregates). Every BPE streaming result matched its one-shot
IDs, status, and fingerprint. The canonical BPE artifact was 10,101 bytes with
SHA-256 `0565e2def8e77c10d6bb9367e6baee7c06291e29ae5e85eb852c46dcacd01c83`;
loading reproduced the candidate.

The following sums of per-sample medians describe this single run across 1,499
input UTF-8 bytes; rates are floored integer units per second. Each domain's
inputs, token counts, raw trials, median, and allocation peaks remain in the
JSON evidence, so these totals do not conceal domain differences.

| Candidate | Tokens | Encode input bytes/s | Encode tokens/s | Decode tokens/s | Largest traced encode peak |
| --- | ---: | ---: | ---: | ---: | ---: |
| Byte reference | 1,499 | 12,642,640 | 12,642,640 | 12,944,285 | 1,797 B |
| Experimental BPE | 928 | 45,738 | 28,315 | 450,969 | 4,061 B |
| Experimental Unigram | 1,422 | 223,404 | 211,928 | 443,817 | 39,694 B |

For BPE streaming, the sums of per-sample medians were 35,816 ns for ingestion,
31,451,994 ns for finalization alone, and 31,673,340 ns for full ingestion plus
finalization. These are separate noisy trial sets and are not additive.
Streaming buffers bytes and emits tokens only after successful finalization;
these observations make no progressive-emission claim.

## Scope and limitations

The runner fixes the sample manifests, rechecks their separation and structural
fingerprint, rejects incomplete/truncated or mismatched results, bounds
repetitions, fixtures, aggregate run deadline, and output size, and excludes raw
text, decoded output, hostnames, paths, and environment variables from reports.
Python deadline checks stop subsequent work; they do not preempt a running
operation. No external input corpus, provider, network, dynamic loading, or
executable artifact is used. Tests cover trial order, units, traced allocation,
fixture and identity binding, fail-closed outcomes, cancellation/deadline,
streaming equivalence, report bounds, and content minimization.

One host and a small generated fixture cannot establish portable performance or
hard memory bounds. These measurements do not approve a production tokenizer,
training corpus, model compatibility, artifact release, or a later P6 gate.
Conformance vectors, corpus/license review, unresolved normalization, offsets,
special-token semantics, and final algorithm selection remain open.

## Closure review gate

The accepted gate, exact-head accepted implementation, post-merge `main` checks,
bounded content-minimizing observations, and complete security/diff review are
recorded. Formal P6.7 closure remains pending exact-head project-owner acceptance
of this closure revision, squash merge, and successful post-merge `main` checks.
This record cannot itself approve later P6 work or production Tokenizer v1.
