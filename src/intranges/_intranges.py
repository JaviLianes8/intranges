"""Set operations on immutable integer spans."""

from __future__ import annotations

from collections.abc import Iterable, Set

from . import _spans as sp
from ._base import _RangeBase
from ._dialect import DEFAULT, Dialect


class IntRanges(_RangeBase):
    """An immutable, lazy set of integers, stored as inclusive spans.

    >>> from intranges import IntRanges
    >>> r = IntRanges.parse("1-3,10-12")
    >>> r.count, str(r | [4]), 11 in r
    (6, '1-4,10-12', True)
    """

    __slots__ = ()

    def format(self, dialect: Dialect = DEFAULT, *, width: int | None = None) -> str:
        """Write the canonical range string; see :func:`compact` for the options.

        >>> from intranges import IntRanges
        >>> IntRanges([1, 2]).format(width=2)
        '01-02'
        """
        from ._compact import format_spans

        return format_spans(self._spans, dialect, width)

    def complement(self, lower: int, upper: int) -> IntRanges:
        """Values in ``lower..upper`` (inclusive) that are not in this set.

        >>> from intranges import IntRanges
        >>> str(IntRanges([2]).complement(1, 3))
        '1,3'
        """
        return self._wrap(sp.complement(self._spans, lower, upper))

    def union(self, *others: Iterable[int]) -> IntRanges:
        """Return the union with every iterable.

        >>> from intranges import IntRanges
        >>> str(IntRanges([1]).union([2], [5]))
        '1-2,5'
        """
        spans = self._spans
        for other in others:
            spans = sp.union(spans, _spans_of(other))
        return self._wrap(spans)

    def intersection(self, *others: Iterable[int]) -> IntRanges:
        """Return values common to every iterable.

        >>> from intranges import IntRanges
        >>> str(IntRanges([1, 2]).intersection([2, 3]))
        '2'
        """
        spans = self._spans
        for other in others:
            spans = sp.intersection(spans, _spans_of(other))
        return self._wrap(spans)

    def difference(self, *others: Iterable[int]) -> IntRanges:
        """Return values absent from every iterable.

        >>> from intranges import IntRanges
        >>> str(IntRanges([1, 2]).difference([2]))
        '1'
        """
        spans = self._spans
        for other in others:
            spans = sp.difference(spans, _spans_of(other))
        return self._wrap(spans)

    def symmetric_difference(self, other: Iterable[int]) -> IntRanges:
        """Return values occurring on exactly one side.

        >>> from intranges import IntRanges
        >>> str(IntRanges([1, 2]).symmetric_difference([2, 3]))
        '1,3'
        """
        theirs = _spans_of(other)
        mine = self._spans
        return self._wrap(sp.union(sp.difference(mine, theirs), sp.difference(theirs, mine)))

    def issubset(self, other: Iterable[int]) -> bool:
        """Whether every value is in the other iterable.

        >>> from intranges import IntRanges
        >>> IntRanges([1]).issubset([1, 2])
        True
        """
        return sp.is_subset(self._spans, _spans_of(other))

    def issuperset(self, other: Iterable[int]) -> bool:
        """Whether every other value is in this set.

        >>> from intranges import IntRanges
        >>> IntRanges([1, 2]).issuperset([1])
        True
        """
        return sp.is_subset(_spans_of(other), self._spans)

    def isdisjoint(self, other: Iterable[int]) -> bool:
        """Whether the two sets have no common value.

        >>> from intranges import IntRanges
        >>> IntRanges([1]).isdisjoint([2])
        True
        """
        return not sp.intersection(self._spans, _spans_of(other))

    __or__ = __ror__ = union  # type: ignore[assignment]
    __and__ = __rand__ = intersection
    __xor__ = __rxor__ = symmetric_difference  # type: ignore[assignment]
    __sub__ = difference

    def __rsub__(self, other: Iterable[int]) -> IntRanges:
        return self._wrap(sp.difference(_spans_of(other), self._spans))

    def __le__(self, other: Set[int]) -> bool:
        return self.issubset(other) if isinstance(other, Set) else NotImplemented

    def __ge__(self, other: Set[int]) -> bool:
        return self.issuperset(other) if isinstance(other, Set) else NotImplemented

    def __lt__(self, other: Set[int]) -> bool:
        if not isinstance(other, Set):
            return NotImplemented
        theirs = _spans_of(other)
        return sp.is_subset(self._spans, theirs) and sp.count(self._spans) < sp.count(theirs)

    def __gt__(self, other: Set[int]) -> bool:
        if not isinstance(other, Set):
            return NotImplemented
        theirs = _spans_of(other)
        return sp.is_subset(theirs, self._spans) and sp.count(theirs) < sp.count(self._spans)


def _spans_of(values: Iterable[int]) -> sp.Spans:
    return values._spans if isinstance(values, IntRanges) else sp.from_ints(values)
