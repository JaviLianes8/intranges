"""Error types raised by intranges.

Range-string errors are :class:`RangeError` subclasses of :class:`ValueError`, so existing
``except ValueError`` handlers keep working. Errors raised while reading a string carry
the full ``text``, the offending ``token`` and its character ``offset`` in ``text``.
"""

from __future__ import annotations


class RangeError(ValueError):
    """Raised when a range string or a set of integers cannot be handled.

    >>> from intranges import RangeError
    >>> error = RangeError("invalid range token", text="1,x", token="x", offset=2)
    >>> str(error)
    'invalid range token at offset 2'

    Attributes:
        text: The full input string, when the error came from parsing.
        token: The offending token, stripped of surrounding whitespace.
        offset: Zero-based index of ``token`` inside ``text``.
    """

    def __init__(
        self,
        message: str,
        *,
        text: str | None = None,
        token: str | None = None,
        offset: int | None = None,
    ) -> None:
        if offset is not None:
            message = f"{message} at offset {offset}"
        super().__init__(message)
        self.text = text
        self.token = token
        self.offset = offset

    def pointer(self) -> str:
        """Return ``text`` with a caret line under the offending token.

        Returns an empty string when the error does not point into a string.
        This explicit diagnostic includes input text: do not log it for secret input.
        At most 160 input characters and 160 carets are returned.

        >>> RangeError("bad", text="1,x", token="x", offset=2).pointer()
        '1,x\\n  ^'

        """
        if self.text is None or self.offset is None:
            return ""
        offset = min(max(0, self.offset), len(self.text))
        start = max(0, offset - 40) if len(self.text) > 160 else 0
        excerpt = self.text[start : start + 160]
        width = min(160, max(1, len(self.token or "")))
        return f"{excerpt}\n{' ' * (offset - start)}{'^' * width}"


class RangeSyntaxError(RangeError):
    """A token does not match the grammar of the active dialect.

    >>> from intranges import RangeSyntaxError
    >>> str(RangeSyntaxError("invalid input"))
    'invalid input'
    """


class DescendingRangeError(RangeError):
    """A range runs from high to low, such as ``"5-1"``.

    >>> from intranges import DescendingRangeError
    >>> str(DescendingRangeError("invalid input"))
    'invalid input'
    """


class RangeOverlapError(RangeError):
    """A token overlaps or repeats an earlier one while ``on_overlap="reject"``.

    >>> from intranges import RangeOverlapError
    >>> str(RangeOverlapError("invalid input"))
    'invalid input'
    """


class RangeOrderError(RangeError):
    """A token starts below an earlier one while ``on_unsorted="reject"``.

    >>> from intranges import RangeOrderError
    >>> str(RangeOrderError("invalid input"))
    'invalid input'
    """


class RangeBoundsError(RangeError):
    """A value falls outside ``lower``/``upper`` or the dialect minimum.

    >>> from intranges import RangeBoundsError
    >>> str(RangeBoundsError("invalid input"))
    'invalid input'
    """


class RangeSizeError(RangeError):
    """Expanding the input would exceed ``max_size`` values or ``max_spans`` spans.

    >>> from intranges import RangeSizeError
    >>> str(RangeSizeError("invalid input"))
    'invalid input'
    """
