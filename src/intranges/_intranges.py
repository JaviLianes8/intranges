"""A lazy, immutable set of integers stored as spans."""

from __future__ import annotations

from bisect import bisect_right
from collections.abc import Iterable, Iterator, Set
from operator import index
from typing import Any

from . import _spans as sp
from ._dialect import DEFAULT, Dialect


class IntRanges(Set[int]):
    """An immutable set of integers that never expands its ranges.

    Values are kept as sorted, disjoint, inclusive spans, so ``IntRanges(range(10**12))``
    holds two integers. Membership is a binary search, :attr:`count` is arithmetic and
    iteration streams values in ascending order. Set operators (``|``, ``&``, ``-``,
    ``^``, ``<=``, ``<``, ``>=``, ``>``) work span by span when both sides are
    ``IntRanges``; any other iterable of ints is converted first. ``==`` and ``hash``
    compare ``IntRanges`` with ``IntRanges`` only, so the hash contract holds. ``in``
    accepts any ``__index__`` integer. ``len()`` stops at ``sys.maxsize``; use ``count``.

    >>> r = IntRanges.parse("1-3,10-12")
    >>> 11 in r, r.count, str(r | IntRanges([4]))
    (True, 6, '1-4,10-12')
    """

    __slots__ = ("_spans",)
    _spans: sp.Spans

    def __init__(self, values: Iterable[int] = ()) -> None:
        """Build from any iterable of ints; a ``range`` with step 1 is not expanded."""
        if isinstance(values, IntRanges):
            self._spans = values._spans
        else:
            self._spans = sp.from_ints(values)

    @classmethod
    def from_spans(cls, spans: Iterable[tuple[int, int]]) -> IntRanges:
        """Build from inclusive ``(low, high)`` pairs in any order, overlapping or not.

        Raises :class:`ValueError` when a pair has ``low > high`` and :class:`TypeError`
        when a bound is not an integer.
        """
        pairs = [(index(low), index(high)) for low, high in spans]
        for low, high in pairs:
            if low > high:
                raise ValueError(f"span ({low}, {high}) has low greater than high")
        return cls._wrap(sp.coalesce(pairs))

    @classmethod
    def parse(cls, text: str, **options: Any) -> IntRanges:
        """Read a range string; keyword options are those of :func:`parse_ranges`."""
        from ._parse import parse_ranges

        return parse_ranges(text, **options)

    @classmethod
    def _wrap(cls, spans: sp.Spans) -> IntRanges:
        obj = cls.__new__(cls)
        obj._spans = spans
        return obj

    @property
    def spans(self) -> tuple[tuple[int, int], ...]:
        """The canonical inclusive ``(low, high)`` spans, ascending and non-adjacent."""
        return self._spans

    @property
    def count(self) -> int:
        """Number of values, as an unbounded int."""
        return sp.count(self._spans)

    @property
    def first(self) -> int:
        """Smallest value. Raises :class:`ValueError` when empty."""
        if not self._spans:
            raise ValueError("first of an empty IntRanges")
        return self._spans[0][0]

    @property
    def last(self) -> int:
        """Largest value. Raises :class:`ValueError` when empty."""
        if not self._spans:
            raise ValueError("last of an empty IntRanges")
        return self._spans[-1][1]

    def __contains__(self, value: object) -> bool:
        try:
            value = index(value)  # type: ignore[arg-type]
        except TypeError:
            return False
        i = bisect_right(self._spans, value, key=lambda span: span[0]) - 1
        return i >= 0 and value <= self._spans[i][1]

    def __iter__(self) -> Iterator[int]:
        for low, high in self._spans:
            yield from range(low, high + 1)

    def __reversed__(self) -> Iterator[int]:
        for low, high in reversed(self._spans):
            yield from range(high, low - 1, -1)

    def __len__(self) -> int:
        return self.count

    def __bool__(self) -> bool:
        return bool(self._spans)

    def __hash__(self) -> int:
        return hash((IntRanges, self._spans))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, IntRanges):
            return self._spans == other._spans
        return NotImplemented

    def __repr__(self) -> str:
        return f"IntRanges({self.format()!r})"

    def __str__(self) -> str:
        return self.format()

    def __reduce__(self) -> tuple[Any, ...]:
        return (type(self).from_spans, (self._spans,))

    def format(self, dialect: Dialect = DEFAULT, *, width: int | None = None) -> str:
        """Write the canonical range string; see :func:`compact` for the options."""
        from ._compact import format_spans

        return format_spans(self._spans, dialect, width)

    def complement(self, lower: int, upper: int) -> IntRanges:
        """Values in ``lower..upper`` (inclusive) that are not in this set."""
        return self._wrap(sp.complement(self._spans, lower, upper))

    def union(self, *others: Iterable[int]) -> IntRanges:
        spans = self._spans
        for other in others:
            spans = sp.union(spans, _spans_of(other))
        return self._wrap(spans)

    def intersection(self, *others: Iterable[int]) -> IntRanges:
        spans = self._spans
        for other in others:
            spans = sp.intersection(spans, _spans_of(other))
        return self._wrap(spans)

    def difference(self, *others: Iterable[int]) -> IntRanges:
        spans = self._spans
        for other in others:
            spans = sp.difference(spans, _spans_of(other))
        return self._wrap(spans)

    def symmetric_difference(self, other: Iterable[int]) -> IntRanges:
        theirs = _spans_of(other)
        mine = self._spans
        return self._wrap(sp.union(sp.difference(mine, theirs), sp.difference(theirs, mine)))

    def issubset(self, other: Iterable[int]) -> bool:
        return sp.is_subset(self._spans, _spans_of(other))

    def issuperset(self, other: Iterable[int]) -> bool:
        return sp.is_subset(_spans_of(other), self._spans)

    def isdisjoint(self, other: Iterable[int]) -> bool:
        return not sp.intersection(self._spans, _spans_of(other))

    __or__ = __ror__ = union  # type: ignore[assignment]
    __and__ = __rand__ = intersection
    __xor__ = __rxor__ = symmetric_difference  # type: ignore[assignment]
    __sub__ = difference

    def __rsub__(self, other: Iterable[int]) -> IntRanges:
        return self._wrap(sp.difference(_spans_of(other), self._spans))

    def __le__(self, other: Any) -> bool:
        return self.issubset(other) if isinstance(other, Set) else NotImplemented

    def __ge__(self, other: Any) -> bool:
        return self.issuperset(other) if isinstance(other, Set) else NotImplemented

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Set):
            return NotImplemented
        theirs = _spans_of(other)
        return sp.is_subset(self._spans, theirs) and sp.count(self._spans) < sp.count(theirs)

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, Set):
            return NotImplemented
        theirs = _spans_of(other)
        return sp.is_subset(theirs, self._spans) and sp.count(theirs) < sp.count(self._spans)


def _spans_of(values: Iterable[int]) -> sp.Spans:
    return values._spans if isinstance(values, IntRanges) else sp.from_ints(values)
