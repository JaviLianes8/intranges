"""Typed two-way conversion between compact range strings and integers.

``parse`` and ``compact`` convert between strings like ``"1-3,5,7-9"`` and lists of
ints. ``IntRanges`` is a lazy, immutable set that never expands its ranges, and
``parse_ranges``, ``count`` and ``normalize`` read strings into it. Named dialects cover
printer page lists, Linux cpu lists, Slurm indexes and HTTP byte ranges.
"""

from __future__ import annotations

from ._compact import compact
from ._dialect import CPULIST, DEFAULT, DIALECTS, HTTP, PAGES, SLURM, Dialect
from ._errors import (
    DescendingRangeError,
    RangeBoundsError,
    RangeError,
    RangeOrderError,
    RangeOverlapError,
    RangeSizeError,
    RangeSyntaxError,
)
from ._intranges import IntRanges
from ._parse import DEFAULT_MAX_SIZE, DEFAULT_MAX_SPANS, count, normalize, parse, parse_ranges

__version__ = "0.2.0"

__all__ = [
    "CPULIST",
    "DEFAULT",
    "DEFAULT_MAX_SIZE",
    "DEFAULT_MAX_SPANS",
    "DIALECTS",
    "HTTP",
    "PAGES",
    "SLURM",
    "DescendingRangeError",
    "Dialect",
    "IntRanges",
    "RangeBoundsError",
    "RangeError",
    "RangeOrderError",
    "RangeOverlapError",
    "RangeSizeError",
    "RangeSyntaxError",
    "compact",
    "count",
    "normalize",
    "parse",
    "parse_ranges",
]
