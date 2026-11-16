# P6.11 — Deterministic Tokenizer v1 Training Evidence

## Status

**Implementation and evidence proposed — exact-head project-owner acceptance is
required.**

The accepted P6.11 gate is
`docs/P6_11_TOKENIZER_V1_TRAINING_RUN_GATE.md`. Gate PR #32 was accepted at
head `7c7cabf453c856fd460c99e0693afb0da41128a6`, squash-merged as
`2e7cad0900ec2b1a065e5688f520e8f7c624bd69`, and passed exact-head and
post-merge runs 68/69. This proposal implements only that fixed run. It creates
no persistent artifact and grants no promotion, signing, compatibility, final
selection, model, execution, provider/network, or P7 authority.

## Exact implementation and inputs

- tokenizer implementation revision:
  `1b1519233b54f55326709b198ad7e95e9834219f`;
- dataset snapshot revision:
  `a8573904fd944e9be26e911d768e7335e4bdf1e0`;
- dataset package implementation revision:
  `cfda1cea94e0501a2b9c67491d47e04294ce35d8`;
- dataset manifest:
  `374773d05a9aae380ad88f477210da75d40adc90cca1afac9ee8800a93656fef`;
- dataset replay:
  `002ea5b42cd67d94dcc3e03531c272499963a5a9ffa0171ab01adfdb8a554206`;
- tokenizer admission manifest:
  `a2f676b2717e86717d469b9274b91cb3c3bf48daf58e83efe97221e4d5a7151a`;
- 8 accepted sources, 1,024 ordered samples, 112,467 bytes; and
- ordered sample-digest sequence:
  `ec76753c7d3c4353f8b91d56f34373704fd49b78f22af15f3192a74d0c92fae6`.

The coordinator requires exact equality with these identities before strict
UTF-8 projection. It then constructs exactly 512 ordinary IDs with 256 ordered
merges and `vocabulary_limit` finish status. Cancellation and monotonic deadlines
are checked before and after admission, between conversions, around every merge,
between holdout samples, and before evidence finalization. Every terminal state
returns no successful candidate report and cannot fall back or weaken controls.

## Deterministic candidate and evaluation

- ordinary-candidate fingerprint:
  `072d8850d68f5c16b152c87d15eb01bd2e86100a6012be9fea05fbfa36410e5d`;
- P6.9 behavior fingerprint:
  `ef23540517cb696d57f722c43663e8bc52dac9d9a5e2f7ff9d72ab6e8d0bd347`;
- fixed holdout identity:
  `1250db8007142344e51a6c8114ed80032f0d2226f38304097ec1c1345eb72c23`;
- holdout bytes / candidate tokens: `1,499 / 1,005`;
- accepted P6.4 comparison candidate tokens: `928`;
- evaluation digest:
  `4833fb4b840297a553127630d9555cfcc8653db501b844735d40a8900e320172`;
- identity-bound conformance digest:
  `0d30e646dfc9c1d658b0931b50dd0a5e1616a800a997108cdfe822dcd0732581`;
  and
- canonical training-evidence digest:
  `279d62e1c7617ed8d873509cfc8947ef8ae816827495166335d187a61ec00ab0`.

| Holdout domain | UTF-8 bytes | Candidate tokens |
| --- | ---: | ---: |
| Natural language | 155 | 109 |
| Code | 220 | 162 |
| Logs | 147 | 102 |
| Structured data | 143 | 96 |
| Network | 146 | 91 |
| Security identifiers | 140 | 122 |
| Detection rules | 339 | 204 |
| Security prose | 209 | 119 |

Every holdout sample is digest-disjoint from training, completes strict-UTF-8
encode/decode reversibly, matches an independent ordered-merge oracle, and has
byte-split streaming equivalence. All eight domains improve on the byte
reference. The run also exercises P6.9 special-token, truncation, offset, and
exact-fingerprint rules plus fail-closed negative cases. The older P6.8 IDs are
not claimed for this different candidate; the new results are bound by the
conformance digest above.

## Reproducibility and repository boundary

`scripts/verify_p6_11_training_run.py` rebuilds the accepted dataset entirely in
memory from the exact local dataset checkout, blocks socket creation during
construction and evaluation, and performs two fresh runs. It requires exact
token bytes, merge triples, candidate identity, semantic identity, structural
metrics, and evidence digest equality. The unchanged CI matrix must reproduce
that same result on Python 3.11, 3.12, and 3.13 before owner acceptance.

The production package retains zero runtime dependencies and does not import the
dataset package. CI obtains the public dataset repository at the exact accepted
commit only after all repository-local gates, then passes its in-memory bytes
through the tokenizer-owned contracts. Raw/decoded corpus text, learned token
bytes, rendered vocabulary, paths, host data, secrets, and timing are absent from
the report and deterministic identity.

## Verification and remaining boundary

Local Python 3.12 validation observed Ruff, Black, strict mypy,
repository/security validation, dependency consistency, split-package import,
311 tests with 100% source and branch coverage, package build, exact distribution
verification, and two byte-identical full snapshot runs. The final GitHub
Python 3.11–3.13 matrix remains required on the exact review head.

Even after acceptance and merge, this evidence authorizes only proposing a
separate artifact-promotion/signing gate. No artifact has been written, signed,
published, promoted, installed, or declared Tokenizer v1. Final Tokenizer v1
selection, model work, and P7 remain blocked.
