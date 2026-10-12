"""Read range strings into lists, lazy sets, counts and canonical strings."""

from __future__ import annotations

from typing import Literal

from . import _spans as sp
from ._dialect import DEFAULT, Dialect
from ._errors import RangeError, RangeOrderError, RangeOverlapError, RangeSizeError
from ._intranges import IntRanges
from ._tokens import Piece, scan

DEFAULT_MAX_SIZE = 10_000_000
"""Default cap on the number of values :func:`parse` will put in a list."""

DEFAULT_MAX_SPANS = 1_000_000
"""Default cap on the number of separate spans a strided input may create."""

OverlapPolicy = Literal["merge", "reject"]
OrderPolicy = Literal["allow", "reject"]


def _fail(kind: type[RangeError], message: str, text: str, piece: Piece) -> RangeError:
    return kind(message, text=text, token=piece.token, offset=piece.offset)


def parse(
    text: str,
    *,
    range_sep: str | None = None,
    list_sep: str | None = None,
    dialect: Dialect = DEFAULT,
    lower: int | None = None,
    upper: int | None = None,
    max_size: int | None = DEFAULT_MAX_SIZE,
) -> list[int]:
    """Expand a range string such as ``"1-5,8,10-12"`` into a list of ints.

    Values come out in input order and repeats are kept, so ``parse("3,1-2,2")`` is
    ``[3, 1, 2, 2]``. Use :func:`parse_ranges` for set semantics without expansion.
    Whitespace around tokens and separators is ignored. An empty string gives ``[]``.

    Args:
        text: The range string.
        range_sep: Overrides ``dialect.range_sep`` (default ``"-"``).
        list_sep: Overrides ``dialect.list_sep`` (default ``","``).
        dialect: Grammar to read, such as ``CPULIST`` or ``HTTP``.
        lower: Smallest allowed value; also the start of an ``all`` alias.
        upper: Largest allowed value; also the end of ``"5-"``, ``"-5"`` and ``N``.
        max_size: Refuse to build more values than this (checked before allocating);
            ``None`` lifts the cap.

    Raises:
        RangeSyntaxError: A token does not match the dialect grammar.
        DescendingRangeError: A range runs high to low, such as ``"5-1"``.
        RangeBoundsError: A value is outside ``lower``/``upper`` or the dialect minimum.
        RangeSizeError: The expansion would exceed ``max_size``.
        ValueError: The separators are empty or clash, or ``lower > upper``.

    >>> parse("1-3,7")
    [1, 2, 3, 7]
    >>> parse("0-10:3", dialect=CPULIST)
    [0, 3, 6, 9]
    """
    chosen = dialect.with_separators(range_sep, list_sep)
    pieces = scan(text, chosen, lower, upper)
    total = 0
    for piece in pieces:
        total += piece.size()
        if max_size is not None and total > max_size:
            raise _fail(RangeSizeError, f"expansion exceeds max_size={max_size}", text, piece)
    result: list[int] = []
    for piece in pieces:
        for low, high in piece.spans():
            result.extend(range(low, high + 1))
    return result


def parse_ranges(
    text: str,
    *,
    range_sep: str | None = None,
    list_sep: str | None = None,
    dialect: Dialect = DEFAULT,
    lower: int | None = None,
    upper: int | None = None,
    on_overlap: OverlapPolicy = "merge",
    on_unsorted: OrderPolicy = "allow",
    max_spans: int | None = DEFAULT_MAX_SPANS,
) -> IntRanges:
    """Read a range string into a lazy :class:`IntRanges` without expanding it.

    ``parse_ranges("0-10000000000")`` costs two integers. Overlapping, repeated and
    unsorted tokens are merged by default.

    Args:
        on_overlap: ``"merge"`` unions overlapping or repeated tokens; ``"reject"``
            raises :class:`RangeOverlapError` naming the later of the two tokens.
        on_unsorted: ``"allow"`` accepts tokens in any order; ``"reject"`` raises
            :class:`RangeOrderError` when a token starts below the previous token.
        max_spans: Cap on separate spans created by strides such as ``"0-10:2"``;
            ``None`` lifts it.
        Other options are those of :func:`parse`.

    >>> parse_ranges("5,1-3,2").spans
    ((1, 3), (5, 5))
    """
    if on_overlap not in ("merge", "reject"):
        raise ValueError(f"on_overlap must be 'merge' or 'reject', got {on_overlap!r}")
    if on_unsorted not in ("allow", "reject"):
        raise ValueError(f"on_unsorted must be 'allow' or 'reject', got {on_unsorted!r}")
    chosen = dialect.with_separators(range_sep, list_sep)
    pieces = scan(text, chosen, lower, upper)
    total = 0
    for index, piece in enumerate(pieces):
        total += piece.span_count()
        if max_spans is not None and total > max_spans:
            raise _fail(RangeSizeError, f"input exceeds max_spans={max_spans}", text, piece)
        if on_unsorted == "reject" and index and piece.start < pieces[index - 1].start:
            raise _fail(RangeOrderError, "token starts below the previous token", text, piece)
    tagged = sorted(
        (low, high, index) for index, piece in enumerate(pieces) for low, high in piece.spans()
    )
    if on_overlap == "reject":
        _reject_overlaps(tagged, pieces, text)
    return IntRanges._wrap(sp.coalesce((low, high) for low, high, _ in tagged))


def _reject_overlaps(tagged: list[tuple[int, int, int]], pieces: list[Piece], text: str) -> None:
    reach, owner = None, -1
    for low, high, index in tagged:
        if reach is not None and low <= reach:
            later = pieces[max(index, owner)]
            raise _fail(RangeOverlapError, "token overlaps an earlier token", text, later)
        if reach is None or high > reach:
            reach, owner = high, index


def count(
    text: str,
    *,
    range_sep: str | None = None,
    list_sep: str | None = None,
    dialect: Dialect = DEFAULT,
    lower: int | None = None,
    upper: int | None = None,
    max_spans: int | None = DEFAULT_MAX_SPANS,
) -> int:
    """Number of distinct values in a range string, computed without expanding it.

    Options are those of :func:`parse_ranges`.

    >>> count("1-1000000,500000-2000000")
    2000000
    """
    return parse_ranges(
        text,
        range_sep=range_sep,
        list_sep=list_sep,
        dialect=dialect,
        lower=lower,
        upper=upper,
        max_spans=max_spans,
    ).count


def normalize(
    text: str,
    *,
    range_sep: str | None = None,
    list_sep: str | None = None,
    dialect: Dialect = DEFAULT,
    lower: int | None = None,
    upper: int | None = None,
    output: Dialect | None = None,
    width: int | None = None,
) -> str:
    """Rewrite a range string in canonical form: sorted, merged, minimal.

    ``output`` picks the dialect to write (default: the input dialect with the given
    separators) and ``width`` zero-pads numbers. Other options are those of
    :func:`parse_ranges`.

    >>> normalize("8, 1-3, 2, 4")
    '1-4,8'
    """
    chosen = dialect.with_separators(range_sep, list_sep)
    ranges = parse_ranges(text, dialect=chosen, lower=lower, upper=upper)
    return ranges.format(output if output is not None else chosen, width=width)
