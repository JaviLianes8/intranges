"""Algebra on canonical spans: sorted, disjoint, non-adjacent, inclusive ``(low, high)``."""

from __future__ import annotations

from collections.abc import Iterable
from operator import index

Span = tuple[int, int]
Spans = tuple[Span, ...]


def coalesce(spans: Iterable[Span]) -> Spans:
    """Sort spans and merge every overlapping or adjacent pair."""
    out: list[Span] = []
    for low, high in sorted(spans):
        if out and low <= out[-1][1] + 1:
            if high > out[-1][1]:
                out[-1] = (out[-1][0], high)
        else:
            out.append((low, high))
    return tuple(out)


def from_ints(values: Iterable[int]) -> Spans:
    """Build canonical spans from integers, in any order, with repeats.

    Raises :class:`TypeError` for a value that is not an integer.
    """
    if isinstance(values, range) and values.step == 1:
        return ((values.start, values.stop - 1),) if values.start < values.stop else ()
    return coalesce((value, value) for value in map(index, values))


def union(a: Spans, b: Spans) -> Spans:
    return coalesce(a + b)


def intersection(a: Spans, b: Spans) -> Spans:
    out: list[Span] = []
    i = j = 0
    while i < len(a) and j < len(b):
        low = max(a[i][0], b[j][0])
        high = min(a[i][1], b[j][1])
        if low <= high:
            out.append((low, high))
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return tuple(out)


def difference(a: Spans, b: Spans) -> Spans:
    out: list[Span] = []
    j = 0
    for low, high in a:
        while j < len(b) and b[j][1] < low:
            j += 1
        k = j
        while k < len(b) and b[k][0] <= high:
            if b[k][0] > low:
                out.append((low, b[k][0] - 1))
            low = max(low, b[k][1] + 1)
            k += 1
        if low <= high:
            out.append((low, high))
    return tuple(out)


def complement(a: Spans, lower: int, upper: int) -> Spans:
    if lower > upper:
        raise ValueError(f"lower {lower} is greater than upper {upper}")
    return difference(((lower, upper),), a)


def is_subset(a: Spans, b: Spans) -> bool:
    return not difference(a, b)


def count(a: Spans) -> int:
    return sum(high - low + 1 for low, high in a)
