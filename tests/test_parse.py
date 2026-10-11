import pytest

from intranges import RangeError, parse


def test_parse_single_value() -> None:
    assert parse("8") == [8]


def test_parse_a_range() -> None:
    assert parse("1-5") == [1, 2, 3, 4, 5]


def test_parse_mixed_singles_and_ranges() -> None:
    assert parse("1-5,8,10-12") == [1, 2, 3, 4, 5, 8, 10, 11, 12]


def test_parse_negative_single() -> None:
    assert parse("-5") == [-5]


def test_parse_negative_range() -> None:
    assert parse("-3--1") == [-3, -2, -1]


def test_parse_range_crossing_zero() -> None:
    assert parse("-2-2") == [-2, -1, 0, 1, 2]


def test_parse_tolerates_whitespace() -> None:
    assert parse(" 1 - 3 , 7 ") == [1, 2, 3, 7]


def test_parse_single_point_range() -> None:
    assert parse("4-4") == [4]


def test_parse_empty_string_is_empty_list() -> None:
    assert parse("") == []
    assert parse("   ") == []


def test_parse_custom_separators() -> None:
    assert parse("1..3;6", range_sep="..", list_sep=";") == [1, 2, 3, 6]


def test_parse_rejects_descending_range() -> None:
    with pytest.raises(RangeError):
        parse("5-1")


def test_parse_rejects_garbage() -> None:
    with pytest.raises(RangeError):
        parse("1-x")


def test_parse_rejects_empty_token() -> None:
    with pytest.raises(RangeError):
        parse("1,,2")


def test_parse_rejects_empty_separator() -> None:
    with pytest.raises(ValueError):
        parse("1-2", range_sep="")
