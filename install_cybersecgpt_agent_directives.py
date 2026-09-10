#!/usr/bin/env python3
"""
CyberSecGPT Agent Directive Installer / Verifier — Policy Version 2.1

Read order enforced by policy:
  1. CYBERSECGPT_MASTER_SYSTEM_INSTRUCTIONS.md
  2. CYBERSECGPT_MASTER_AUTONOMOUS_AI_BRAIN_SPECIFICATION.md
  3. CYBERSECGPT_DEEP_REASONING_BRAIN_IMPLEMENTATION_DIRECTIVE.md

Canonical docs location:
  cybersecgpt-docs/engineering/

Protection:
- MASTER_SYSTEM is operator-owned and is NEVER overwritten automatically.
- MASTER_BRAIN is authoritative and is NEVER overwritten automatically when it differs.
- The deep-reasoning directive and agent policy files are managed and may be upgraded
  only with --upgrade, with backups created first.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

POLICY_VERSION = "2.1"
MASTER_SYSTEM = "CYBERSECGPT_MASTER_SYSTEM_INSTRUCTIONS.md"
MASTER_BRAIN = "CYBERSECGPT_MASTER_AUTONOMOUS_AI_BRAIN_SPECIFICATION.md"
DIRECTIVE = "CYBERSECGPT_DEEP_REASONING_BRAIN_IMPLEMENTATION_DIRECTIVE.md"
AGENTS = "AGENTS.md"
COPILOT = Path(".github") / "copilot-instructions.md"
WORKFLOW = Path(".github") / "workflows" / "cybersecgpt-agent-policy.yml"
INSTALLER = "install_cybersecgpt_agent_directives.py"
LOCK = Path(".cybersecgpt") / "agent-policy.lock.json"

PACK_DIR = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def backup(path: Path) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dst = path.with_name(f"{path.name}.bak.{stamp}")
    shutil.copy2(path, dst)
    print(f"backup: {dst}")


def sibling_docs_repo(repo: Path) -> Path:
    if repo.name.lower() == "cybersecgpt-docs":
        return repo
    return repo.parent / "cybersecgpt-docs"


def canonical_engineering_dir(repo: Path) -> Path:
    return sibling_docs_repo(repo) / "engineering"


def exact_candidates(repo: Path, filename: str) -> list[Path]:
    docs = sibling_docs_repo(repo)
    return [
        repo / filename,
        docs / "engineering" / filename,
        docs / filename,
        repo / "engineering" / filename,
        repo / "docs" / "engineering" / filename,
        repo / "docs" / filename,
    ]


def locate(repo: Path, filename: str) -> Path | None:
    for p in exact_candidates(repo, filename):
        try:
            if p.is_file():
                return p.resolve()
        except OSError:
            pass
    return None


def copy_if_absent(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(src, dst)
        print(f"installed mirror: {dst}")


def ensure_protected_local_mirror(repo: Path, canonical: Path, filename: str) -> Path:
    """
    Create a local exact mirror if missing.
    NEVER overwrite a differing local protected file.
    """
    local = repo / filename
    if not local.exists():
        shutil.copy2(canonical, local)
        print(f"installed protected local mirror: {local}")
        return local.resolve()

    if sha256(local) != sha256(canonical):
        raise RuntimeError(
            f"Protected doctrine differs from canonical and was NOT overwritten:\n"
            f"  local: {local}\n"
            f"  canonical: {canonical}\n"
            "Review and reconcile manually."
        )
    print(f"protected mirror matches: {local}")
    return local.resolve()


def ensure_canonical_brain_spec(repo: Path) -> Path:
    eng = canonical_engineering_dir(repo)
    eng.mkdir(parents=True, exist_ok=True)
    canonical = eng / MASTER_BRAIN
    bundled = PACK_DIR / MASTER_BRAIN

    if canonical.exists():
        if sha256(canonical) != sha256(bundled):
            print(
                "NOTICE: canonical autonomous AI brain specification differs from "
                "the bundled V2.1 snapshot. Canonical file is preserved."
            )
        return canonical.resolve()

    if not bundled.is_file():
        raise FileNotFoundError(f"Bundled brain specification missing: {bundled}")

    shutil.copy2(bundled, canonical)
    print(f"installed canonical brain specification: {canonical}")
    return canonical.resolve()


def ensure_canonical_directive(repo: Path, upgrade: bool) -> Path:
    eng = canonical_engineering_dir(repo)
    eng.mkdir(parents=True, exist_ok=True)
    canonical = eng / DIRECTIVE
    bundled = PACK_DIR / DIRECTIVE

    if not bundled.is_file():
        raise FileNotFoundError(f"Bundled directive missing: {bundled}")

    if canonical.exists():
        if sha256(canonical) == sha256(bundled):
            print(f"canonical directive unchanged: {canonical}")
            return canonical.resolve()
        if not upgrade:
            raise RuntimeError(
                f"Canonical directive differs: {canonical}\n"
                "Re-run with --upgrade after review. A backup will be created."
            )
        backup(canonical)

    shutil.copy2(bundled, canonical)
    print(f"installed canonical directive: {canonical}")
    return canonical.resolve()


def install_managed(src: Path, dst: Path, upgrade: bool) -> None:
    src = src.resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)

    try:
        if dst.exists() and dst.resolve() == src:
            print(f"managed source already local: {dst}")
            return
    except OSError:
        pass

    if dst.exists():
        if sha256(src) == sha256(dst):
            print(f"unchanged: {dst}")
            return
        if not upgrade:
            raise RuntimeError(
                f"Managed policy file differs: {dst}\n"
                "Re-run with --upgrade after review. A backup will be created."
            )
        backup(dst)

    shutil.copy2(src, dst)
    print(f"installed: {dst}")


def find_canonical_system(repo: Path) -> Path:
    # The exact canonical location is preferred and required for workspace installation.
    canonical = canonical_engineering_dir(repo) / MASTER_SYSTEM
    if canonical.is_file():
        return canonical.resolve()

    # Standalone fallback: a local mirror can serve verification after cloning.
    local = repo / MASTER_SYSTEM
    if local.is_file():
        return local.resolve()

    raise FileNotFoundError(
        f"Required {MASTER_SYSTEM} not found.\n"
        f"Expected canonical location: {canonical}\n"
        "This V2.1 pack intentionally does not invent or overwrite master system instructions."
    )


def write_lock(repo: Path, files: dict[str, Path]) -> None:
    payload = {
        "schema": 3,
        "policy_version": POLICY_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_order": [
            MASTER_SYSTEM,
            MASTER_BRAIN,
            DIRECTIVE,
        ],
        "canonical_docs_location": "cybersecgpt-docs/engineering/",
    }

    for key, path in files.items():
        try:
            rel = str(path.relative_to(repo))
        except ValueError:
            rel = str(path)
        payload[key] = {"path": rel, "sha256": sha256(path)}

    target = repo / LOCK
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"lock: {target}")


def verify_contains(path: Path, concepts: list[str], errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8").lower()
    for c in concepts:
        if c.lower() not in text:
            errors.append(f"{path} missing required concept: {c}")


def verify(repo: Path) -> int:
    errors: list[str] = []

    required_local = {
        "master_system": repo / MASTER_SYSTEM,
        "master_brain": repo / MASTER_BRAIN,
        "deep_reasoning_directive": repo / DIRECTIVE,
        "agents": repo / AGENTS,
        "copilot_instructions": repo / COPILOT,
        "policy_workflow": repo / WORKFLOW,
        "installer": repo / INSTALLER,
    }

    for key, path in required_local.items():
        if not path.is_file():
            errors.append(f"Missing local required file ({key}): {path}")

    lock_path = repo / LOCK
    if not lock_path.is_file():
        errors.append(f"Missing policy lock: {lock_path}")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 2

    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: cannot parse {lock_path}: {exc}", file=sys.stderr)
        return 2

    if lock.get("policy_version") != POLICY_VERSION:
        errors.append(
            f"Policy version mismatch: lock={lock.get('policy_version')} expected={POLICY_VERSION}"
        )

    expected_order = [MASTER_SYSTEM, MASTER_BRAIN, DIRECTIVE]
    if lock.get("read_order") != expected_order:
        errors.append(f"Read-order mismatch in policy lock: {lock.get('read_order')}")

    for key, path in required_local.items():
        expected = lock.get(key, {}).get("sha256")
        actual = sha256(path)
        if expected != actual:
            errors.append(
                f"Policy drift: {key} hash differs. expected={expected} actual={actual}"
            )

    verify_contains(
        repo / AGENTS,
        [
            MASTER_SYSTEM,
            MASTER_BRAIN,
            DIRECTIVE,
            "Mandatory Read Order",
            "Hybrid Intelligence Architecture",
            "Intelligence Router",
            "Verification",
        ],
        errors,
    )
    verify_contains(
        repo / COPILOT,
        [
            MASTER_SYSTEM,
            MASTER_BRAIN,
            DIRECTIVE,
            "Hybrid intelligence is mandatory",
            "Intelligence Router",
            "Tool security",
        ],
        errors,
    )
    verify_contains(
        repo / DIRECTIVE,
        [
            "Instruction Stack, Canonical Location, and Authority",
            "cybersecgpt-docs/",
            "Hybrid Intelligence Architecture",
            "Intelligence Router",
            "Adaptive reasoning budgets",
            "Definition of Done",
        ],
        errors,
    )

    # In cybersecgpt-docs, also verify canonical engineering copies.
    if repo.name.lower() == "cybersecgpt-docs":
        eng = repo / "engineering"
        for name in (MASTER_SYSTEM, MASTER_BRAIN, DIRECTIVE):
            p = eng / name
            if not p.is_file():
                errors.append(f"Missing canonical engineering document: {p}")

        if (eng / MASTER_SYSTEM).is_file():
            if sha256(eng / MASTER_SYSTEM) != sha256(repo / MASTER_SYSTEM):
                errors.append("Local master-system mirror differs from canonical engineering copy.")
        if (eng / MASTER_BRAIN).is_file():
            if sha256(eng / MASTER_BRAIN) != sha256(repo / MASTER_BRAIN):
                errors.append("Local brain-spec mirror differs from canonical engineering copy.")
        if (eng / DIRECTIVE).is_file():
            if sha256(eng / DIRECTIVE) != sha256(repo / DIRECTIVE):
                errors.append("Local directive mirror differs from canonical engineering copy.")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 2

    print("PASS: CyberSecGPT V2.1 policy is installed and hash-consistent.")
    print(f"policy version: {POLICY_VERSION}")
    print("read order:")
    print(f"  1. {MASTER_SYSTEM}")
    print(f"  2. {MASTER_BRAIN}")
    print(f"  3. {DIRECTIVE}")
    return 0


def install(repo: Path, upgrade: bool) -> int:
    # 1) Locate protected canonical master-system instructions.
    canonical_system = find_canonical_system(repo)

    # 2) Establish canonical autonomous-brain specification under docs/engineering.
    canonical_brain = ensure_canonical_brain_spec(repo)

    # 3) Establish/update canonical deep-reasoning directive under docs/engineering.
    canonical_directive = ensure_canonical_directive(repo, upgrade=upgrade)

    # 4) Create exact local protected mirrors.
    local_system = ensure_protected_local_mirror(repo, canonical_system, MASTER_SYSTEM)
    local_brain = ensure_protected_local_mirror(repo, canonical_brain, MASTER_BRAIN)

    # 5) Install local managed directive and agent policy files.
    install_managed(canonical_directive, repo / DIRECTIVE, upgrade)
    install_managed(PACK_DIR / AGENTS, repo / AGENTS, upgrade)
    install_managed(PACK_DIR / COPILOT, repo / COPILOT, upgrade)
    install_managed(PACK_DIR / WORKFLOW, repo / WORKFLOW, upgrade)
    install_managed(PACK_DIR / INSTALLER, repo / INSTALLER, upgrade)

    files = {
        "master_system": repo / MASTER_SYSTEM,
        "master_brain": repo / MASTER_BRAIN,
        "deep_reasoning_directive": repo / DIRECTIVE,
        "agents": repo / AGENTS,
        "copilot_instructions": repo / COPILOT,
        "policy_workflow": repo / WORKFLOW,
        "installer": repo / INSTALLER,
    }
    write_lock(repo, files)

    print("\nInstalled CyberSecGPT Agent Directive Pack V2.1.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--verify", action="store_true")
    parser.add_argument(
        "--upgrade",
        action="store_true",
        help="Upgrade managed V2 policy files to V2.1 after backups. Protected master documents are never overwritten.",
    )
    args = parser.parse_args()

    repo = args.repo.resolve()
    if not repo.is_dir():
        print(f"ERROR: repository does not exist: {repo}", file=sys.stderr)
        return 2

    try:
        return verify(repo) if args.verify else install(repo, args.upgrade)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
