"""Public API boundary tests."""

import cybersecgpt.tokenizer as tokenizer


def test_public_api_is_explicit() -> None:
    assert tokenizer.__all__ == [
        "BpeMerge",
        "BpeTrainingFinishStatus",
        "ByteBpeCandidate",
        "ByteBpeTrainingConfig",
        "ByteBpeTrainingResult",
        "ByteUnigramCandidate",
        "ByteUnigramTrainingConfig",
        "ByteUnigramTrainingResult",
        "CandidateEvaluationReport",
        "CandidateSampleMetrics",
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
        "ExactRatio",
        "FinishStatus",
        "ReferenceSampleMetrics",
        "SpecialToken",
        "TokenizerContractError",
        "TokenizerDescriptor",
        "Utf8ByteReferenceTokenizer",
        "UnigramTrainingFinishStatus",
        "evaluate_candidate",
        "evaluate_utf8_byte_reference",
        "train_byte_bpe_candidate",
        "train_byte_unigram_candidate",
    ]
