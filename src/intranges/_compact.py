"""Collapse integers into a compact range string."""

from __future__ import annotations

from collections.abc import Iterable


def _format_run(start: int, end: int, range_sep: str) -> str:
    if start == end:
        return str(start)
    return f"{start}{range_sep}{end}"


def compact(values: Iterable[int], *, range_sep: str = "-", list_sep: str = ",") -> str:
    """Collapse integers into a compact range string such as ``"1-3,5-6"``.

    The input is sorted and de-duplicated first, so unsorted or repeated values are
    accepted. An empty input yields an empty string.
    """
    ordered = sorted(set(values))
    if not ordered:
        return ""

    parts: list[str] = []
    start = previous = ordered[0]
    for value in ordered[1:]:
        if value == previous + 1:
            previous = value
            continue
        parts.append(_format_run(start, previous, range_sep))
        start = previous = value
    parts.append(_format_run(start, previous, range_sep))
    return list_sep.join(parts)
