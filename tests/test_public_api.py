"""Public API boundary tests."""

import cybersecgpt.tokenizer as tokenizer


def test_public_api_is_explicit() -> None:
    assert tokenizer.__all__ == [
        "MAX_IDENTIFIER_LENGTH",
        "MAX_EVALUATION_SAMPLES",
        "MAX_TEXT_BYTES",
        "MAX_TOKEN_COUNT",
        "MAX_VOCABULARY_SIZE",
        "UTF8_BYTE_REFERENCE_FINGERPRINT",
        "DecodeRequest",
        "DecodeResult",
        "EncodeRequest",
        "EncodeResult",
        "EvaluationDomain",
        "EvaluationManifest",
        "EvaluationSample",
        "FinishStatus",
        "ReferenceSampleMetrics",
        "SpecialToken",
        "TokenizerContractError",
        "TokenizerDescriptor",
        "Utf8ByteReferenceTokenizer",
        "evaluate_utf8_byte_reference",
    ]
