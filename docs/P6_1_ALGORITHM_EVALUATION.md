# P6.1 — Tokenizer v1 Algorithm Evaluation Gate

## Status

**Proposed — implementation blocked pending measured evidence and acceptance**

This record defines how CyberSecGPT will select Tokenizer v1 behavior. It does not
select an algorithm, create vocabulary contents, train an artifact, or approve a
tokenizer for model compatibility.

## Candidate set

The first evaluation must compare, at minimum:

1. a deterministic UTF-8 byte baseline with a fixed 256-byte alphabet;
2. byte-level Byte Pair Encoding (BPE) with guaranteed byte fallback; and
3. Unigram tokenization with guaranteed byte fallback.

Additional candidates may be evaluated only when their implementation and
dependency boundaries remain first-party, deterministic, offline, reproducible,
and independently testable.

The byte baseline is a conformance reference, not the presumed winner. Candidate
selection must be justified by measured results rather than novelty or popularity.

## Fixed evaluation dimensions

Every candidate must be evaluated using the same versioned corpus manifest,
sampling policy, split, special-token reservation, resource ceilings, and
measurement implementation.

Required measurements:

- deterministic artifact reproduction from the same inputs and configuration;
- exact encode reproducibility and required decode reversibility;
- tokens per UTF-8 byte and tokens per Unicode scalar value;
- compression ratio relative to the byte baseline;
- encode and decode throughput;
- peak memory and artifact size;
- streaming equivalence across adversarial chunk boundaries;
- malformed-input and invalid-byte behavior;
- normalization and combining-character behavior;
- unknown and literal special-token handling;
- maximum-input, truncation, and resource-limit behavior; and
- fingerprint stability and sensitivity to every behavior-defining change.

Results must be reported separately by domain rather than hidden in one aggregate.

## Required domains

The versioned evaluation manifest must contain inert, provenance-recorded samples
for:

- natural language, including English and Khasi;
- source code, assembly, PowerShell, and POSIX shell;
- Windows and Linux logs;
- JSON, YAML, XML, HTTP, and DNS;
- URLs, IP addresses, cryptographic hashes, and CVE identifiers;
- Sigma and YARA rules;
- SIEM queries, firewall rules, and IDS/IPS signatures;
- infrastructure-as-code and security telemetry; and
- defensive malware-analysis and threat-intelligence prose.

No confidential data, personal data, live credentials, weaponized payloads, or
unlicensed corpus content may be committed.

## Semantic decision gates

The following decisions remain unresolved until benchmark evidence is reviewed:

- Unicode normalization profile, including whether v1 preserves exact input;
- invalid-byte and replacement policy;
- pretokenization rules and original/normalized offset semantics;
- special-token roles, IDs, escaping, and literal rendering;
- deterministic training ordering, tie-breaking, and numeric behavior;
- canonical non-executable artifact encoding;
- canonical fingerprint input and digest procedure;
- vocabulary target and hard maximum;
- streaming state and chunk-boundary contract; and
- licensing status for code, artifacts, and every data-manifest entry.

## Security acceptance criteria

A candidate is ineligible if it:

- loads or executes artifact-supplied code;
- requires a proprietary provider, remote API, external-provider tokenizer, or
  network access for core behavior;
- accepts an unknown special-token role as a control instruction;
- logs raw input or decoded output by default;
- allocates from unvalidated artifact counts or attacker-controlled sizes;
- silently substitutes a different tokenizer or artifact after failure;
- treats tokenizer input or output as authorization;
- changes behavior without changing its canonical fingerprint; or
- cannot fail explicitly on integrity, version, deadline, or resource errors.

## Selection rule

Tokenizer v1 may be selected only after:

1. candidate implementations and evaluation harness pass the unchanged repository
   gates on every supported Python version;
2. the evaluation corpus manifest and licensing/provenance evidence are reviewed;
3. benchmark results and conformance vectors are reproducible from an exact commit;
4. security and complete-diff review find no hidden provider, network, executable
   artifact, authorization, or later-roadmap dependency;
5. the project-owner architecture/security acceptance authority records an
   explicit decision for the exact evidence revision; and
6. exact-head CI, merge, and post-merge main CI pass.

Until then, all algorithm and semantic choices remain **Proposed**.
