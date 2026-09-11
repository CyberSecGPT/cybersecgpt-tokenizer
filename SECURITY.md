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

The experimental byte-BPE candidate uses fixed evaluation-only semantics,
immutable in-memory learned data, bounded deterministic construction, guaranteed
byte fallback, and explicit failure. Construction is bounded to 256 merges and
1 MiB of manifest content per run. It performs no I/O, networking, dynamic
loading, subprocess execution, or raw-text logging. Candidate decoding
range-checks IDs before lookup and rejects malformed UTF-8 without replacement.
Persistent artifact loading remains prohibited until a separate non-executable
schema and fingerprint gate is accepted.

Candidate-neutral evaluation accepts only the existing bounded tokenizer
operations. It verifies result fingerprints against the candidate descriptor,
records decode errors rather than promoting them to reversible outcomes, and
omits ratios when encoding is incomplete. Reports use sample digests and integer
counts and never retain raw text. Evaluation output is evidence only: it cannot
approve a tokenizer, grant authorization, alter classification or target scope,
enable network/provider access, or relax any budget or verification requirement.
