"""Collapse integers into a canonical range string."""

from __future__ import annotations

from collections.abc import Iterable

from . import _spans as sp
from ._dialect import DEFAULT, Dialect
from ._errors import RangeBoundsError


def _number(value: int, width: int | None) -> str:
    return str(value) if width is None else f"{value:0{width}d}"


def format_spans(spans: sp.Spans, dialect: Dialect, width: int | None) -> str:
    """Write canonical spans in ``dialect``; ``width`` zero-pads every number."""
    if width is not None and width < 1:
        raise ValueError(f"width must be at least 1, got {width}")
    if spans:
        low = spans[0][0]
        if (low < 0 and not dialect.negatives) or (
            dialect.minimum is not None and low < dialect.minimum
        ):
            raise RangeBoundsError(f"{low} cannot be written in the {dialect.name} dialect")
    parts = []
    for low, high in spans:
        text = _number(low, width)
        if high != low:
            text += dialect.range_sep + _number(high, width)
        parts.append(text)
    body = dialect.list_sep.join(parts)
    return dialect.prefix + body if body else ""


def compact(
    values: Iterable[int],
    *,
    range_sep: str | None = None,
    list_sep: str | None = None,
    dialect: Dialect = DEFAULT,
    width: int | None = None,
) -> str:
    """Collapse integers into the canonical range string, such as ``"1-3,5-6"``.

    The input is sorted and de-duplicated first, so unsorted or repeated values are
    accepted. Runs of two or more consecutive values become ``low-high``. An empty input
    yields an empty string. An :class:`IntRanges` or a step-1 ``range`` is written from
    its spans without being expanded.

    Args:
        values: Integers in any order, an :class:`IntRanges` or a ``range``.
        range_sep: Overrides ``dialect.range_sep``.
        list_sep: Overrides ``dialect.list_sep``.
        dialect: Output grammar. Its ``prefix`` (``"bytes="`` for ``HTTP``) is written.
        width: Zero-pad every number to this many characters, as in Slurm hostlists
            such as ``"001-010"``.

    Raises:
        RangeBoundsError: A value cannot be written in the dialect (negative where
            negatives are off, or below the dialect minimum).
        TypeError: A value is not an integer.

    >>> compact([6, 5, 1, 3, 2])
    '1-3,5-6'
    >>> compact(range(1, 11), width=3)
    '001-010'
    """
    from ._intranges import _spans_of

    chosen = dialect.with_separators(range_sep, list_sep)
    return format_spans(_spans_of(values), chosen, width)
