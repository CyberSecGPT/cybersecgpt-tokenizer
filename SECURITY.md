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
Exact-head and post-merge validation verify these P6.5 controls at merge
`345846ac0e02b3bd0c265b1d2f4649d0774cade9`; they do not approve another P6
security boundary.

The proposed P6.6 artifact gate permits only a fixed, bounded, non-executable
binary schema. Envelope size, magic, version, length, and digest are validated
before payload counts or lengths are used; descriptor, provenance, token, merge,
and canonical-byte integrity are then revalidated. It forbids pickle/marshal,
code execution, paths, external references, I/O, networking, callbacks, dynamic
loading, subprocesses, providers, fallback, and implicit corpus approval.

The P6.6 implementation preserves that boundary through exact `bytes` admission,
envelope-first validation, bounded counts and token lengths, reconstructed
candidate validation, generic content-minimizing failures, and exact canonical
rebuilding. Artifact validity remains data integrity, never authorization,
license approval, or model compatibility.

These P6.6 controls are verified at accepted implementation head
`b4f857687f3e838fcae7b1a7f27f62e52440ea50`, merge
`92776213a1e8003682752a268af5e4bc0664457d`, and successful exact-head and
post-merge runs 32 and 33. They grant no later P6 security approval.

The accepted P6.7 gate measures only fixed inert generated fixtures. The
observational runner checks complete reversible outcomes and exact structural
identity before reporting, separates times from deterministic fingerprints,
restricts work and report size, and minimizes output to identities, digests,
counts, timings, and traced allocations. Cancellation and deadlines block new
work but cannot forcibly interrupt an active Python call. Observed throughput
and traced allocations confer no authorization, resource-limit guarantee,
artifact approval, corpus/license approval, or tokenizer selection.

The P6.7 gate and implementation passed exact-head and post-merge CI and policy
runs 36/37 and 41/42 respectively. Implementation acceptance was bound to head
`b40be6923ac7af1dd8b9f385de97f3afca9c3b9b` and merge
`32b7aef9bdcac29d66bdf2857ef3f84bc0444853`. Closure PR #20 was accepted
at exact head `6cb6095e7c932aea300b4d5419573e61460af72f`, squash-merged as
`8a8d2cfa40b6b790528292cc492dc79597dc66b1`, and passed exact-head and
post-merge CI and agent-policy runs 44/45. The runtime authorization, provider,
classification, target-scope, offline, deadline, budget, and verification
boundaries remain unchanged; P6.7 closure grants no later P6 approval.

The accepted P6.8 conformance gate requires independently checked, bounded
vectors and explicit negative outcomes for malformed inputs and artifacts,
unknown roles, truncation, cancellation, deadlines, and fingerprint mismatch.
It treats all fixtures and decoded output as untrusted data; conformance cannot
grant authorization, relax any policy or resource boundary, approve a corpus,
or select a production tokenizer.

P6.8 gate acceptance is bound to PR #22 head
`773ef632bf1201d232a99fa100afa144a3828ee6`, merge
`c863af96bfee43889b8c2be8d98e5d9c55868433`, and green exact-head/main
runs 48/49. The implementation's bounded, offline known-vector
verifier fails on changed identities, fixture data, incorrect truncation, invalid
UTF-8/IDs, cancelled or expired streams, and corrupted canonical artifact data.
Its formal closure does not relax any security boundary.

The P6.8 implementation was accepted at exact PR #23 head
`d4b4b7826ebbeaeecf5a0ffc4303041f50b9a568`, squash-merged as
`980ac53493cbef3ba6fad958e5fa78525682b7ab`, and passed exact-head and
post-merge CI and policy runs 50/51. Closure PR #24 was accepted at exact head
`5972c304a37a42d3bc68e84cf7ebef73e28d36cd`, squash-merged as
`a15bffed922c8712b8c9ae63869f3561d81ebc21`, and passed exact-head and
post-merge runs 52/53. P6.8 closure does not relax any existing security boundary.

The accepted P6.9 semantic profile and proposed implementation keep all text,
token IDs, offsets, special renderings, artifacts, and decoded output untrusted.
Literal special-looking text
cannot create a control ID; special insertion and decode behavior are typed and
explicit. Invalid UTF-8/IDs, incompatible fingerprints, malformed artifacts,
limits, cancellation, and deadlines fail closed. The proposal grants no
authorization, corpus/license approval, model compatibility, or production
selection. The gate and implementation passed separate exact-head acceptance,
squash merge, and post-merge review at PRs #26/#27 and runs 56–59. Formal P6.9
closure remains separately gated and cannot relax any security boundary.
