"""Validate tokenizer repository security and dependency boundaries."""

import re
import tomllib
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = frozenset(
    {
        ".gitattributes",
        ".github/workflows/ci.yml",
        ".gitignore",
        "AGENTS.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "P6_ACCEPTANCE.md",
        "README.md",
        "SECURITY.md",
        "docs/ARCHITECTURE.md",
        "pyproject.toml",
        "scripts/validate_repository.py",
        "scripts/verify_distribution.py",
        "src/cybersecgpt/tokenizer/__init__.py",
        "src/cybersecgpt/tokenizer/contracts.py",
        "src/cybersecgpt/tokenizer/evaluation.py",
        "src/cybersecgpt/tokenizer/py.typed",
        "src/cybersecgpt/tokenizer/reference.py",
        "tests/__init__.py",
        "tests/test_contracts.py",
        "tests/test_evaluation.py",
        "tests/test_public_api.py",
        "tests/test_reference.py",
    }
)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
)
PROVIDER_MARKERS = (
    "openai",
    "anthropic",
    "cohere",
    "google-generativeai",
    "google-genai",
)
TEXT_SUFFIXES = frozenset({".md", ".py", ".toml", ".txt", ".yml", ".yaml"})
TEXT_NAMES = frozenset({".gitattributes", ".gitignore"})


class RepositoryValidationError(RuntimeError):
    """Report a repository policy violation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RepositoryValidationError(message)


def main() -> None:
    missing = sorted(path for path in REQUIRED_FILES if not (ROOT / path).is_file())
    _require(not missing, f"required repository files are missing: {missing}")

    with (ROOT / "pyproject.toml").open("rb") as stream:
        parsed = cast(dict[str, object], tomllib.load(stream))
    project = parsed.get("project")
    _require(isinstance(project, dict), "pyproject project table is missing")
    dependencies = cast(dict[str, object], project).get("dependencies")
    _require(dependencies == [], f"runtime dependency boundary changed: {dependencies}")
    normalized = "\n".join(cast(list[str], dependencies)).lower()
    _require(
        not any(marker in normalized for marker in PROVIDER_MARKERS),
        "provider SDK dependency detected in core runtime dependencies",
    )

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".") and part not in {".github"} for part in path.parts):
            continue
        if any(part in {"build", "dist", "__pycache__"} for part in path.parts):
            continue
        if path.suffix not in TEXT_SUFFIXES and path.name not in TEXT_NAMES:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in SECRET_PATTERNS:
            _require(
                pattern.search(text) is None,
                f"sensitive material pattern detected in {path.relative_to(ROOT)}",
            )

    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    _require("offline" in readme, "README must preserve offline operation")
    _require("authorization" in readme, "README must preserve non-authorization")
    print("Tokenizer repository validation passed.")


if __name__ == "__main__":
    main()
