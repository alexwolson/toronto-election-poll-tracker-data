"""Tests for process_all.py import correctness."""
import importlib
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent


def test_process_all_imports_cleanly():
    """process_all must import without ModuleNotFoundError.

    This catches the src.* → backend.model.* migration bug.
    """
    # Remove any cached version so we get a fresh import
    for key in list(sys.modules.keys()):
        if "process_all" in key:
            del sys.modules[key]

    spec = importlib.util.spec_from_file_location(
        "scripts.process_all",
        str(_REPO_ROOT / "scripts" / "process_all.py"),
    )
    assert spec is not None, "Could not locate scripts/process_all.py — check _REPO_ROOT path"

    module = importlib.util.module_from_spec(spec)
    # We only test that the module-level code (imports, constants) doesn't crash.
    # We don't call main() since that requires data files.
    try:
        spec.loader.exec_module(module)
    except SystemExit:
        pass  # main() calls sys.exit on missing files — that's fine

    assert module is not None
    # Verify the key backend.model symbols are importable — this is the actual bug we're guarding
    from backend.model import aggregator, coattails, lean, names, validate  # noqa: F401
