# Security Policy

Report suspected vulnerabilities privately through GitHub Security Advisories.
Do not disclose secrets, private corpora, personal data, malicious tokenizer
artifacts, or exploit details in public issues.

Tokenizer input, metadata, manifests, artifacts, and decoded output are untrusted
data and never authorization. Artifacts must be non-executable and validated for
schema, hashes, sizes, counts, IDs, and integer bounds before allocation or use.
Unknown special-token roles are data, not instructions. Core behavior must remain
offline and independent of proprietary remote AI APIs and provider tokenizers.
