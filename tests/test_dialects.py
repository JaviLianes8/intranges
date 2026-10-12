"""Examples taken from the documents each dialect cites."""

import pytest

from intranges import (
    CPULIST,
    DEFAULT,
    DIALECTS,
    HTTP,
    PAGES,
    SLURM,
    Dialect,
    RangeBoundsError,
    RangeSyntaxError,
    compact,
    parse,
    parse_ranges,
)


def test_kernel_cpu_list_basic_forms() -> None:
    assert parse("0-3,8-11", dialect=CPULIST) == [0, 1, 2, 3, 8, 9, 10, 11]
    assert parse("1,2,10-20", dialect=CPULIST) == [1, 2, *range(10, 21)]


def test_kernel_used_group_example() -> None:
    values = parse("100-2000:2/25", dialect=CPULIST)
    assert values[:6] == [100, 101, 125, 126, 150, 151]
    assert all((v - 100) % 25 in (0, 1) for v in values)
    assert values[-1] == 2000


def test_kernel_last_cpu_and_all_aliases() -> None:
    assert parse("16-N", dialect=CPULIST, upper=31) == list(range(16, 32))
    assert parse("all", dialect=CPULIST, upper=31) == parse("0-N", dialect=CPULIST, upper=31)
    assert parse("ALL", dialect=CPULIST, upper=3) == [0, 1, 2, 3]
    with pytest.raises(RangeBoundsError):
        parse("16-N", dialect=CPULIST)


def test_taskset_stride_examples() -> None:
    assert parse("0-10:3", dialect=CPULIST) == [0, 3, 6, 9]
    assert parse("0-10:2", dialect=CPULIST) == [0, 2, 4, 6, 8, 10]


def test_kernel_rejects_used_greater_than_group() -> None:
    with pytest.raises(RangeSyntaxError):
        parse("0-10:3/2", dialect=CPULIST)
    with pytest.raises(RangeSyntaxError):
        parse("0-10:0", dialect=CPULIST)


def test_cpulist_rejects_negative_values() -> None:
    with pytest.raises(RangeSyntaxError):
        parse("-1", dialect=CPULIST)


def test_slurm_array_examples() -> None:
    assert parse("0-15:4", dialect=SLURM) == [0, 4, 8, 12]
    assert parse("0,6,16-32", dialect=SLURM) == [0, 6, *range(16, 33)]
    with pytest.raises(RangeSyntaxError):
        parse("0-15%4", dialect=SLURM)
    with pytest.raises(RangeSyntaxError):
        parse("0-15:2/4", dialect=SLURM)


def test_slurm_hostlist_brackets_and_padding() -> None:
    assert parse("[1-3,5]", dialect=SLURM) == [1, 2, 3, 5]
    assert parse("[001-003]", dialect=SLURM) == [1, 2, 3]
    assert compact(range(1, 11), dialect=SLURM, width=3) == "001-010"


def test_cups_page_ranges() -> None:
    assert parse("1-4,7,9-12", dialect=PAGES) == [1, 2, 3, 4, 7, 9, 10, 11, 12]
    with pytest.raises(RangeBoundsError):
        parse("0-3", dialect=PAGES)
    with pytest.raises(RangeSyntaxError):
        parse("5-", dialect=PAGES, upper=9)


def test_http_byte_ranges() -> None:
    length = 10000
    upper = length - 1
    assert parse_ranges("bytes=0-499", dialect=HTTP, upper=upper).spans == ((0, 499),)
    assert parse_ranges("bytes=500-999", dialect=HTTP, upper=upper).spans == ((500, 999),)
    assert parse_ranges("bytes=-500", dialect=HTTP, upper=upper).spans == ((9500, 9999),)
    assert parse_ranges("bytes=9500-", dialect=HTTP, upper=upper).spans == ((9500, 9999),)
    assert parse_ranges("0-0,-1", dialect=HTTP, upper=upper).spans == ((0, 0), (9999, 9999))


def test_http_clamps_and_rejects_unsatisfiable() -> None:
    assert parse_ranges("0-20000", dialect=HTTP, upper=99).spans == ((0, 99),)
    assert parse_ranges("-500", dialect=HTTP, upper=99).spans == ((0, 99),)
    with pytest.raises(RangeBoundsError):
        parse_ranges("200-300", dialect=HTTP, upper=99)
    with pytest.raises(RangeSyntaxError):
        parse_ranges("-0", dialect=HTTP, upper=99)
    with pytest.raises(RangeSyntaxError):
        parse_ranges("-5", dialect=HTTP)


def test_http_format_writes_the_unit() -> None:
    assert compact([0, 1, 2, 9], dialect=HTTP) == "bytes=0-2,9"
    assert compact([], dialect=HTTP) == ""


def test_format_refuses_values_the_dialect_cannot_hold() -> None:
    with pytest.raises(RangeBoundsError):
        compact([-1], dialect=CPULIST)
    with pytest.raises(RangeBoundsError):
        compact([0], dialect=PAGES)
    with pytest.raises(ValueError):
        compact([1], width=0)


def test_dialect_registry() -> None:
    assert DIALECTS == {
        "default": DEFAULT,
        "pages": PAGES,
        "cpulist": CPULIST,
        "slurm": SLURM,
        "http": HTTP,
    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"range_sep": ""},
        {"list_sep": ""},
        {"range_sep": ",", "list_sep": ","},
        {"range_sep": "1"},
        {"stride": ""},
        {"groups": True},
        {"suffix": True},
        {"last_alias": "N1"},
    ],
)
def test_dialect_rejects_incoherent_settings(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        Dialect(**kwargs)  # type: ignore[arg-type]


def test_custom_dialect() -> None:
    dots = Dialect(name="dots", range_sep="..", list_sep=";", stride="by")
    assert parse("1..9by4;20", dialect=dots) == [1, 5, 9, 20]
    assert compact([1, 2, 3, 20], dialect=dots) == "1..3;20"
    assert DEFAULT.with_separators(":", None) == Dialect(range_sep=":")
