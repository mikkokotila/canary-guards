"""Negative test (#63): a tree that weakens safety fails the guard.

Self-contained: builds evil fixture trees, never touches PR_TREE.
"""
import pytest

import test_prod_gate_external as external
import test_static_tripwires as tripwires


@pytest.fixture()
def evil_tree(tmp_path, monkeypatch):
    evil = tmp_path / "evil"
    (evil / "scripts").mkdir(parents=True)
    (evil / "scripts" / "prod_gate.sh").write_text("#!/bin/bash\nexit 0\n")
    (evil / "scripts" / "container_run.sh").write_text(
        "#!/bin/bash\ndocker build .\nbash scripts/prod_gate.sh . \"$@\"\n")
    ci = evil / ".github" / "workflows"
    ci.mkdir(parents=True)
    (ci / "ci.yml").write_text("name: ci\njobs:\n  smoke:\n    runs-on: ubuntu-latest\n")
    (evil / "Dockerfile").write_text("FROM x\nCOPY .env /app/.env\n")
    monkeypatch.setenv("PR_TREE", str(evil))
    return evil


def test_gutted_gate_fails_behavioral_suite(evil_tree, tmp_path):
    first, second = tmp_path / "t1", tmp_path / "t2"
    first.mkdir()
    second.mkdir()
    with pytest.raises(AssertionError):
        external.test_prod_refuses_branch_and_detached(first)
    with pytest.raises(AssertionError):
        external.test_prod_refuses_stale_and_ahead_main(second)


def test_gutted_ci_launcher_and_dockerfile_trip_wires(evil_tree):
    with pytest.raises(AssertionError):
        tripwires.test_ci_invokes_pinned_guard()
    with pytest.raises(AssertionError):
        tripwires.test_launcher_invokes_prod_gate_pre_build()
    with pytest.raises(AssertionError):
        tripwires.test_no_credential_files_baked_into_images()
