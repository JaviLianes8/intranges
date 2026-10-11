"""Typed two-way conversion between a compact range string and a list of ints."""

from __future__ import annotations

from ._compact import compact
from ._errors import RangeError
from ._parse import parse

__version__ = "0.1.0"

__all__ = ["RangeError", "compact", "parse"]
