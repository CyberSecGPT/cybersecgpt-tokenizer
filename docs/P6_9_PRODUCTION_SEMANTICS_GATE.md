# P6.9 — Tokenizer v1 Production Semantics and Compatibility Gate

## Status and decision boundary

**Accepted — implementation evidence remains independently gated.**

The project owner accepted this gate at PR #26 head
`bb3557b5b351ae2471b6107ded617eb15a0cee69`. It was squash-merged as
`e6234f46ad7e9ceb5d53e33f2a7deba174958db4`; exact-head and post-merge
Python 3.11–3.13 CI/build/distribution and agent-policy runs 56 and 57 passed.

P6.8 closed experimental conformance-vector evidence. This gate proposes the
observable semantic profile that a future Tokenizer v1 byte-BPE artifact must
implement. It does not approve a corpus or license, train or promote an artifact,
claim model compatibility, or finally select Tokenizer v1. Corpus governance,
training, artifact promotion, model integration, and release remain separately
reviewed gates.

The experimental byte-BPE recommendation advances because it passed the fixed
comparison, streaming, artifact, performance, and conformance slices. This gate
does not convert that recommendation into final selection. If later corpus or
release evidence fails, selection must fail closed or be reconsidered.

## Versioned semantic profile

The proposed profile identifier is `cybersecgpt-tokenizer-v1-semantics-1`.
Every behavior below is fingerprint-defining.

### Input, Unicode, and normalization

- The public one-shot input is Unicode text. Its canonical tokenizer input is
  strict UTF-8 bytes. Byte-stream input is admitted only by the bounded streaming
  interface and must form complete strict UTF-8 at successful finalization.
- Tokenizer v1 performs **no Unicode normalization**. NFC/NFD and other
  canonically equivalent but byte-distinct strings remain distinct. The profile
  must never apply locale-sensitive case folding, whitespace rewriting, control
  stripping, replacement characters, or invisible repair.
- Invalid, incomplete, or non-UTF-8 byte input fails explicitly with no partial
  successful output. Decode rejects invalid token IDs and token sequences that
  do not form complete strict UTF-8. There is no replacement-mode fallback.
- NUL, newlines, tabs, bidi controls, noncharacters, and other valid Unicode are
  data. Their presence grants no authorization and triggers no hidden parsing.

### Pretokenization and ordinary tokens

- Pretokenization is the whole strict UTF-8 byte sequence; there are no regex,
  word, whitespace, language, code, security-identifier, or locale boundaries.
- Ordinary IDs `0..255` are the fixed byte fallback alphabet. Learned byte-BPE
  IDs are consecutive from `256` in canonical merge order and may not exceed
  `511` for Tokenizer v1. Every ordinary token maps to a non-empty byte string.
- Ordered merge rules, ordinary token bytes/IDs, merge configuration, input
  encoding, normalization and pretokenization identifiers are canonical
  fingerprint inputs. Training tie-breaking remains deterministic and integer
  based. No random seed or runtime vocabulary mutation is permitted.

### Initial special-token allocation

The initial allocation is deliberately small and model-neutral:

| Role | ID | Literal rendering | Insertion rule |
| --- | ---: | --- | --- |
| `bos` | 512 | `<\|bos\|>` | only when explicitly requested |
| `eos` | 513 | `<\|eos\|>` | only after a complete, non-truncated encode when explicitly requested |
| `pad` | 514 | `<\|pad\|>` | never inserted by tokenizer encode |

- Vocabulary size is 515 and valid IDs are `0..514`. Special IDs never appear in
  the learned merge graph and cannot overlap ordinary IDs.
- There is no `unknown` token because byte fallback represents every valid UTF-8
  input. Mask, separator, role, tool, memory, document, modality, and other
  control tokens are deferred until a model contract demonstrates need and
  receives separate acceptance.
- Literal strings such as `<|bos|>` are ordinary untrusted text. They never
  become special IDs through ordinary encoding. Special insertion uses a typed
  request mode, not text matching. Unknown roles and IDs fail explicitly.
- Decode uses an explicit special-token mode. `reject` fails on any special ID;
  `preserve` returns typed special segments rather than injecting control meaning;
  `render` emits the fixed literal rendering as untrusted text. No mode executes,
  authorizes, or interprets a role.

### Truncation and streaming

- Encoding never truncates unless an explicit maximum-token policy is supplied.
  The limit includes requested `bos`/`eos` tokens.
- Truncation selects the longest token prefix within the limit whose concatenated
  ordinary bytes end on a complete UTF-8 scalar boundary. It may backtrack from
  a raw token-count boundary. A truncated result never appends `eos` and must
  report `truncated`; `bos` is retained only if it fits.
- A complete result appends requested `eos` only if the full ordinary sequence
  and all requested special tokens fit. No silent fallback drops special tokens.
- Buffered streaming retains P6.5 semantics: bounded ordered byte chunks, no
  progressive token emission, strict validation at finalization, and exact
  equivalence to one-shot encoding for the same request. Cancellation, deadline,
  byte, chunk, and output limits remain terminal and cannot yield partial output.

### Offset semantics

- Offset requests are optional and fingerprint-defining. Each ordinary token has
  a half-open `[start_byte, end_byte)` span into the original strict UTF-8 byte
  sequence. Spans are ordered, adjacent, non-overlapping, and cover exactly the
  emitted ordinary bytes.
- Because normalization is `none`, original and normalized byte spans are
  identical. Byte offsets, not Python indices, UTF-16 units, or grapheme counts,
  are canonical.
- An optional Unicode-scalar span is present only when both token byte endpoints
  align to scalar boundaries. A token that starts or ends inside a multi-byte
  scalar has no scalar span. Consumers must not invent one.
- `bos` uses zero-width byte/scalar span at input start; `eos` uses zero-width
  span at input end. `pad` has no source span. Truncated output covers only its
  emitted prefix and records the first omitted byte offset.

## Identity and compatibility

- The Tokenizer v1 behavior fingerprint covers canonical ordinary tokens and
  merges, this semantic profile identifier, artifact/algorithm versions,
  strict-UTF-8 and byte-fallback behavior, normalization/pretokenization,
  truncation, streaming finalization, offset rules, and exact special-role/ID/
  rendering/insertion/decode policies.
- Model compatibility is exact fingerprint equality only. Vocabulary size,
  algorithm label, filename, mutable version tag, artifact digest, or common
  token prefix is insufficient. Tokenizer v1 defines no compatibility aliases.
- The artifact digest also binds provenance and license metadata and may differ
  across byte-distinct envelopes that reconstruct identical behavior. Such an
  artifact is usable only if its provenance/license/approval policy is accepted;
  equal behavior fingerprint alone does not approve distribution.
- Any behavior change produces a new fingerprint and requires new conformance
  vectors. Artifact-only migration may preserve a behavior fingerprint only
  after byte-for-byte behavioral replay over the accepted canonical vectors.

## Security and implementation requirements

- Tokenizer inputs, IDs, offsets, literal special-looking text, artifact bytes,
  descriptors, provenance, and decoded output remain untrusted data and never
  authorization or executable instructions.
- Validate versions, counts, sizes, IDs, lengths, digests, special allocations,
  merge references, and offset bounds before allocation or use. No dynamic code,
  callback, plugin, external reference, path, network, provider, subprocess, or
  automatic artifact substitution is permitted.
- Implementation must add typed immutable request/result contracts, canonical
  fingerprint encoding, exhaustive positive/negative known vectors, every
  relevant UTF-8 and merge boundary, special-token injection denial, truncation
  backtracking, offset invariants, artifact round trips, identity sensitivity,
  exact compatibility rejection, cancellation/deadline/resource failures, and
  content-minimizing errors/logging.
- Preserve unchanged Ruff, Black, strict mypy, repository/security validation,
  dependency consistency, split-package imports, pytest at 100% tokenizer source
  coverage on Python 3.11–3.13, package build, and exact distribution checks.

The gate acceptance permits only the separately reviewed implementation in
`P6_9_PRODUCTION_SEMANTICS_EVIDENCE.md`. That implementation requires its own
exact-head acceptance and verified merge. No production training or later P6
work begins through this acceptance.
