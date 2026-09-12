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

The experimental byte-Unigram candidate permits no runtime floating-point
scoring, unbounded substring discovery, external tokenizer state, or persistent
artifact. Its candidate pool, substring length, training bytes, vocabulary,
token IDs, and decode output are bounded and validated. Construction and
execution are local and deterministic; failures remain explicit, and candidate
or evaluation output grants no approval or authority.

The controlled benchmark uses only inert generated CC0 fixtures with
separate construction and evaluation manifests. Deterministic reports contain
digests and counts rather than sample text, and recommendation requires complete,
reversible, fingerprint-consistent evidence. Recommendation is never
authorization, artifact approval, model compatibility, or final algorithm
selection.
Manifest separation and complete domain coverage are validated before
construction. The report fingerprint binds the fixed settings, manifest/sample
digests, candidate identities, structural metrics, eligibility, and
recommendation using length-prefixed UTF-8 fields.

The accepted P6.5 streaming contract and implementation treat byte chunks and all
terminal output as untrusted data. It bounds each chunk, aggregate bytes,
admission calls, and tokens; checks cancellation and monotonic deadlines;
validates strict UTF-8 only at finalization; and never emits partial tokens on
failure. It permits no I/O, network, callback, dynamic loading, subprocess, or
raw-content logging. Until a safe BPE frontier is proven, progressive token
emission is prohibited.
