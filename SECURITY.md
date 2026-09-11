# Security Policy

Report suspected vulnerabilities privately through GitHub Security Advisories.
Do not disclose secrets, private corpora, personal data, malicious tokenizer
artifacts, or exploit details in public issues.

Tokenizer input, metadata, manifests, artifacts, and decoded output are untrusted
data and never authorization. Artifacts must be non-executable and validated for
schema, hashes, sizes, counts, IDs, and integer bounds before allocation or use.
Unknown special-token roles are data, not instructions. Core behavior must remain
offline and independent of proprietary remote AI APIs and provider tokenizers.

The UTF-8 byte reference has no special-token roles, rejects requested insertion,
range-checks every ID against 0..255, and decodes with strict UTF-8 validation and
no replacement. Its evaluation metrics contain digests and counts, not raw sample
text. These reference semantics do not approve the eventual Tokenizer v1 policy.

The proposed byte-BPE candidate must use fixed evaluation-only semantics,
immutable in-memory learned data, bounded deterministic construction, guaranteed
byte fallback, and explicit failure. Persistent artifact loading remains
prohibited until a separate non-executable schema and fingerprint gate is
accepted.
