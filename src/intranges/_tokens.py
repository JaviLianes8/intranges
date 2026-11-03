"""Split a range string into validated pieces, one per token, without expanding them."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from functools import lru_cache
from typing import NamedTuple, NoReturn

from ._dialect import Dialect
from ._errors import DescendingRangeError, RangeBoundsError, RangeError, RangeSyntaxError
from ._validation import bounds, decimal


class Piece(NamedTuple):
    """One token: groups of ``used`` values every ``step`` from ``start`` up to ``end``."""

    token: str
    offset: int
    start: int
    end: int
    step: int = 1
    used: int = 1

    def size(self) -> int:
        if self.step == 1:
            return self.end - self.start + 1
        full, rest = divmod(self.end - self.start + 1, self.step)
        return full * self.used + min(rest, self.used)

    def span_count(self) -> int:
        return 1 if self.step == 1 else (self.end - self.start) // self.step + 1

    def last(self) -> int:
        if self.step == 1:
            return self.end
        first_of_last = self.start + (self.end - self.start) // self.step * self.step
        return min(first_of_last + self.used - 1, self.end)

    def spans(self) -> Iterator[tuple[int, int]]:
        if self.step == 1:
            yield (self.start, self.end)
            return
        for low in range(self.start, self.end + 1, self.step):
            yield (low, min(low + self.used - 1, self.end))


@lru_cache(maxsize=128)
def _pattern(dialect: Dialect) -> re.Pattern[str]:
    num = r"-?\d+" if dialect.negatives else r"\d+"
    if dialect.last_alias:
        num = rf"(?:{num}|{re.escape(dialect.last_alias)})"
    stride = ""
    if dialect.stride:
        stride = rf"(?:\s*{re.escape(dialect.stride)}\s*(?P<step>\d+)(?:\s*/\s*(?P<grp>\d+))?)?"
    sep = re.escape(dialect.range_sep)
    return re.compile(rf"(?P<lo>{num})?(?:\s*(?P<sep>{sep})\s*(?P<hi>{num})?)?{stride}")


def _strip_frame(text: str, dialect: Dialect) -> tuple[str, int]:
    """Drop an optional unit prefix and enclosing brackets, returning body and offset."""
    body, base = text, 0
    lead = len(body) - len(body.lstrip())
    if dialect.prefix and body[lead:].lower().startswith(dialect.prefix.lower()):
        base = lead + len(dialect.prefix)
        body = text[base:]
    if dialect.brackets:
        inner = body.strip()
        if inner.startswith("[") and inner.endswith("]"):
            base += body.index("[") + 1
            body = inner[1:-1]
    return body, base


def _chunks(body: str, base: int, sep: str) -> Iterator[tuple[str, int]]:
    pos = 0
    while True:
        cut = body.find(sep, pos)
        chunk = body[pos:] if cut < 0 else body[pos:cut]
        yield chunk.strip(), base + pos + len(chunk) - len(chunk.lstrip())
        if cut < 0:
            return
        pos = cut + len(sep)


def scan(text: str, dialect: Dialect, lower: int | None, upper: int | None) -> list[Piece]:
    """Return one validated :class:`Piece` per token of ``text``, in input order."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    lower, upper = bounds(lower, upper)
    body, base = _strip_frame(text, dialect)
    if not body.strip():
        return []
    return [
        _read(token, offset, text, dialect, lower, upper)
        for token, offset in _chunks(body, base, dialect.list_sep)
    ]


Fail = Callable[[type[RangeError], str], NoReturn]


def _read(
    token: str, offset: int, text: str, d: Dialect, lower: int | None, upper: int | None
) -> Piece:
    def fail(kind: type[RangeError], message: str) -> NoReturn:
        raise kind(message, text=text, token=token, offset=offset)

    if not token:
        fail(RangeSyntaxError, "empty range token")
    if any(len(part) > 600 for part in re.findall(r"\d+", token)):
        fail(RangeSyntaxError, "integer exceeds 600 digits")
    floor = _floor(lower, d.minimum)
    if d.all_alias and token.lower() == d.all_alias.lower():
        if floor is None or upper is None:
            fail(RangeBoundsError, "alias needs lower and upper bounds")
        if floor > upper:
            fail(RangeBoundsError, "alias is empty: lower exceeds upper")
        return Piece(token, offset, floor, upper)
    match = _pattern(d).fullmatch(token)
    if match is None or (match["lo"] is None and match["sep"] is None):
        fail(RangeSyntaxError, "invalid range token")

    def value(raw: str) -> int:
        if raw == d.last_alias:
            if upper is None:
                fail(RangeBoundsError, "alias needs an upper bound")
            return upper
        return decimal(raw)

    lo, hi = match["lo"], match["hi"]
    step = decimal(match["step"]) if d.stride and match["step"] else None
    if match["sep"] is None:
        if step is not None:
            fail(RangeSyntaxError, "a stride needs a range")
        start = end = value(lo)
    elif lo is None:
        if not d.suffix or upper is None:
            hint = "needs an upper bound" if d.suffix else "is not allowed"
            fail(RangeSyntaxError, f"suffix range {hint}")
        if hi is None or not hi.isdigit() or decimal(hi) == 0:
            fail(RangeSyntaxError, "suffix range needs a positive length")
        start, end = upper - decimal(hi) + 1, upper
        if d.clamp and d.minimum is not None:
            start = max(start, d.minimum)
        if start > end:
            fail(RangeBoundsError, "suffix range is unsatisfiable")
    elif hi is None:
        if not d.open_end:
            fail(RangeSyntaxError, "open-ended range is not allowed")
        if upper is None:
            fail(RangeBoundsError, "open-ended range needs an upper bound")
        start, end = value(lo), upper
        if start > end:
            fail(RangeBoundsError, "start is above the upper bound")
    else:
        start, end = value(lo), value(hi)
    if end < start:
        fail(DescendingRangeError, "descending range")
    if d.clamp and upper is not None and start <= upper < end:
        end = upper
    piece = Piece(token, offset, start, end, *_stride(step, match.groupdict().get("grp"), d, fail))
    if floor is not None and piece.start < floor:
        fail(RangeBoundsError, "value is below the lower bound")
    if upper is not None and piece.last() > upper:
        fail(RangeBoundsError, "value is above the upper bound")
    return piece


def _floor(lower: int | None, minimum: int | None) -> int | None:
    if lower is None or minimum is None:
        return minimum if lower is None else lower
    return max(lower, minimum)


def _stride(step: int | None, grp: str | None, d: Dialect, fail: Fail) -> tuple[int, int]:
    if step is None:
        return 1, 1
    if grp is not None and not d.groups:
        fail(RangeSyntaxError, "used/group strides are not allowed")
    used, size = (1, step) if grp is None else (step, decimal(grp))
    if size == 0 or used == 0 or used > size:
        fail(RangeSyntaxError, "stride must satisfy 0 < used <= group")
    return (1, 1) if used == size else (size, used)
