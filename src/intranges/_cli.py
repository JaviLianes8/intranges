"""Command-line interface: ``intranges <command> ...``."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable, Sequence
from itertools import islice
from typing import NoReturn

from . import __version__
from ._compact import compact
from ._dialect import DIALECTS, Dialect
from ._errors import RangeError
from ._intranges import IntRanges
from ._parse import DEFAULT_MAX_SIZE, parse, parse_ranges

EXAMPLES = """\
examples:
  intranges expand "1-3,7"                        # 1 2 3 7, one per line
  intranges expand "0-10:3" --dialect cpulist -d ,  # 0,3,6,9
  seq 1 5 | intranges compress                    # 1-5
  intranges compress 6 5 1 3 2                    # 1-3,5-6
  intranges normalize "8, 1-3, 2, 4"              # 1-4,8
  intranges count "0-10000000000"                 # 10000000001
  intranges contains "0-3,8-11" 9 12              # 9 yes / 12 no, exit 2
  intranges complement "0-3,8-11" --lower 0 --upper 15   # 4-7,12-15
  intranges expand "900-" --dialect http --upper 999 -d ,
  intranges expand -- "-3--1"                     # put -- before a text that starts with -

exit codes: 0 success, 1 error (message on stderr), 2 a "contains" value is absent.
"""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: error: {message}\n")


def _common(sub: argparse.ArgumentParser, text: bool = True) -> None:
    if text:
        sub.add_argument("text", help='range string, or "-" to read it from stdin')
    sub.add_argument("--dialect", choices=sorted(DIALECTS), default="default")
    sub.add_argument("--lower", type=int, help="smallest allowed value")
    sub.add_argument("--upper", type=int, help='largest allowed value; end of "5-" and N')
    sub.add_argument("--range-sep", help="override the range separator")
    sub.add_argument("--list-sep", help="override the list separator")


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser used by :func:`main`."""
    parser = _Parser(
        prog="intranges",
        description="Expand, compress and query integer range strings like 1-3,5,7-9.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subs = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    sub = subs.add_parser("expand", help="print every value of a range string")
    _common(sub)
    sub.add_argument("-d", "--delimiter", default="\n", help="output separator (newline)")
    sub.add_argument("--unique", action="store_true", help="sorted, without repeats")
    sub.add_argument("--max-size", type=int, default=DEFAULT_MAX_SIZE, help="value cap")
    sub = subs.add_parser("compress", help="turn integers into a canonical range string")
    _common(sub, text=False)
    sub.add_argument("values", nargs="*", help="integers; read from stdin when omitted")
    sub.add_argument("--width", type=int, help="zero-pad numbers to this width")
    sub = subs.add_parser("normalize", aliases=["normalise"], help="canonical form")
    _common(sub)
    sub.add_argument("--to", choices=sorted(DIALECTS), help="output dialect")
    sub.add_argument("--width", type=int, help="zero-pad numbers to this width")
    sub = subs.add_parser("count", help="number of distinct values")
    _common(sub)
    sub = subs.add_parser("contains", help="test membership; exit 2 if any is absent")
    _common(sub)
    sub.add_argument("values", nargs="+", type=int, help="integers to test")
    sub = subs.add_parser("complement", help="values within --lower..--upper not listed")
    _common(sub)
    return parser


def _dialect(args: argparse.Namespace) -> Dialect:
    return DIALECTS[args.dialect].with_separators(args.range_sep, args.list_sep)


def _text(args: argparse.Namespace) -> str:
    return sys.stdin.read().strip() if args.text == "-" else str(args.text)


def _ranges(args: argparse.Namespace) -> IntRanges:
    return parse_ranges(_text(args), dialect=_dialect(args), lower=args.lower, upper=args.upper)


def _emit(values: Iterable[int], delimiter: str) -> None:
    """Stream values in chunks so a large expansion never builds one huge string."""
    stream = iter(values)
    lead = ""
    while chunk := list(islice(stream, 4096)):
        sys.stdout.write(lead + delimiter.join(map(str, chunk)))
        lead = delimiter
    sys.stdout.write("\n")


def _run(args: argparse.Namespace) -> int:
    out = sys.stdout
    if args.command == "expand":
        if args.unique:
            ranges = _ranges(args)
            if args.max_size is not None and ranges.count > args.max_size:
                raise RangeError(f"expansion exceeds max_size={args.max_size}")
            values: Sequence[int] | IntRanges = ranges
        else:
            values = parse(
                _text(args),
                dialect=_dialect(args),
                lower=args.lower,
                upper=args.upper,
                max_size=args.max_size,
            )
        out.write(args.delimiter.join(map(str, values)) + "\n")
    elif args.command == "compress":
        raw = args.values or [t for t in re.split(r"[\s,]+", sys.stdin.read()) if t]
        try:
            ints = [int(token) for token in raw]
        except ValueError as exc:
            raise ValueError(f"not an integer: {exc}") from None
        out.write(compact(ints, dialect=_dialect(args), width=args.width) + "\n")
    elif args.command in ("normalize", "normalise"):
        target = DIALECTS[args.to] if args.to else _dialect(args)
        out.write(_ranges(args).format(target, width=args.width) + "\n")
    elif args.command == "count":
        out.write(f"{_ranges(args).count}\n")
    elif args.command == "contains":
        ranges = _ranges(args)
        found = [value in ranges for value in args.values]
        for value, hit in zip(args.values, found, strict=True):
            out.write(f"{value} {'yes' if hit else 'no'}\n")
        return 0 if all(found) else 2
    else:
        if args.lower is None or args.upper is None:
            raise ValueError("complement needs --lower and --upper")
        complement = _ranges(args).complement(args.lower, args.upper)
        out.write(complement.format(_dialect(args)) + "\n")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return its exit code."""
    args = build_parser().parse_args(argv)
    try:
        return _run(args)
    except RangeError as exc:
        print(f"intranges: error: {exc}", file=sys.stderr)
        if exc.pointer():
            print(exc.pointer(), file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"intranges: error: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
