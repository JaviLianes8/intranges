"""A lazy, immutable set of integers stored as spans."""

from __future__ import annotations

from bisect import bisect_right
from collections.abc import Callable, Iterable, Iterator, Set
from operator import index
from typing import Literal, TypeVar

from . import _spans as sp
from ._dialect import DEFAULT, Dialect

_T = TypeVar("_T", bound="_RangeBase")


class _RangeBase(Set[int]):
    """An immutable set of integers that never expands its ranges.

    >>> from intranges import IntRanges
    >>> r = IntRanges.parse("1-3,10-12")
    >>> 11 in r, r.count, str(r | IntRanges([4]))
    (True, 6, '1-4,10-12')
    """

    __slots__ = ("_spans",)
    _spans: sp.Spans

    def __init__(self, values: Iterable[int] = ()) -> None:
        """Build from any iterable of ints; a ``range`` with step 1 is not expanded."""
        if isinstance(values, _RangeBase):
            self._spans = values._spans
        else:
            self._spans = sp.from_ints(values)

    def __setattr__(self, name: str, value: object) -> None:
        if name == "_spans" and hasattr(self, "_spans"):
            raise AttributeError("IntRanges is immutable")
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        raise AttributeError("IntRanges is immutable")

    @classmethod
    def from_spans(cls: type[_T], spans: Iterable[tuple[int, int]]) -> _T:
        """Build from inclusive ``(low, high)`` pairs in any order, overlapping or not.

        Raises :class:`ValueError` when a pair has ``low > high`` and :class:`TypeError`
        when a bound is not an integer.


        >>> from intranges import IntRanges
        >>> IntRanges.from_spans([(3, 4), (1, 2)]).spans
        ((1, 4),)
        """
        pairs = [(index(low), index(high)) for low, high in spans]
        for low, high in pairs:
            if low > high:
                raise ValueError("span has low greater than high")
        return cls._wrap(sp.coalesce(pairs))

    @classmethod
    def parse(
        cls: type[_T],
        text: str,
        *,
        range_sep: str | None = None,
        list_sep: str | None = None,
        dialect: Dialect = DEFAULT,
        lower: int | None = None,
        upper: int | None = None,
        on_overlap: Literal["merge", "reject"] = "merge",
        on_unsorted: Literal["allow", "reject"] = "allow",
        max_spans: int | None = 1_000_000,
    ) -> _T:
        """Read a range string with the options of :func:`parse_ranges`.

        >>> from intranges import IntRanges
        >>> IntRanges.parse("1-2").spans
        ((1, 2),)
        """
        from ._parse import parse_ranges

        return cls._wrap(
            parse_ranges(
                text,
                range_sep=range_sep,
                list_sep=list_sep,
                dialect=dialect,
                lower=lower,
                upper=upper,
                on_overlap=on_overlap,
                on_unsorted=on_unsorted,
                max_spans=max_spans,
            ).spans
        )

    @classmethod
    def _wrap(cls: type[_T], spans: sp.Spans) -> _T:
        obj = cls.__new__(cls)
        obj._spans = spans
        return obj

    @property
    def spans(self) -> tuple[tuple[int, int], ...]:
        """The canonical inclusive ``(low, high)`` spans, ascending and non-adjacent.

        >>> from intranges import IntRanges
        >>> IntRanges([1, 3]).spans
        ((1, 1), (3, 3))
        """
        return self._spans

    @property
    def count(self) -> int:
        """Number of values, as an unbounded int.

        >>> from intranges import IntRanges
        >>> IntRanges(range(10**20)).count
        100000000000000000000
        """
        return sp.count(self._spans)

    @property
    def first(self) -> int:
        """Smallest value. Raises :class:`ValueError` when empty.

        >>> from intranges import IntRanges
        >>> IntRanges([3, 1]).first
        1
        """
        if not self._spans:
            raise ValueError("first of an empty IntRanges")
        return self._spans[0][0]

    @property
    def last(self) -> int:
        """Largest value. Raises :class:`ValueError` when empty.

        >>> from intranges import IntRanges
        >>> IntRanges([3, 1]).last
        3
        """
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
        return hash((_RangeBase, self._spans))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _RangeBase):
            return self._spans == other._spans
        return NotImplemented

    def __repr__(self) -> str:
        return f"IntRanges({self.format()!r})"

    def format(self, dialect: Dialect = DEFAULT, *, width: int | None = None) -> str:
        from ._compact import format_spans

        return format_spans(self._spans, dialect, width)

    def __str__(self) -> str:
        return self.format()

    def __reduce__(
        self,
    ) -> tuple[Callable[[Iterable[tuple[int, int]]], _RangeBase], tuple[sp.Spans]]:
        return (type(self).from_spans, (self._spans,))
