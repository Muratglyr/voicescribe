"""Access to files shipped inside the package (default config, prompts, messages)."""

from __future__ import annotations

from importlib import resources
from importlib.resources.abc import Traversable

RESOURCE_PACKAGE = __name__
RESOURCE_ENCODING = "utf-8"
DEFAULTS_FILE = "defaults.toml"
PROMPTS_DIR = "prompts"
MESSAGES_DIR = "messages"


def resource(*parts: str) -> Traversable:
    """Return a handle to a packaged resource, e.g. ``resource("prompts", "x.md")``."""
    return resources.files(RESOURCE_PACKAGE).joinpath(*parts)


def read_resource(*parts: str) -> str:
    """Read a packaged text resource."""
    return resource(*parts).read_text(encoding=RESOURCE_ENCODING)
