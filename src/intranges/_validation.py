"""Bound resource options and keep conversion errors independent of input text."""

from __future__ import annotations

from operator import index


def limit(value: int | None, name: str) -> int | None:
    if value is None:
        return None
    try:
        value = index(value)
    except TypeError:
        raise TypeError(f"{name} must be an integer or None") from None
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


def bounds(lower: int | None, upper: int | None) -> tuple[int | None, int | None]:
    try:
        lower = None if lower is None else index(lower)
        upper = None if upper is None else index(upper)
    except TypeError:
        raise TypeError("bounds must be integers or None") from None
    if lower is not None and upper is not None and lower > upper:
        raise ValueError("lower is greater than upper")
    return lower, upper


def decimal(raw: str) -> int:
    if len(raw.lstrip("-+")) > 600:
        raise ValueError("integer exceeds 600 digits")
    try:
        return int(raw)
    except ValueError:
        raise ValueError("not an integer") from None
