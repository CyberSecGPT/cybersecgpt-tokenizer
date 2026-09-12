"""Verify tokenizer wheel ownership and dependency boundaries."""

import argparse
import zipfile
from email.parser import Parser
from pathlib import Path

EXPECTED_SOURCE_MEMBERS = frozenset(
    {
        "cybersecgpt/tokenizer/__init__.py",
        "cybersecgpt/tokenizer/byte_bpe.py",
        "cybersecgpt/tokenizer/contracts.py",
        "cybersecgpt/tokenizer/evaluation.py",
        "cybersecgpt/tokenizer/py.typed",
        "cybersecgpt/tokenizer/reference.py",
        "cybersecgpt/tokenizer/unigram.py",
    }
)
PROVIDER_MARKERS = (
    "openai",
    "anthropic",
    "cohere",
    "google-generativeai",
    "google-genai",
)


class DistributionVerificationError(RuntimeError):
    """Report a distribution boundary violation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DistributionVerificationError(message)


def verify_wheel(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        source_members = {name for name in names if name.startswith("cybersecgpt/")}
        _require(
            source_members == EXPECTED_SOURCE_MEMBERS,
            f"wheel source members are incorrect: {sorted(source_members)}",
        )
        _require(
            "cybersecgpt/__init__.py" not in names,
            "tokenizer wheel must not own the top-level namespace package",
        )
        metadata_names = [
            name for name in names if name.endswith(".dist-info/METADATA")
        ]
        _require(
            len(metadata_names) == 1,
            "wheel must contain exactly one METADATA file",
        )
        metadata = Parser().parsestr(archive.read(metadata_names[0]).decode("utf-8"))
        _require(
            metadata.get("Name") == "cybersecgpt-tokenizer",
            "wheel Name is incorrect",
        )
        _require(metadata.get("Version") == "0.1.0", "wheel Version is incorrect")
        requirements = [str(item) for item in metadata.get_all("Requires-Dist", [])]
        runtime_requirements = [
            item for item in requirements if "; extra ==" not in item
        ]
        _require(
            runtime_requirements == [],
            f"unexpected runtime dependencies: {runtime_requirements}",
        )
        normalized = "\n".join(requirements).lower()
        _require(
            not any(marker in normalized for marker in PROVIDER_MARKERS),
            "provider SDK dependency detected in wheel metadata",
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    wheels = sorted(args.directory.glob("*.whl"))
    _require(len(wheels) == 1, f"expected one wheel, found {len(wheels)}")
    verify_wheel(wheels[0])
    print("Tokenizer distribution verification passed.")


if __name__ == "__main__":
    main()
