"""Static tripwires over the target tree: guard presence, no baked creds."""
import os
import re
from pathlib import Path


def _tree() -> Path:
    try:
        return Path(os.environ["PR_TREE"])
    except KeyError:
        raise RuntimeError("PR_TREE must point at the checked-out target repo")


def test_ci_invokes_pinned_guard():
    text = (_tree() / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8")
    assert re.search(
        r"uses:\s*mikkokotila/canary-guards/\.github/workflows/guard\.yml@([0-9a-f]{40})",
        text), "ci.yml must invoke the pinned external guard"


def test_launcher_invokes_prod_gate_pre_build():
    text = (_tree() / "scripts" / "container_run.sh").read_text(encoding="utf-8")
    assert (_tree() / "scripts" / "prod_gate.sh").exists()
    assert text.index("prod_gate.sh") < text.index("docker build")


def test_no_credential_files_baked_into_images():
    for df in ("Dockerfile", "boundary/Dockerfile"):
        for i, line in enumerate(
                (_tree() / df).read_text(encoding="utf-8").splitlines(), 1):
            if line.strip().upper().startswith("COPY"):
                low = line.lower()
                assert ".env" not in low and ".key" not in low \
                    and "secret" not in low, f"{df}:{i}"
    ignore = (_tree() / ".dockerignore").read_text(encoding="utf-8")
    assert ".env" in ignore and "*.key" in ignore  # COPY . relies on this
