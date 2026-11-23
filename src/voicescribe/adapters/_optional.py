"""Lazy import of optional heavy dependencies with an actionable error message."""

from __future__ import annotations

import importlib
from types import ModuleType

from voicescribe.core.errors import DependencyError


def import_optional(module: str, *, extra: str, feature: str) -> ModuleType:
    """Import ``module`` or raise a :class:`DependencyError` naming the pip extra to install."""
    try:
        return importlib.import_module(module)
    except ImportError as error:
        raise DependencyError("error.missing_dependency", package=module, feature=feature, extra=extra) from error
