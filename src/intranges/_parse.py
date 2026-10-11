"""Expand compact range strings into lists of integers."""

from __future__ import annotations

import re
from functools import cache

from ._errors import RangeError


@cache
def _token_pattern(range_sep: str) -> re.Pattern[str]:
    sep = re.escape(range_sep)
    return re.compile(rf"^(-?\d+)(?:\s*{sep}\s*(-?\d+))?$")


def parse(text: str, *, range_sep: str = "-", list_sep: str = ",") -> list[int]:
    """Expand a compact range string such as ``"1-5,8,10-12"`` into a list of ints.

    Whitespace around tokens is ignored. A bound may be negative. Each range runs
    low to high: a descending range is rejected with :class:`RangeError`.
    """
    if not range_sep:
        raise ValueError("range_sep must not be empty")
    if not list_sep:
        raise ValueError("list_sep must not be empty")

    result: list[int] = []
    if not text.strip():
        return result

    pattern = _token_pattern(range_sep)
    for raw in text.split(list_sep):
        token = raw.strip()
        if not token:
            raise RangeError(f"empty range token in {text!r}")
        match = pattern.fullmatch(token)
        if match is None:
            raise RangeError(f"invalid range token {token!r}")
        start = int(match.group(1))
        upper = match.group(2)
        if upper is None:
            result.append(start)
            continue
        end = int(upper)
        if end < start:
            raise RangeError(f"descending range {token!r}")
        result.extend(range(start, end + 1))
    return result
