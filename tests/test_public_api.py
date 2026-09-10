"""Public API boundary tests."""

import cybersecgpt.tokenizer as tokenizer


def test_public_api_is_explicit() -> None:
    assert tokenizer.__all__ == [
        "MAX_IDENTIFIER_LENGTH",
        "MAX_TEXT_BYTES",
        "MAX_TOKEN_COUNT",
        "MAX_VOCABULARY_SIZE",
        "DecodeRequest",
        "DecodeResult",
        "EncodeRequest",
        "EncodeResult",
        "FinishStatus",
        "SpecialToken",
        "TokenizerContractError",
        "TokenizerDescriptor",
    ]
