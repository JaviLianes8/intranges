"""Named range-string dialects and their documented sources."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Dialect:
    """The grammar used to read and write a range string.

    Attributes:
        name: Short label used in messages and by the CLI.
        range_sep: Separator between the two bounds of a range, ``"-"`` in ``"1-3"``.
        list_sep: Separator between tokens, ``","`` in ``"1-3,5"``.
        negatives: Accept a leading ``-`` on a bound as a sign.
        stride: Separator introducing a step, ``":"`` in ``"0-10:2"``, or ``None``.
        groups: Also accept the Linux kernel ``"a-b:used/group"`` form after ``stride``.
        open_end: Accept ``"5-"`` meaning "5 to ``upper``" (``upper`` must be given).
        suffix: Accept ``"-5"`` meaning "the last 5 values up to ``upper``" (HTTP style).
            Requires ``negatives=False`` so the leading ``-`` is unambiguous.
        clamp: Clip range ends above ``upper`` down to ``upper`` instead of raising.
        brackets: Accept the whole list wrapped in ``[...]`` (Slurm hostlist style).
        prefix: Optional leading unit such as ``"bytes="``; written back by ``compact``.
        last_alias: Token standing for ``upper``, such as the kernel's ``"N"``.
        all_alias: Token standing for ``lower..upper``, such as the kernel's ``"all"``.
        minimum: Smallest value the dialect allows, or ``None`` for no floor.
    """

    name: str = "default"
    range_sep: str = "-"
    list_sep: str = ","
    negatives: bool = True
    stride: str | None = None
    groups: bool = False
    open_end: bool = True
    suffix: bool = False
    clamp: bool = False
    brackets: bool = False
    prefix: str = ""
    last_alias: str | None = None
    all_alias: str | None = None
    minimum: int | None = None

    def __post_init__(self) -> None:
        if not self.range_sep:
            raise ValueError("range_sep must not be empty")
        if not self.list_sep:
            raise ValueError("list_sep must not be empty")
        seps = [self.range_sep, self.list_sep] + ([self.stride] if self.stride else [])
        if len(set(seps)) != len(seps):
            raise ValueError(f"separators must be distinct, got {seps!r}")
        for sep in seps:
            if any(ch.isdigit() or ch.isspace() for ch in sep):
                raise ValueError(f"separator {sep!r} must not contain digits or spaces")
        if self.stride == "":
            raise ValueError("stride must be None or a non-empty string")
        if self.groups and self.stride is None:
            raise ValueError("groups=True needs a stride separator")
        if self.suffix and self.negatives:
            raise ValueError("suffix ranges need negatives=False to stay unambiguous")
        for alias in (self.last_alias, self.all_alias):
            if alias is not None and (not alias.isalpha()):
                raise ValueError(f"alias {alias!r} must be alphabetic")

    def with_separators(self, range_sep: str | None, list_sep: str | None) -> Dialect:
        """Return a copy with the given separators replaced (``None`` keeps the current)."""
        return replace(
            self,
            range_sep=self.range_sep if range_sep is None else range_sep,
            list_sep=self.list_sep if list_sep is None else list_sep,
        )


DEFAULT = Dialect()
"""Signed integers, ``-`` ranges, ``,`` lists, open ends when ``upper`` is given."""

PAGES = Dialect(name="pages", negatives=False, open_end=False, minimum=1)
"""Printer page lists such as CUPS ``-o page-ranges=1-4,7,9-12``. Pages start at 1."""

CPULIST = Dialect(
    name="cpulist",
    negatives=False,
    stride=":",
    groups=True,
    open_end=False,
    last_alias="N",
    all_alias="all",
    minimum=0,
)
"""Linux cpu lists: ``0-3,8-11``, kernel ``100-2000:2/25``, taskset ``0-10:3``, ``16-N``."""

SLURM = Dialect(name="slurm", negatives=False, stride=":", open_end=False, brackets=True, minimum=0)
"""Slurm ``--array`` indexes such as ``0-15:4`` and hostlist numbers such as ``[1-3,5]``."""

HTTP = Dialect(
    name="http",
    negatives=False,
    open_end=True,
    suffix=True,
    clamp=True,
    prefix="bytes=",
    minimum=0,
)
"""RFC 9110 byte ranges: ``bytes=0-499,500-``, suffix ``-500``. ``upper`` is length - 1."""

DIALECTS: dict[str, Dialect] = {d.name: d for d in (DEFAULT, PAGES, CPULIST, SLURM, HTTP)}
"""Built-in dialects by name."""
