import pytest

from intranges import (
    DescendingRangeError,
    RangeBoundsError,
    RangeError,
    RangeOrderError,
    RangeOverlapError,
    RangeSizeError,
    RangeSyntaxError,
    count,
    parse,
    parse_ranges,
)


def test_error_points_at_the_bad_token() -> None:
    with pytest.raises(RangeSyntaxError) as info:
        parse("1-3, 5, x-9")
    err = info.value
    assert (err.text, err.token, err.offset) == ("1-3, 5, x-9", "x-9", 8)
    assert "offset 8" in str(err)
    assert err.pointer() == "1-3, 5, x-9\n        ^^^"


def test_offsets_skip_prefix_and_brackets() -> None:
    from intranges import HTTP, SLURM

    with pytest.raises(RangeSyntaxError) as info:
        parse("bytes=0-1,z", dialect=HTTP, upper=9)
    assert info.value.offset == 10
    with pytest.raises(RangeSyntaxError) as info:
        parse(" [1,q]", dialect=SLURM)
    assert info.value.offset == 4


def test_errors_without_location_have_no_pointer() -> None:
    err = RangeError("plain")
    assert str(err) == "plain"
    assert err.pointer() == ""
    assert (err.text, err.token, err.offset) == (None, None, None)


@pytest.mark.parametrize(
    "kind",
    [
        RangeSyntaxError,
        DescendingRangeError,
        RangeOverlapError,
        RangeOrderError,
        RangeBoundsError,
        RangeSizeError,
    ],
)
def test_every_error_is_a_range_error_and_value_error(kind: type[RangeError]) -> None:
    assert issubclass(kind, RangeError)
    assert issubclass(kind, ValueError)


def test_specific_errors_are_raised() -> None:
    with pytest.raises(DescendingRangeError):
        parse("5-1")
    with pytest.raises(RangeSyntaxError, match="empty"):
        parse("1,,2")
    with pytest.raises(RangeSyntaxError, match="stride"):
        parse("5:2", dialect=__import__("intranges").SLURM)
    with pytest.raises(RangeBoundsError, match="upper bound"):
        parse("5-")
    with pytest.raises(RangeBoundsError):
        parse("1-10", lower=2)
    with pytest.raises(RangeBoundsError):
        parse("1-10", upper=9)
    with pytest.raises(ValueError, match="greater"):
        parse("1", lower=5, upper=1)


def test_negative_number_rule() -> None:
    assert parse("-3--1") == [-3, -2, -1]
    assert parse("-2-2") == [-2, -1, 0, 1, 2]
    assert parse("-5") == [-5]
    with pytest.raises(DescendingRangeError):
        parse("1--3")
    with pytest.raises(RangeSyntaxError):
        parse("--3")
    with pytest.raises(RangeSyntaxError):
        parse("+3")


def test_open_end_needs_and_uses_upper() -> None:
    assert parse("5-", upper=7) == [5, 6, 7]
    assert parse("-2-", upper=0) == [-2, -1, 0]


def test_overlap_policy() -> None:
    assert parse_ranges("1-5,3,4-8").spans == ((1, 8),)
    with pytest.raises(RangeOverlapError) as info:
        parse_ranges("1-5,9,3", on_overlap="reject")
    assert info.value.token == "3"
    with pytest.raises(RangeOverlapError) as info:
        parse_ranges("3,1-5", on_overlap="reject")
    assert info.value.token == "1-5"
    with pytest.raises(RangeOverlapError):
        parse_ranges("2,2", on_overlap="reject")
    assert parse_ranges("1-2,3-4", on_overlap="reject").spans == ((1, 4),)


def test_order_policy() -> None:
    assert parse_ranges("9,1").spans == ((1, 1), (9, 9))
    with pytest.raises(RangeOrderError) as info:
        parse_ranges("1,9,4", on_unsorted="reject")
    assert info.value.token == "4"
    assert parse_ranges("1,4,9", on_unsorted="reject").count == 3


def test_policy_values_are_validated() -> None:
    with pytest.raises(ValueError):
        parse_ranges("1", on_overlap="keep")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        parse_ranges("1", on_unsorted="sort")  # type: ignore[arg-type]


def test_parse_size_guard_checks_before_allocating() -> None:
    with pytest.raises(RangeSizeError) as info:
        parse("1-3,0-10000000000")
    assert info.value.token == "0-10000000000"
    with pytest.raises(RangeSizeError):
        parse("1-11", max_size=10)
    assert len(parse("1-10", max_size=10)) == 10
    assert parse("1-11", max_size=None) == list(range(1, 12))


def test_span_guard_for_strides() -> None:
    from intranges import SLURM

    with pytest.raises(RangeSizeError):
        parse_ranges("0-100000000:2", dialect=SLURM)
    assert parse_ranges("0-100:2", dialect=SLURM, max_spans=51).count == 51
    with pytest.raises(RangeSizeError):
        parse_ranges("0-100:2", dialect=SLURM, max_spans=50)


def test_count_never_expands() -> None:
    assert count("0-10000000000") == 10_000_000_001
    assert count("1-5,3-9") == 9
    assert count("") == 0


def test_unsatisfiable_derived_ranges_are_bounds_errors() -> None:
    from intranges import CPULIST, HTTP, Dialect

    with pytest.raises(RangeBoundsError):
        parse_ranges("bytes=10000-", dialect=HTTP, upper=9999)
    with pytest.raises(RangeBoundsError):
        parse("15-", upper=10)
    with pytest.raises(RangeBoundsError):
        parse_ranges("-5", dialect=HTTP, upper=-1)
    with pytest.raises(RangeBoundsError):
        parse("all", dialect=CPULIST, upper=-1)
    with pytest.raises(RangeBoundsError):
        parse_ranges("-5", dialect=HTTP, lower=97, upper=99)
    with pytest.raises(RangeSyntaxError):
        parse_ranges("-", dialect=HTTP, upper=9)
    odd = Dialect(negatives=False, suffix=True, last_alias="N")
    with pytest.raises(RangeSyntaxError):
        parse("-N", dialect=odd, upper=10)
