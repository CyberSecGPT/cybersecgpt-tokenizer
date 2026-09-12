# P6.4 — Controlled Algorithm Benchmark Evidence

## Status

**Implementation evidence proposed — exact-head project-owner acceptance required**

The accepted P6.4 gate was squash-merged to `main` as
`dd063926d8a5a2026b1c69dc6926c840038a9345` after exact-revision acceptance and
successful pull-request and post-merge CI. This record applies that gate. It is
a reproducible recommendation input, not final Tokenizer v1 selection.

## Controlled inputs

- Construction manifest: `p6.4-generated-construction@1`, 10 newly generated
  inert `CC0-1.0` samples.
- Evaluation manifest: `p6.4-generated-evaluation@1`, 17 separate newly
  generated inert `CC0-1.0` samples.
- Fixture source: `benchmarks/p6_4_corpus.py`.
- Provenance: `generated:cybersecgpt-tokenizer:p6.4`.
- Vocabulary limit: `512` for both learned candidates.
- BPE merge budget: `256`.
- Maximum construction bytes: `1048576`.
- Unigram maximum piece bytes: `16`; distinct substring limit: `262144`; seed
  piece limit: `8192`.
- Evaluation token limit: `4194304`.
- Normalization: none; pretokenization: strict UTF-8 bytes; special tokens: none.
- Bound accepted gate revision: `p6.4-gate-dd063926`.

The manifests are identifier- and content-disjoint. Runtime validation rejects
shared IDs, shared content digests, and evaluation manifests that omit any of the
eight accepted domains. Stable evaluation sample IDs explicitly cover English,
Khasi, Python, C, assembly, PowerShell, POSIX shell, Windows/Linux logs, JSON,
YAML, XML, HTTP, DNS, URL/IP/hash/CVE identifiers, Sigma, YARA, SIEM, firewall,
IDS, infrastructure-as-code, telemetry, defensive malware analysis, and threat
intelligence.

## Deterministic result

| Candidate | Fingerprint | Vocabulary | Tokens | Domain wins | Eligible |
|---|---|---:|---:|---:|---|
| UTF-8 byte reference | `a3d93532b1fcd00c09bff1e9b8444b567c9bd2b153aa083a4debc3f90d61334e` | 256 | 1499 | 0 | Baseline only |
| Byte-BPE | `fe32ae1b111956debd74643c1273a47c1b4e542514b7b25a570d57b9bdbedd80` | 512 | 928 | 8 | Yes |
| Byte-frequency Unigram | `b2b378651912fb2b2c2767e25df3116fe6201c30e06da61f21b0d09adf05bb06` | 512 | 1422 | 0 | Yes |

| Domain | UTF-8 bytes | BPE tokens | Unigram tokens |
|---|---:|---:|---:|
| Natural language | 155 | 104 | 155 |
| Code | 220 | 142 | 207 |
| Logs | 147 | 96 | 146 |
| Structured data | 143 | 88 | 138 |
| Network | 146 | 86 | 110 |
| Security identifiers | 140 | 120 | 133 |
| Detection rules | 339 | 170 | 328 |
| Security prose | 209 | 122 | 205 |

Both learned candidates reached the fixed vocabulary limit, reproduced identical
construction fingerprints, reproduced identical structural evaluations, and
completed reversible decoding for every sample without truncation or hidden
error. The deterministic report fingerprint is
`f979122b76acffb434a536fd8e834fa9a1ce5d92bc1bb8cceda737e42a638b32`.

## Recommendation

**Recommend `experimental-byte-bpe-v1` to advance to the remaining Tokenizer v1
gates.** Reason: `more_domain_wins`; BPE used fewer tokens in all eight evaluation
domains. The algorithm-ID tie-break was not used.

This result is specific to the versioned generated manifests and fixed settings.
It does not establish general model quality, approve the fixtures as a production
training corpus, or authorize a release.

## Replay and failure evidence

Run from the repository root:

```text
PYTHONPATH=src:. python scripts/run_p6_4_benchmark.py
```

The renderer emits only identities, digests, fixed configuration, candidate
fingerprints, counts, exact ratios, eligibility, recommendation, and report
fingerprint. It emits no raw fixture text, decoded content, wall-clock timing,
memory observation, host identity, or secret.

Tests cover repeated construction and evaluation, report-fingerprint sensitivity,
domain aggregation, incomplete-domain rejection, manifest separation, candidate
binding mismatch, zero/one/two eligible candidates, domain-win selection,
total-token selection, deterministic tie-breaking, and content-minimizing output.

## Remaining selection blockers

Final Tokenizer v1 selection remains blocked on accepted evidence for streaming
equivalence, canonical persistent artifact format and size, controlled throughput
and peak-memory observations, conformance vectors, corpus review, and unresolved
P6.1 semantic decisions. Recommendation grants no authorization, classification,
network/provider access, execution authority, artifact approval, or compatibility
claim.
