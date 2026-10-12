"""The public contract: every exported name and the full promise it makes."""

import doctest
import importlib
import importlib.resources
import pickle
from collections.abc import Callable
from collections.abc import Set as AbstractSet

import pytest

import intranges as ir


def _parse() -> None:
    assert ir.parse("1-5,8,10-12") == [1, 2, 3, 4, 5, 8, 10, 11, 12]
    assert ir.parse("3,1-2,2") == [3, 1, 2, 2]
    assert ir.parse(" -3 - -1 , 0 ") == [-3, -2, -1, 0]
    assert ir.parse("") == [] and ir.parse("  ") == []
    assert ir.parse("1..3;6", range_sep="..", list_sep=";") == [1, 2, 3, 6]
    assert ir.parse("5-", upper=6) == [5, 6]
    for bad, kind in (("5-1", ir.DescendingRangeError), ("x", ir.RangeSyntaxError)):
        with pytest.raises(kind):
            ir.parse(bad)
    with pytest.raises(ir.RangeSizeError):
        ir.parse("0-99999999999")
    assert ir.parse("1-3", max_size=None) == [1, 2, 3]
    with pytest.raises(ir.RangeBoundsError):
        ir.parse("1-5", lower=2)
    with pytest.raises(ir.RangeBoundsError):
        ir.parse("1-5", upper=4)
    with pytest.raises(ValueError):
        ir.parse("1", lower=3, upper=2)
    with pytest.raises(ValueError):
        ir.parse("1", range_sep="")


def _compact() -> None:
    assert ir.compact([6, 5, 1, 1, 3, 2]) == "1-3,5-6"
    assert ir.compact([]) == ""
    assert ir.compact([-3, -2, 0]) == "-3--2,0"
    assert ir.compact(range(10**15)) == "0-999999999999999"
    assert ir.compact(ir.IntRanges([1, 3])) == "1,3"
    assert ir.compact([1, 2, 3, 6], range_sep="..", list_sep=";") == "1..3;6"
    assert ir.compact([1, 2], width=3) == "001-002"
    assert ir.compact([1, 2], dialect=ir.HTTP) == "bytes=1-2"
    with pytest.raises(TypeError):
        ir.compact([1.5])  # type: ignore[list-item]
    with pytest.raises(ir.RangeBoundsError):
        ir.compact([-1], dialect=ir.CPULIST)


def _parse_ranges() -> None:
    r = ir.parse_ranges("9,1-5,3")
    assert isinstance(r, ir.IntRanges) and r.spans == ((1, 5), (9, 9))
    assert ir.parse_ranges("0-10000000000").count == 10_000_000_001
    with pytest.raises(ir.RangeOverlapError):
        ir.parse_ranges("1-5,3", on_overlap="reject")
    with pytest.raises(ir.RangeOrderError):
        ir.parse_ranges("5,1", on_unsorted="reject")
    with pytest.raises(ir.RangeSizeError):
        ir.parse_ranges("0-10:2", dialect=ir.SLURM, max_spans=3)


def _count() -> None:
    assert ir.count("1-5,3-9") == 9
    assert ir.count("0-15:4", dialect=ir.SLURM) == 4


def _normalize() -> None:
    assert ir.normalize("8, 1-3, 2, 4") == "1-4,8"
    assert ir.normalize("1-3", output=ir.HTTP) == "bytes=1-3"
    assert ir.normalize("3;1", list_sep=";") == "1;3"
    assert ir.normalize("[1-2]", dialect=ir.SLURM, width=2) == "01-02"


def _int_ranges() -> None:
    r = ir.IntRanges.parse("1-3,10-12")
    assert isinstance(r, AbstractSet)
    assert 11 in r and 4 not in r and r.count == len(r) == 6
    assert list(r) == [1, 2, 3, 10, 11, 12] and (r.first, r.last) == (1, 12)
    assert str(r | [4]) == "1-4,10-12" and str(r.complement(0, 13)) == "0,4-9,13"
    assert ir.IntRanges.from_spans([(1, 3), (10, 12)]) == r
    other = ir.IntRanges.parse("2-11")
    assert str(r & other) == "2-3,10-11" and str(r - other) == "1,12"
    assert str(r ^ other) == "1,4-9,12" and str({0} | r) == "0-3,10-12"
    assert str({1, 5} - r) == "5" and str({1, 5} & r) == "1" and str({1, 5} ^ r) == "2-3,5,10-12"
    assert ir.IntRanges([2]) < r and r > ir.IntRanges([2]) and r >= r and not r < r
    assert hash(r) == hash(ir.IntRanges(list(r))) and r != frozenset(r)
    assert pickle.loads(pickle.dumps(r)) == r
    assert list(reversed(r)) == [12, 11, 10, 3, 2, 1]
    assert r.format(width=2) == "01-03,10-12" and repr(r) == "IntRanges('1-3,10-12')"
    assert True in r and "1" not in r and 1.0 not in r
    for prop in ("first", "last"):
        with pytest.raises(ValueError):
            getattr(ir.IntRanges(), prop)
    with pytest.raises(ValueError):
        ir.IntRanges.from_spans([(2, 1)])
    with pytest.raises(ValueError):
        r.complement(2, 1)


def _dialect() -> None:
    d = ir.Dialect(name="x", range_sep="..", list_sep=";")
    assert ir.parse("1..2;5", dialect=d) == [1, 2, 5]
    with pytest.raises(ValueError):
        ir.Dialect(range_sep="")


def _presets() -> None:
    assert ir.parse("1-2", dialect=ir.DEFAULT) == [1, 2]
    assert ir.parse("1-4,7", dialect=ir.PAGES) == [1, 2, 3, 4, 7]
    assert ir.parse("0-10:3", dialect=ir.CPULIST) == [0, 3, 6, 9]
    assert ir.parse("0-15:4", dialect=ir.SLURM) == [0, 4, 8, 12]
    assert ir.parse("-2", dialect=ir.HTTP, upper=9) == [8, 9]
    assert set(ir.DIALECTS) == {"default", "pages", "cpulist", "slurm", "http"}


def _limits() -> None:
    assert ir.DEFAULT_MAX_SIZE == 10_000_000
    assert ir.DEFAULT_MAX_SPANS == 1_000_000


def _errors() -> None:
    for name in (
        "RangeSyntaxError",
        "DescendingRangeError",
        "RangeOverlapError",
        "RangeOrderError",
        "RangeBoundsError",
        "RangeSizeError",
    ):
        kind = getattr(ir, name)
        assert issubclass(kind, ir.RangeError) and issubclass(kind, ValueError)
    err = ir.RangeError("bad", text="1,x", token="x", offset=2)
    assert (err.text, err.token, err.offset) == ("1,x", "x", 2)
    assert err.pointer() == "1,x\n  ^"


CONTRACTS: dict[str, Callable[[], None]] = {
    "parse": _parse,
    "compact": _compact,
    "parse_ranges": _parse_ranges,
    "count": _count,
    "normalize": _normalize,
    "IntRanges": _int_ranges,
    "Dialect": _dialect,
    "DIALECTS": _presets,
    "DEFAULT_MAX_SIZE": _limits,
    "DEFAULT_MAX_SPANS": _limits,
    **{name: _presets for name in ("DEFAULT", "PAGES", "CPULIST", "SLURM", "HTTP")},
    **{
        name: _errors
        for name in (
            "RangeError",
            "RangeSyntaxError",
            "DescendingRangeError",
            "RangeOverlapError",
            "RangeOrderError",
            "RangeBoundsError",
            "RangeSizeError",
        )
    },
}


def test_all_lists_exactly_the_contracted_names() -> None:
    assert sorted(ir.__all__) == sorted(CONTRACTS)


@pytest.mark.parametrize("name", sorted(CONTRACTS))
def test_contract(name: str) -> None:
    assert hasattr(ir, name)
    CONTRACTS[name]()


def test_public_callables_and_classes_are_documented() -> None:
    for name in ir.__all__:
        obj = getattr(ir, name)
        if callable(obj):
            assert obj.__doc__ and len(obj.__doc__) > 40, name


@pytest.mark.parametrize(
    "module", ["_compact", "_intranges", "_parse", "_errors", "_dialect", "_spans", "_tokens"]
)
def test_docstring_examples_run(module: str) -> None:
    mod = importlib.import_module(f"intranges.{module}")
    result = doctest.testmod(mod, extraglobs=vars(ir), optionflags=doctest.ELLIPSIS)
    assert result.failed == 0
    if module in ("_compact", "_intranges", "_parse"):
        assert result.attempted > 0


def test_version_is_a_three_part_string() -> None:
    parts = ir.__version__.split(".")
    assert len(parts) == 3 and all(part.isdigit() for part in parts)
    assert ir.__version__ == "0.2.0"


def test_the_package_ships_type_information() -> None:
    assert importlib.resources.files("intranges").joinpath("py.typed").is_file()
