"""Guards the layering: dependencies may only point inwards (adapters/config -> core)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[1] / "src" / "voicescribe"

# layer -> voicescribe sub-packages it must never import
FORBIDDEN = {
    "core": {"config", "application", "adapters", "cli"},
    "config": {"application", "adapters", "cli"},
    "adapters": {"application", "cli"},
    "application": {"cli"},
}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
    return names


@pytest.mark.parametrize("layer", sorted(FORBIDDEN))
def test_layer_dependencies_point_inwards(layer: str) -> None:
    violations = [
        f"{path.relative_to(PACKAGE)} imports {name}"
        for path in (PACKAGE / layer).rglob("*.py")
        for name in _imports(path)
        if name.startswith("voicescribe.") and name.split(".")[1] in FORBIDDEN[layer]
    ]

    assert violations == []


def test_core_uses_only_the_standard_library() -> None:
    third_party = [
        f"{path.relative_to(PACKAGE)} imports {name}"
        for path in (PACKAGE / "core").rglob("*.py")
        for name in _imports(path)
        if name.split(".")[0] not in sys.stdlib_module_names
        and not name.startswith("voicescribe.core")
        and name != "__future__"
    ]

    assert third_party == []
