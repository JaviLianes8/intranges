"""Error types raised by intranges.

Every error is a :class:`RangeError`, which is itself a :class:`ValueError`, so existing
``except ValueError`` handlers keep working. Errors raised while reading a string carry
the full ``text``, the offending ``token`` and its character ``offset`` in ``text``.
"""

from __future__ import annotations


class RangeError(ValueError):
    """Raised when a range string or a set of integers cannot be handled.

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
        """
        if self.text is None or self.offset is None:
            return ""
        width = max(1, len(self.token or ""))
        return f"{self.text}\n{' ' * self.offset}{'^' * width}"


class RangeSyntaxError(RangeError):
    """A token does not match the grammar of the active dialect."""


class DescendingRangeError(RangeError):
    """A range runs from high to low, such as ``"5-1"``."""


class RangeOverlapError(RangeError):
    """A token overlaps or repeats an earlier one while ``on_overlap="reject"``."""


class RangeOrderError(RangeError):
    """A token starts below an earlier one while ``on_unsorted="reject"``."""


class RangeBoundsError(RangeError):
    """A value falls outside ``lower``/``upper`` or the dialect minimum."""


class RangeSizeError(RangeError):
    """Expanding the input would exceed ``max_size`` values or ``max_spans`` spans."""
