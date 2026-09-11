# P6 — CyberSecGPT Tokenizer v1 Acceptance Plan

## Status

**In progress — architecture and repository bootstrap**

This plan begins P6 after verified P5 closure. It does not select a tokenizer
algorithm, vocabulary, normalization profile, artifact encoding, or training
corpus, and it does not claim a trained or production-ready tokenizer.

## Governing scope

- Canonical owner: `CyberSecGPT/cybersecgpt-tokenizer`
- Roadmap milestone: P6 — CyberSecGPT Tokenizer v1
- Contract: `cybersecgpt-docs/docs/specifications/tokenizer-contract.md`
- Allowed dependencies: Foundation and approved normalization/data interfaces
- Forbidden core dependencies: proprietary remote AI APIs, external-provider
  tokenizers, model/inference/training implementations, and product surfaces

## Required implementation slices

1. Repository, security, contribution, validation, and package boundaries.
2. Versioned immutable tokenizer descriptor and bounded request/result contracts.
3. Explicit Unicode, invalid-input, normalization, pretokenization, and offset
   semantics.
4. Deterministic encode, decode, streaming, truncation, and special-token behavior.
5. Non-executable, self-describing artifact schema with strict bounds and
   canonical content fingerprinting.
6. Exact model/tokenizer compatibility checks based on fingerprints rather than
   vocabulary size.
7. First-party candidate training interface with dataset-manifest provenance;
   training success must not grant artifact approval.
8. Canonical conformance vectors for empty, ASCII, Unicode, combining characters,
   malformed inputs, code, logs, structured data, security identifiers, streaming,
   truncation, and every special-token/escape rule.
9. Benchmarks covering natural language, source code, assembly, shell and
   PowerShell, logs, JSON/YAML/XML, HTTP/DNS, URLs/IPs/hashes/CVEs, Sigma/YARA,
   SIEM queries, firewall/IDS rules, infrastructure-as-code, telemetry, malware
   analysis, and threat intelligence.
10. Reproducible build, dependency consistency, exact distribution-boundary
    checks, strict static analysis, and 100% source coverage across supported
    Python versions.

## Security invariants

- Tokenizer input, artifacts, manifests, metadata, and decoded output are
  untrusted data and never authorization.
- Artifacts contain data only and never load or execute supplied code.
- Schema, hashes, sizes, counts, IDs, and integer bounds are validated before
  allocation or use.
- Unknown special-token roles are not interpreted as control instructions.
- Raw input and decoded output are not logged by default.
- Core startup, training, encoding, decoding, validation, and tests work with the
  network disabled and without provider credentials.
- Resource limits, deadlines, truncation, errors, and integrity failures fail
  explicitly; they cannot silently widen scope or substitute another tokenizer.

## Decision gates

Before algorithm implementation, record and review:

- algorithm candidate and benchmark rationale;
- normalization and invalid-input policy;
- pretokenization and offset semantics;
- canonical artifact and fingerprint encoding;
- initial special-token role/ID allocation;
- reproducibility and training-data provenance requirements; and
- licensing status for code, artifacts, and training data.

Any change to repository ownership, dependency direction, public contract
compatibility, trust boundaries, or persistent artifact format follows the
architecture change gate and requires the applicable ADR/review.

The experimental behavior proposed for the required byte-BPE candidate is
recorded in `docs/P6_2_BYTE_BPE_CANDIDATE.md`. BPE implementation remains blocked
until that exact revision receives project-owner architecture/security
acceptance. Unigram numeric and training semantics require a separate gate.

## Initial completion evidence

P6 is complete only when the selected Tokenizer v1 implementation, artifacts,
conformance vectors, benchmarks, packaging boundary, security review, exact-head
CI, merge, and post-merge CI are all independently verified and recorded. A
repository scaffold, passing unit tests, or successful tokenizer-training run is
not sufficient by itself.
